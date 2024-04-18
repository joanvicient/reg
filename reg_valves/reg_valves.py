#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions

#from valve import Valve
from flask import Flask, jsonify, request, redirect
from wemos import DiscoverValvesIn, SetWemosGpio
from mqttclient import MqttClient
from restclient import RestClient
import socket
import time
import logging
import sys
import argparse

valveDict = {}
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.get("/config/")
def get_config():
    return "Log level: " + str(logging.getLevelName()), 200

@app.patch("/config/")
def patch_config():
    if request.is_json:
        body = request.get_json()
        logging.debug('PATCH config - Body: ' + str(body))
    else:
        return {"error": "Request must be JSON"}, 415

    if 'log_level' in body:
        level = str(body['log_level']).upper()
        if level == 'INFO':
            logging.getLogger().setLevel(logging.INFO)
            return "Loglevel INFO set", 202
        if level == 'DEBUG':
            logging.getLogger().setLevel(logging.DEBUG)
            return "Log_level DEBUG set", 202
        else:
            logging.error('log_level ' + level + " not supported")
            return "ERROR: log_level supported: INFO, ", 400
    else:
        return "log_level is the only supported parameter", 400

# home route that redirects to
# valves page
@app.route("/")
def home():
    return redirect("/valves")

# returns all the discovered valves
@app.get('/valves/')
def get_all_valves():
    logging.debug('GET ' + str(valveDict))
    logging.info('GET valves')
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
            logging.info('GET valves/'+valve['name'])
            return jsonify(valve)
        elif 'value' in args:
            value = args['value']
            if value=='1' or value=='0':
                logging.info('custom POST using GET -> ' + valve['name'] + " = " + value)
                return SetWemosGpio(valve['ip'], valve['gpio'], value)
            else:
                return 'value param only accepts 0 or 1', 400
        else:
            logging.error('wrong args: ' + str(args) + " for " + valve['name'])
            return 'bad argument', 400

# PUT localhost:5001/valves/farigola
# with body:
#{
#    "value": "0"
#}
@app.put('/valves/<string:id>')
def put_valves(id):
    logging.debug('PUT valves/' + id)
    if not id in valveDict:
        return id + "not found in valve dictionary", 204
    else:
        valve = valveDict[id]

    if request.is_json:
        body = request.get_json()
        logging.debug('Body: ' + str(body))
    else:
        return {"error": "Request must be JSON"}, 415

    if not 'value' in body:
        return "value param not found", 400
    else:
        value = body['value']
        if (value == '0') or (value == '1'):
            logging.info('PUT valves/' + valve['name'] + " = " + value)
            return SetWemosGpio(valve['ip'], valve['gpio'], value)
        else:
            return "value shall be '0' or '1'", 400

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
            logging.info(' - Adding valve: ' + str(v))
            valveDict[v] = vDict[v]

def on_esp(topic, payload):
    if (topic[0:7]=='esp/esp'):
        esp = topic[4:]
        if (payload == 'ON'):
            logging.info(esp + ' is ONLINE')
        elif (payload == 'OFF'):
            logging.info(esp + ' is OFFLINE')
            for v in list(valveDict):
                if (valveDict[v]['esp'] == esp):
                    logging.info(' - Removing valve: ' + str(v))
                    del valveDict[v]

    elif (topic[:8]=='esp/ip4/' and payload != '0'):
        esp = topic[8:]
        ip = '192.168.1.' + payload
        UpdateValveDict(DiscoverValvesIn(esp, ip))
    else:
        logging.error(topic + ' - ' + payload)

def on_mqtt_callback(topic, payload):
    if (topic[0:4] == 'esp/'):
        on_esp(topic, payload)
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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Discovers valves using MQTT and provides a REST API to controll them.')
    parser.add_argument('-p', '--port', type=int, help='REST server port', default=5001, dest="port")
    parser.add_argument("-l", "--log-level", type=str.upper, help='INFO or DEBUG', default="INFO", dest="log_level")
    args = parser.parse_args()

    #init logging
    if args.log_level == 'DEBUG':
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    logging.info('Log level: ' + args.log_level)
    logging.info('REST api available at port ' + str(args.port))

    #init mqtt client
    mqtt = MqttClient("reg_valves", ['esp/+', 'esp/ip4/+'], on_mqtt_callback)
    serverInfoDict = GenerateServerInfoDict(args.port)
    mqtt.publish("reg/reg_valves/info", serverInfoDict, retain = True)

    logging.info("Init successful")

    app.url_map.strict_slashes = False
    app.run(host='0.0.0.0', port=args.port)

    #never gets that far
    print('')
    print('')
    print('DONE:')
    for v in valveDict:
        print('key: ' + v + ' - Value: '+ str(valveDict[v]))
