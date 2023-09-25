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
    valveList = []
    url = "http://" + hostname + "/json"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            sensors = data["Sensors"]
            for sensor in sensors:
                taskValues = sensor["TaskValues"]
                #print (taskValues)
                for taskValue in taskValues:
                    taskValueName = taskValue["Name"]
                    #print (taskValueName)
                    name, gio = taskValueName.split(':')
                    print (name)
                    #print (gio)
                    valve = Valve(name, hostname, gio)
                    valveList.append(valve)

        else:
            print(url + " returned print " + r.status_code)
    except requests.exceptions.ConnectionError:
        print("connection print on " + url)
    except:
        print(url + " returned: " + r.text)
            

    return valveList

def DiscoverValves(wemosList):
    ValveList = []
    for wemos in wemosList:
        ValveList = ValveList + DiscoverValvesIn(wemos)

    return ValveList
