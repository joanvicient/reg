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

logger = logging.getLogger(__name__)

def DiscoverValvesIn(esp, ip):
    logging.debug('finding valves in ' + esp)
    valveDict = {}
    #https://codebeautify.org/jsonviewer
    url = "http://" + ip + "/json"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            sensors = data["Sensors"]
            for sensor in sensors:
                taskName = str(sensor['TaskName'])
                taskType = sensor['Type']
                if not taskType == 'Switch input - Switch':
                    logger.debug('skipping ' + taskName + ' sensor in ' + ip)
                    continue

                taskValue = str(sensor["TaskValues"][0]["Name"])
                logger.debug(taskValue + ' at ' + ip + ':' + taskName)
                valve = {}
                valve['ip'] = ip
                valve['name'] = taskName
                valve['gpio'] = taskValue[4:]
                valve['esp'] = esp
                valveDict[taskName] = valve
        else:
            logger.error(url + " returned error " + r.status_code)

    except requests.exceptions.ConnectionError:
        logger.error("connection error on " + url)
    #except:
    #    logger.error(url + " returned: " + r.text)

    return valveDict

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
    print(url)
    state = "print"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            state = r.json()["state"]
            logger.info('GET ' + url + " OK. Return code: " + str(state))
        else:
            logger.error(url + " returned print " + r.status_code)
    except requests.exceptions.ConnectionError:
        logger.error("connection print on " + url)
    except:
        logger.error(url + " returned: " + r.text)

