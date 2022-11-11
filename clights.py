# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 21:00:02 2021

@author: Ernst
"""
import os
import requests
import json
from threading import Timer
import RPi.GPIO as GPIO
import time
import logging


# User configuration
pinLights = 24
LIGHTS_ON_TIME = 5  # Time that the lights turn on for each tweet in seconds.


bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[logging.FileHandler('output.log', mode='w'),
                              stream_handler])


global ledDC, OnOff
ledDC = 0  # Initiate DutyCycle
OnOff = 'Off'

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Configure pins as output
GPIO.setup(pinLights, GPIO.OUT, initial=1)
lights = GPIO.PWM(pinLights, 100)  # 100 Hz
lights.start(0)


def LightsOn():
    global ledDC, OnOff
    OnOff = 'On'
    if ledDC < 100:
        for i in range(ledDC + 1, 101):
            lights.ChangeDutyCycle(i)
            ledDC = i
            time.sleep(0.05)

    
def LightsOff():
    global ledDC, OnOff
    OnOff = 'Off'
    for i in range(ledDC, -1, -1):
        if OnOff == 'Off':
            lights.ChangeDutyCycle(i)
            ledDC = i
            time.sleep(0.05)


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    logging.info(json.dumps(response.json()))
    return response.json()


def delete_all_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    rules = response.json()
    if rules is None or "data" not in rules:
        logging.info("No rules present.")
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    logging.info(json.dumps(response.json()))


def set_rules(rules):
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    logging.info(json.dumps(response.json()))


def get_stream():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream?expansions=author_id", auth=bearer_oauth, stream=True,
    )
    logging.info(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    
    t = Timer(1.0, LightsOff)  # Initiate timer object
    for response_line in response.iter_lines():
            if response_line:
                json_response = json.loads(response_line)
                try:
                    data = json_response['data']
                    text = data['text']
                except KeyError:
                    continue
                
                users = json_response['includes']['users'][0]
                name = users['name']
                username = users['username']
                
                logging.info('    - {} (@{}): {}\n'.format(name, username, text))
                
                LightsOn()
                    
                t.cancel()  # reset timer every time a tweet is found
                t = Timer(LIGHTS_ON_TIME, LightsOff)
                t.start()


def main():    
    status = False
    while not status:
        try:
            get_rules()
            delete_all_rules()
             
            rules = [
                 {"value": "(christmas OR holidays) -is:retweet -is:reply -is:quote", "tag": "Christmas"},
                 ]
            set_rules(rules)
            status = True

        except:
            logging.info('Unable to reach rules, trying again in 10 sec')
            time.sleep(10)
        
        get_stream()


if __name__ == '__main__':
    try:
        main()
        
    except KeyboardInterrupt:
        lights.stop()
        GPIO.cleanup()
