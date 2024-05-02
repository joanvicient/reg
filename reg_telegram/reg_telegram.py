#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that starts a telegram bot
# insteacts with scheduler and valves via mqtt and rest
import sys
import argparse
import socket
import logging
import os
from mqttclient import MqttClient
import requests
from telegramBot import RegTelegramBot
import json
import time

token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
admin_id = os.getenv("TELEGRAM_ADMIN_ID")
regTelegramBot = None
reg = {}

def on_mqtt_callback(topic, payload):
    logging.debug(topic + ' - ' + payload)
    if str(topic).startswith('reg/'):
        if str(topic).endswith('/info'):
            service = topic[4:-5]
            a = json.loads(payload)
            reg[service] = a
            if regTelegramBot:
                regTelegramBot.setValvesServer(reg)
        else:
            logging.debug("mqtt message not used")
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={topic[9:] + ': ' + payload}"
        logging.debug(requests.get(url).json()) # this sends the message

def GenerateServerInfoDict(rest_port):
    serverInfoDict = {}

    hostname=socket.gethostname()
    IPAddr=socket.gethostbyname(hostname)

    serverInfoDict['hostname'] = hostname
    serverInfoDict['ip'] = IPAddr
    serverInfoDict['port'] = rest_port

    return serverInfoDict

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Telegram bot!')
    parser.add_argument("-l", "--log-level", type=str.upper, help='INFO or DEBUG', default="INFO", dest="log_level")
    args = parser.parse_args()

    #init logging
    if args.log_level == 'DEBUG':
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    logging.info('Log level: ' + args.log_level)
    logging.debug('TELEGRAM - Token: ' + token + '. Admin: ' + admin_id + '. Chat: ' + chat_id)

    #init mqtt client
    mqtt = MqttClient("reg_telegram", ['telegram/#', 'reg/#'], on_mqtt_callback)
    serverInfoDict = GenerateServerInfoDict("0")
    mqtt.publish("reg/reg_telegram/info", serverInfoDict, retain = True)

    time.sleep(1)
    logging.info("Init successful")
    regTelegramBot = RegTelegramBot(token, chat_id, admin_id, reg)