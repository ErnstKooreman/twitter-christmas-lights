# twitter_christmaslights
Connect christmas lights to Twitter

*(disclaimer: I am not a professional electrician and have no background as such. This is just a hobby project, please be careful with electronics)*

## Filter tweets
The current script is set to turn the ligts on for 1 second when an original tweet (no re-tweets, replies or quotes) containing `christmas` or `holidays` is tweeted. The Twitter API v2 "filtered stream" is used for this. To create your own filters, see the following [documentation](https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule).

## Hardware
- Raspberry pi
- MOSFET (I used [this](https://nl.aliexpress.com/item/32328363970.html) one)
- LED Christmas lights
- 10 kΩ pull down resistor

### Wiring diagram
<img src=https://user-images.githubusercontent.com/105346709/201608458-3d2f7a85-f807-47a7-acec-53aba00d8855.png width="350">

## Installation
### Authentication token
To get a bearer token, go to the twitter [developer platform](https://developer.twitter.com), create an account and generate a bearer token. With a free account, you can get 500K tweets/month/project. On your RaspberryPi, create a file called `environment` in the `/etc` folder and put your token in there:
```
TWITTER_BEARER_TOKEN=<YOUR_TOKEN_HERE>
```  
Save the file, log out and log back in to load it. You can check if it is there using the `env` command in the terminal.

### Running at startup
To have the `clights.py` script run at startup of your RaspberryPi, add the `clights.service` to the `/etc/systemd/system` folder and edit `WorkingDirectory` and `ExecStart` to point to the directory containing the clights.py file, and the file itself, respectively. This service runs after the RaspberryPi is connected to the internet.

Save the file and reload the daemon:
```
sudo systemctl daemon-reload
```

Start the service:
```
sudo service clights start
```

Check if the service is running by either using 
```
journalctl -f -u clights.service
``` 
or checking the `output.log` file in the `clights.py` folder.
If everything looks fine, enable the service to tell systemd to start it automatically at boot:
```
sudo systemctl enable startupbrowser.service
```
