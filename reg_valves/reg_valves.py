#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions

#from valve import Valve
from flask import Flask, jsonify, request
from wemos import DiscoverValvesIn
from mqttclient import MqttClient
from restclient import RestClient
import socket
import time
import logging
import sys

valveDict = {}
REST_PORT = 5001
app = Flask(__name__)

@app.get('/valves')
def get_all_valves():
    logging.debug('GET ' + str(valveDict))
    return jsonify(valveDict)

@app.get('/valves/<string:id>')
def get_valves(id):
    logging.debug("GET id: " + id)
    if id in valveDict:
        #print(id + " exists")
        return jsonify(valveDict[id])
    else:
        #print(id + ' do not exists')
        return "Not found", 204

def UpdateRegDockers(topic, payload):
    logging.debug('update reg docker')
    return

def on_reg(topic, payload):
    logging.debug('on_reg')
    return

def UpdateValveDict(vDict):
    for v in vDict:
        if v in valveDict:
            if vDict[v] == valveDict[v]:
                logging.debug('Valve already exists: ' + str(v))
            else:
                logging.debug('Valve already exists: ' + str(v) + ' with different values. Updating it')
                del valveDict[v]
                valveDict[v] = vDict[v]
        else:
            logging.debug('Adding valve: ' + str(v))
            valveDict[v] = vDict[v]

def on_esp(topic, payload):
    if (topic[0:7]=='esp/esp'):
        esp = topic[4:]
        if (payload == 'ON'):
            logging.info(esp + ' is ONLINE again')
        elif (payload == 'OFF'):
            for v in valveDict:
                if (valveDict[v]['esp'] == esp):
                    del valveDict[v]

    elif (topic[:8]=='esp/ip4/' and payload != '0'):
        esp = topic[8:]
        ip = '192.168.1.' + payload
        UpdateValveDict(DiscoverValvesIn(esp, ip))
    else:
        logging.debug(topic + ' - ' + payload)

def on_mqtt_callback(topic, payload):
    if (topic[0:4] == 'esp/'):
        on_esp(topic, payload)
    elif (topic[0:4] == 'reg/'):
        on_reg(topic, payload)
    else:
        logging.debug('uncached topic: ' + topic + ' - ' + payload)

def GetServerInfoDict():
    serverInfoDict = {}

    hostname=socket.gethostname()
    IPAddr=socket.gethostbyname(hostname)

    serverInfoDict['hostname'] = hostname
    serverInfoDict['ip'] = IPAddr
    serverInfoDict['port'] = REST_PORT

    return serverInfoDict

if __name__ == "__main__":

    #init logging
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    #initialize valves
    rest = RestClient()
    storedValvesDict = rest.getValves()
    logging.debug ('stored:')
    logging.debug(storedValvesDict)

    #init mqtt client
    mqtt = MqttClient("reg_valves", ['esp/+', 'esp/ip4/+'], on_mqtt_callback)
    serverInfoDict = GetServerInfoDict()
    mqtt.publish("reg/reg_valves/info", serverInfoDict, retain = True)

    logging.info("Init successful")

    app.run(port=REST_PORT)
    #never gets that far
    time.sleep(62)

    print('')
    print('')
    print('DONE:')
    for v in valveDict:
        print('key: ' + v + ' - Value: '+ str(valveDict[v]))
