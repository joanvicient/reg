#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions

#from valve import Valve
from flask import Flask, jsonify, request
from wemos import DiscoverValvesIn, SetWemosGpio
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

# returns the required valve 
# use localhost:5001/valves/espigol?value=1
# to activate or deactivate the valve
@app.get('/valves/<string:id>')
def get_valves(id):
    logging.debug("GET id: " + id)
    if not id in valveDict:
        return "Not found", 204
    else:
        valve = valveDict[id]
        args = request.args
        logging.debug(args)
        if len(args) == 0:
            logging.debug('no args')
            return jsonify(valve)
        elif 'value' in args:
            logging.debug('value in args')
            value = args['value']
            if value=='1' or value=='0':
                SetWemosGpio(valve['ip'], valve['gpio'], value)
                return 'done', 202
            else:
                return 'value param only accepts 0 or 1', 400
        else:
            logging.debug('wrong args')
            return 'bad argument', 400

# PUT localhost:5001/valves/farigola
# with body:
#{
#    "value": "0"
#}
@app.put('/valves/<string:id>')
def put_valves(id):
    if not id in valveDict:
        return id + "not found in valve dictionary", 204
    else:
        valve = valveDict[id]

    if request.is_json:
        body = request.get_json()
    else:
        return {"error": "Request must be JSON"}, 415

    if not 'value' in body:
        return "value param not found", 400
    else:
        value = body['value']
        if (value == '0') or (value == '1'):
            SetWemosGpio(valve['ip'], valve['gpio'], value)
            return "DONE", 201
        else:
            return "value shall be '0' or '1'", 400

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
    #rest = RestClient()
    #storedValvesDict = rest.getValves()
    #logging.debug ('stored:')
    #logging.debug(storedValvesDict)

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
