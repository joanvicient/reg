#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions

#from valve import Valve
from mqttclient import MqttClient
import socket
import logging
import sys
import argparse
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import time

reg_valve_ip = None
reg_valve_port = None

logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)

### MQTT client ######################################################################
def on_mqtt_callback(topic, payload):
    if (topic == 'reg/reg_valves/info'):
        logging.debug('MQTT: ' + topic + ", with body: " + payload)
        a = json.loads(payload)
        global reg_valve_ip
        global reg_valve_port
        reg_valve_ip = str(a['ip'])
        reg_valve_port = str(a['port'])
    else:
        logging.error('uncached topic: ' + topic + ' - ' + payload)

def GenerateServerInfoDict(rest_port):
    serverInfoDict = {}

    hostname=socket.gethostname()
    IPAddr=socket.gethostbyname(hostname)

    serverInfoDict['hostname'] = hostname
    serverInfoDict['ip'] = IPAddr
    serverInfoDict['port'] = rest_port

    return serverInfoDict

### GET REST ########################################################################################################
# rest GET <url>
# returns <ok>, <dictioary>
# <ok> is true if communications was ok and a json was recieved from REST server
def get_rest(url):
    valves = {}
    try:
        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            logging.error('GET ' + url + ' error: ' + r.status_code)
            return False, valves
        else:
            valves = r.json()
            return True, valves
    except Exception as e:
        logging.error("exception on GET " + url + ": " + e.__class__.__name__)
        return False, valves

###
#
def disable_valve_in_url(url):
    body = { "value": "0" }
    try:
        r = requests.patch(url, json = body)
        logging.debug(r.json)
        return r.status_code == requests.codes.ok
    except Exception as e:
        logging.error("exception on PATCH " + url + ": " + e.__class__.__name__)
        return False

def check_valve_in_url(url):
    logging.debug('Checking ' + url)
    ok, ret = get_rest(url)
    if ok == False:
        logging.error("Communication error with " + url)
        return
    
    if not 'value' in ret:
        logging.error("Message recieved from " + url + " is invalid: " + str(ret))
        return
    
    #print(ret)
    if ret['value'] == '0':
        logging.info("Valve " + url + " is not active")
        return
    else:
        logging.debug("Valve " + url + " is active")
    
    #if open, wait an check again
    seconds = 100
    #seconds = 2
    time.sleep(seconds)
    ok, ret = get_rest(url)
    if ret['value'] == '1':
        logging.debug(url + ' is still active!')
        ret = disable_valve_in_url(url)
        if ret:
            logging.info(url + ' has been deactivated')
        else:
            logging.error(url + ' could not have been deactivated')
    else:
        logging.debug(url + 'has been deactivated')

### scheduler #######################################################################################################
def scheduled_job():
    valves = {}
    if (reg_valve_ip == None) or (reg_valve_port == None):
        logging.error('reg_valve addr/port not known')
    else:
        logging.info('starting watchdog: GET all valve names')
        url = 'http://' + reg_valve_ip + ':' + reg_valve_port + '/valves/'
        ok, valve_dict = get_rest(url)
        if ok == False:
            logging.error('Error getting valves')
            return
        else:
            #logging.debug(valve_dict)
            pass

        # get status of each valve
        for valve in valve_dict:
            valve_url = url + valve
            check_valve_in_url(valve_url)

### main ##############################################################################################################
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Every hour checks all valve status and sets to 0 if they are enabled for more than one minute.')
    parser.add_argument("-l", "--log-level", type=str.upper, help='INFO or DEBUG', default="INFO", dest="log_level")
    args = parser.parse_args()

    #init logging
    if args.log_level == 'DEBUG':
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    logging.info('Log level: ' + args.log_level)

    #init mqtt client
    mqtt = MqttClient("reg_watchdog", ['reg/reg_valves/info'], on_mqtt_callback)
    serverInfoDict = GenerateServerInfoDict("0")
    mqtt.publish("reg/reg_watchdog/info", serverInfoDict, retain = True)

    logging.info("Init successful")

    # init scheduler
    sched = BlockingScheduler()
    sched.add_job(scheduled_job, 'cron', minute='15,45')
    #sched.add_job(scheduled_job, 'cron', second='0,30')
    sched.start()

    # never gets that far, only for developing purposes
    time.sleep(1)
    scheduled_job()
