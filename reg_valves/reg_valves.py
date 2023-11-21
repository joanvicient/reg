#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions


from wemos import DiscoverValves, DiscoverWemos
#from valve import Valve
from mqttclient import MqttClient
from restclient import RestClient
import time
import logging
import sys

def Discover():
    valveList = []

    logging.debug("### Finding Wemos ###")
    wemosList = DiscoverWemos()
    logging.debug(wemosList)

    logging.debug("### Finding Valves ###")
    valveDict = DiscoverValves(wemosList)
    for valve in valveList:
        logging.debug(valve)

    return valveDict


if __name__ == "__main__":

    #init logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    #init mqtt client
    mqtt = MqttClient("reg_valves", [], None)

    #initialize valves
    discoveredValvesDict = Discover()
    rest = RestClient()
    storedValvesDict = rest.getValves()

    logging.debug('discovered:')
    logging.debug(discoveredValvesDict)
    logging.debug ('stored:')
    logging.debug(storedValvesDict)

    rest.postValves(discoveredValvesDict)
    #subscribe mqtt endpoints

    storedValvesDict = rest.getValves()
    logging.debug(storedValvesDict)

    for valve in storedValvesDict:
        logging.info('Detected: ' + str(valve))

    logging.info("Init successful")
