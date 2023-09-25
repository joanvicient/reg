#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions


from wemos import DiscoverValves, DiscoverWemos
from valve import Valve
from mqttclient import MqttClient

class RegValves:

    def Discover(self):
        self.valveList = []

        print("")
        print("### Finding Wemos ###")
        self.wemosList = DiscoverWemos()
        print(self.wemosList)

        print("")
        print("### Finding Valves ###")
        self.valveList = DiscoverValves(self.wemosList)
        for valve in self.valveList:
            print(valve)

    def __init__(self):
        self.Discover()

if __name__ == "__main__":
    #regValves = RegValves()
    mqtt = MqttClient("reg_valves")
