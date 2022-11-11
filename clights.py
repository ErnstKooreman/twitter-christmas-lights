# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 21:00:02 2021

@author: Ernst
"""
import requests
import json
from threading import Timer
import RPi.GPIO as GPIO
import time
import logging

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[logging.FileHandler('output.log', mode='w'),
                              stream_handler])


global ledDC, OnOff
ledDC = 0
OnOff = 'Off'

# Configure GPIO pins
pinLeds = 24

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Configure pins as output
GPIO.setup(pinLeds, GPIO.OUT, initial=1)
ledstrip = GPIO.PWM(pinLeds, 100)  # 100 Hz
ledstrip.start(0)


def LightsOn():
    global ledDC, OnOff
    OnOff = 'On'
    if ledDC < 100:
        for i in range(ledDC + 1, 101):
            ledstrip.ChangeDutyCycle(i)
            ledDC = i
            time.sleep(0.05)

    
def LightsOff():
    global ledDC, OnOff
    OnOff = 'Off'
    for i in range(ledDC, -1, -1):
        if OnOff == 'Off':
            ledstrip.ChangeDutyCycle(i)
            ledDC = i
            time.sleep(0.05)


bearer_token = "AAAAAAAAAAAAAAAAAAAAAPoAWAEAAAAAIqEYGv80qMNnaOnfnNjog2N5gco%3DHV40eVUR1usB0CbbxqnrWzt9jOwREiM43bWstZIwYB2nCG71Qw"


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
    
    t = Timer(1.0, LightsOff)
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
                    
                t.cancel()
                t = Timer(5.0, LightsOff)
                t.start()


def main():    
    status = False
    while not status:
        try:
            get_rules()
            delete_all_rules()
             
            rules = [
                 {"value": "(kerst OR kerstmis OR kerstfeest OR kerstvakantie) -is:retweet -is:reply -is:quote", "tag": "Kerst"},
#                {"value": '(sinterklaas OR "sint nicolaas") -is:retweet -is:reply -is:quote', "tag": "Sinterklaas"},
		 {"value": "(oud en nieuw) -is:retweet -is:reply -is:quote", "tag": "OenN"}
                 ]
            set_rules(rules)
            get_stream()
            status = True

        except:
            logging.info('Unable to reach rules, trying again in 10 sec')
            time.sleep(10)


if __name__ == '__main__':
    try:
        main()
        
    except KeyboardInterrupt:
        ledstrip.stop()
        GPIO.cleanup()
