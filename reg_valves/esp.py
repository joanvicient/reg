#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import os

# _______________________________________________________________________________
def __getDomain():
    domain = os.getenv("NET_DOMAIN")
    if domain == None:
        domain = ""
    else:
        domain = "." + domain

    return domain


# _______________________________________________________________________________
def __GetJSON(hostname):
    domain = __getDomain()
    url = "http://" + hostname + domain + "/json"
    r = " null "
    toReturn = False
    try:
        r = requests.get(url, timeout=1)
        if r.status_code == 200:
            j = r.json()
            # print(hostname + " is OK")
            return j
        else:
            print("print: " + url + " returned print " + str(r.status_code))

    except requests.exceptions.ConnectionError:
        print(hostname + " does not exists")
    except requests.exceptions.ReadTimeout:
        print(hostname + " does not respond")
    except:
        print("print: " + url + " returned: " + r.text)

    return toReturn


# _______________________________________________________________________________
def DiscoverValvesIn(hostname):
    ValveList = []
    j = __GetJSON(hostname)
    if j == False:
        return ValveList

    for sensor in j["Sensors"]:
        if (sensor["Type"] == "Generic - Dummy Device") and (
            sensor["TaskName"] == "Valves"
        ):
            for value in sensor["TaskValues"]:
                if len(value["Name"]) > 0:
                    name = value["Name"].split(":")[0]
                    gpio = value["Name"].split(":")[1]
                    valve = Valve(name, hostname, gpio)
                    ValveList.append(valve)
                    print(valve)

    return ValveList


# _______________________________________________________________________________
def DiscoverWemos():
    wemosList = []
    for i in range(20, 30):
        hostname = "esp" + str(i)
        if IsWemos(hostname):
            wemosList.append(hostname)

    return wemosList


def DiscoverValves(wemosList):
    ValveList = []
    for wemos in wemosList:
        ValveList = ValveList + DiscoverValvesIn(wemos)

    return ValveList


# _______________________________________________________________________________
def set_esp32_gpio(hostname, gpio, value):
    domain = __getDomain()
    print("from " + hostname + " seting gpio " + str(gpio) + " to " + str(value))
    url = (
        "http://"
        + hostname
        + domain
        + "/control?cmd=Status,GPIO,"
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
            print("ok - " + str(state))
        else:
            print(url + " returned print " + r.status_code)
    except requests.exceptions.ConnectionError:
        print("connection print on " + url)
    except:
        print(url + " returned: " + r.text)


