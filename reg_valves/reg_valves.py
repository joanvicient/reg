#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions

#from valve import Valve
from flask import Flask, jsonify, request, redirect
from wemos import DiscoverValvesIn, UpdateValve, SetWemosGpio
from mqttclient import MqttClient
from restclient import RestClient
import socket
import time
import logging
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor
import threading

# Create a lock
lock = threading.Lock()

espDict = {}
valveDict = {}
app = Flask(__name__)
executor = ThreadPoolExecutor()
logging.getLogger('werkzeug').setLevel(logging.ERROR)


#TODO: create and add yaml to repo: https://editor.swagger.io/
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

# returns all the discovered wemos D1 mini
@app.get('/esp/')
def get_all_esp():
    logging.debug('GET ' + str(espDict))
    logging.info('GET esp')
    return jsonify(espDict)

# returns all the discovered valves
@app.get('/valves/')
def get_all_valves():
    logging.debug('GET ' + str(valveDict))
    logging.info('GET valves')
    return jsonify(valveDict)

# returns the required valve 
# it forces to get the current value of each valve
@app.get('/valves/<string:id>')
def get_valves(id):
    logging.debug("GET id: " + id)
    if not id in valveDict:
        return "Not found", 204
    else:
        valve = valveDict[id]
        value = UpdateValve(valve['name'], valve['ip'])
        valveDict[id]['value'] = value
        logging.info('GET valves/'+valve['name'])
        return jsonify(valve)

# PATCH localhost:5001/valves/farigola
# with body:
#{
#    "value": "0"
#}
@app.patch('/valves/<string:id>')
def patch_valves(id):
    logging.debug('PATCH valves/' + id)
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

    value = body['value']
    if (value != '0') and (value != '1'):
        return "value shall be '0' or '1'", 400

    if lock.acquire(blocking=False):
        logging.info('PATCH valves/' + valve['name'] + " = " + value)
        return SetWemosGpio(valve['ip'], valve['gpio'], value)
        lock.release()
    else:
        return "already executing something", 500

# PUT localhost:5001/reg/
# with body:
# {
# "valve": "freses",
# "duration_s": "10"
# }
@app.put('/reg/')
def put_reg():
    body = request.get_json()
    logging.debug("PUT reg/ " + str(body))

    if not request.is_json:
        return "body shall be json", 415

    if not 'valve' in body:
        return "not valve specified in body", 400

    if (not 'duration_s' in body) or (not str(body['duration_s']).isdigit()):
        return "duration_s missing or invalid", 400

    valve = str(body['valve'])
    duration_s = int(body['duration_s'])

    if lock.acquire(blocking=False):
        logging.info('Watering ' + valve + ' during ' + str(duration_s) + ' seconds.')

        #execute blocking the REST response
        #ret = reg_task(valve, duration_s)
        #lock.release()

        # Execute the background task asynchronously
        executor.submit(reg_task, valve, duration_s)
        ret = "Scheduled " + valve + ' for ' + str(duration_s) + ' seconds.', 200
    else:
        ret = "already executing something", 500

    return ret

### end REST server ##################################################################

### MQTT client ######################################################################
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

def register_or_unregister_esp(esp, payload):
    if (payload == 'ON'):
        logging.info(esp + ' is ONLINE')
    elif (payload == 'OFF'):
        logging.info(esp + ' is OFFLINE')
        for v in list(valveDict):
            if (valveDict[v]['esp'] == esp):
                logging.info(' - Removing valve: ' + str(v))
                del valveDict[v]

def update_esp_value(esp, key, value):
    if esp in espDict:
        espDict[esp][key] = value
    else:
        newEspDict = {}
        newEspDict[key] = value
        espDict[esp] = newEspDict

    if (key == 'ip4' and value != '0'):
        ip = "192.168.1." + value
        UpdateValveDict(DiscoverValvesIn(esp, ip))

def update_valve_status(esp, payload):
    if not esp in espDict:
        return 0

    cmd = str(payload).split(',')
    if len(cmd) != 3:
        return 1

    valve = cmd[0]
    value = cmd[2]
    
    if not valve in valveDict:
        return 2
    
    valveDict[valve]['value'] = value

def on_mqtt_callback(topic, payload):
    if (topic[0:4] == 'esp/'):
        #logging.debug('MQTT: ' + topic + ", with body: " + payload)
        topic_list = str(topic).split('/')
        if len(topic_list) == 2:
            register_or_unregister_esp(topic_list[1], payload)
        elif len(topic_list) == 3:
            if topic_list[2] == 'status':
                update_valve_status(topic_list[1], payload)
            else:
                logging.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")
        elif len(topic_list) == 4:
            if topic_list[2] == 'ip' or 'info':
                update_esp_value(topic_list[1], topic_list[3], payload)
            else:
                logging.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")
        elif len(topic_list) > 4:
            logging.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")
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

## end mqtt ##########################################################################################################


## reg tasks #########################################################################################################
def reg_task(valve: str, duration_s: int):
    print('watering ' + valve + ' for ' + str(duration_s) + ' seconds.')
    if not valve in valveDict:
        print(' unknown valve ' + valve)
        return 'unknown valve', 400

    if not 'main' in valveDict:
        print('main valve not available')
        return 'main not found', 500
    
    vDict = valveDict[valve]
    mDict = valveDict['main']

    SetWemosGpio(vDict['ip'],vDict['gpio'], '1')
    time.sleep(1)
    SetWemosGpio(mDict['ip'],mDict['gpio'], '1')
    time.sleep(duration_s)
    SetWemosGpio(mDict['ip'],mDict['gpio'], '0')
    time.sleep(3)
    SetWemosGpio(vDict['ip'],vDict['gpio'], '0')

    print('watering ' + valve + ' done.')
    lock.release()
    return 'watering ' + valve + ' done.', 200

## end reg tasks ######################################################################################################

#######################################################################################################################
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
    mqtt = MqttClient("reg_valves", ['esp/#'], on_mqtt_callback)
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

    print('')
    for esp in espDict:
        print('key: ' + esp + ' - Value: '+ str(valveDict[esp]))
