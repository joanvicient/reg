#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Class to interact with wemos

# Requirements:
# python -m pip install --upgrade pip
# pip install nmap
# pip install requests
# pip install json

import nmap
import requests
import json
from valve import Valve
import logging

import logging
logger = logging.getLogger(__name__)

def DiscoverWemos():
    wemosList = []

    nm = nmap.PortScanner()
    nm.scan('192.168.1.2-254', '22')
    for host in nm.all_hosts():
        hostname = nm[host].hostname()
        if hostname.startswith('esp'):
            wemosList.append(hostname)
        
    return wemosList


def DiscoverValvesIn(hostname):
    valveDict = {}
    url = "http://" + hostname + "/json"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            sensors = data["Sensors"]
            for sensor in sensors:
                taskName = sensor['TaskName']
                if not taskName == 'Valves':
                    logger.debug('skipping' + taskName + ' sensor')
                    continue

                taskValues = sensor["TaskValues"]
                for taskValue in taskValues:
                    taskValueName = taskValue["Name"]
                    if taskValueName == "":
                        logger.debug('skipping empty task')
                        continue
                    elif not ':' in taskValueName:
                        print(': not found in ' + taskValueName)
                        continue
                    name, gio = taskValueName.split(':')
                    logger.debug(name + ' at ' + hostname + ':' + gio)
                    valve = {}
                    valve['hostname'] = hostname
                    valve['gio'] = gio
                    valveDict[name] = valve

        else:
            logger.error(url + " returned print " + r.status_code)
    except requests.exceptions.ConnectionError:
        logger.error("connection print on " + url)
    except:
        logger.error(url + " returned: " + r.text)
            

    return valveDict

def DiscoverValves(wemosDict):
    ValveDict = {}
    for wemos in wemosDict:
        ValveDict.update(DiscoverValvesIn(wemos))

    return ValveDict
