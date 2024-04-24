#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Class to interact with wemos

# Requirements:
# python -m pip install --upgrade pip
# pip install requests

import requests
import json
import logging
import argparse

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)


def DiscoverValvesIn(esp, ip):
    logging.debug('finding valves in ' + esp)
    valveDict = {}
    #https://codebeautify.org/jsonviewer
    url = "http://" + ip + "/json"
    try:
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            data = r.json()
            sensors = data["Sensors"]
            for sensor in sensors:
                taskName = str(sensor['TaskName'])
                taskType = sensor['Type']
                if not taskType == 'Switch input - Switch':
                    logger.debug('skipping "' + taskName + '" sensor in ' + ip)
                    continue

                gpio = str(sensor["TaskValues"][0]["Name"])
                value = str(sensor["TaskValues"][0]["Value"])

                if gpio.isdigit():
                    logger.debug(taskName + ' at ' + ip + ', gpio ' + gpio + ': ' + value)
                    valve = {}
                    valve['ip'] = ip
                    valve['name'] = taskName
                    valve['gpio'] = gpio
                    valve['esp'] = esp
                    valve['value'] = value
                    valveDict[taskName] = valve
                else:
                    logger.info('Missconfigured ' + taskName + ' at ' + ip)
        else:
           logger.error('exception on GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ")")

    except Exception as e:
        logger.error("exception on GET " + url + ": " + e.__class__.__name__)

    return valveDict

def UpdateValve(valve, ip):
    logging.debug('updating valve ' + str(valve))
    #https://codebeautify.org/jsonviewer
    url = "http://" + ip + "/json"
    value = None
    try:
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            data = r.json()
            sensors = data["Sensors"]
            for sensor in sensors:
                taskName = str(sensor['TaskName'])
                if taskName == valve:
                    value = str(sensor["TaskValues"][0]["Value"])
                    break
        else:
           logger.error('exception on GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ")")

    except Exception as e:
        logger.error("exception on GET " + url + ": " + e.__class__.__name__)

    return value

def SetWemosGpio(ip, gpio, value):
    logger.debug("In " + ip + " seting gpio " + str(gpio) + " to " + str(value))
    url = (
        "http://"
        + ip
        + "/control?cmd=GPIO,"
        + str(gpio)
        + ","
        + str(value)
    )
    try:
        r = requests.get(url, timeout=0.5)
        if r.status_code == requests.codes.ok:
            state = r.json()["state"]
            logger.debug('GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ") - Valve state = " + str(state))
        else:
            logger.error('GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ")")

        return r.reason, r.status_code

    except Exception as e:
        logger.error("exception on GET " + url + ": " + e.__class__.__name__)

    return "Error", 500

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Library to interact with Wemos and its valves. Can be used alone to discover valves')
    parser.add_argument('-i', '--ip', type=str, help='ip', dest="ip", required=True)
    args = parser.parse_args()

    DiscoverValvesIn("esp", args.ip)
