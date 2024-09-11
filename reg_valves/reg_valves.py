#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that discover all valves
# and keeps listening waiting for mqtt instructions

#from valve import Valve
from flask import Flask, jsonify, request, redirect
from wemos import DiscoverValvesIn, UpdateValve, SetWemosGpio
from mqttclient import MqttClient
import socket
import time
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor
import threading

# parser ############################################################################################################
parser = argparse.ArgumentParser(description='Discovers valves using MQTT and provides a REST API to controll them.')
parser.add_argument('-p', '--port', type=int, help='REST server port', default=5001, dest="port")
parser.add_argument("-l", "--log-level", type=str.upper, help='INFO or DEBUG', default="INFO", dest="log_level")
args = parser.parse_args()

# init logging #######################################################################################################
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_entries = []

    def emit(self, record):
        log_entry = {
            'date': self.formatter.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            'level': record.levelname,
            'name': record.name,
            'text': record.getMessage()
        }
        self.log_entries.append(log_entry)

# Create the custom log handler
list_handler = ListHandler()

# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format, handlers=[list_handler])

# Also log to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(getattr(logging, args.log_level))
stdout_handler.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(stdout_handler)

logger = logging.getLogger(__name__)
# start logs
logger.info('Log level: ' + args.log_level)
logger.info('REST api available at port ' + str(args.port))

# Define log level priority
log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
log_level_priority = {level: index for index, level in enumerate(log_levels)}

# global variables #########################################################################################################
lock = threading.Lock()
espDict = {}
valveDict = {}

# REST server ###############################################################################################################
app = Flask(__name__)
app.url_map.strict_slashes = False
executor = ThreadPoolExecutor()
logging.getLogger('werkzeug').setLevel(logging.ERROR)


#TODO: create and add yaml to repo: https://editor.swagger.io/
@app.get("/config/")
def get_config():
    return "Log level: " + str(logger.getLevelName()), 200

@app.patch("/config/")
def patch_config():
    if request.is_json:
        body = request.get_json()
        logger.debug('PATCH config - Body: ' + str(body))
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
            logger.error('log_level ' + level + " not supported")
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
    logger.debug('GET ' + str(espDict))
    logger.info('GET esp')
    return jsonify(espDict)

# returns all the discovered valves
@app.get('/valves/')
def get_all_valves():
    logger.debug('GET ' + str(valveDict))
    logger.info('GET valves')
    return jsonify(valveDict)

# returns the required valve 
# it forces to get the current value of each valve
@app.get('/valves/<string:id>')
def get_valves(id):
    logger.debug("GET id: " + id)
    if not id in valveDict:
        return "Not found", 204
    else:
        valve = valveDict[id]
        value = UpdateValve(valve['name'], valve['ip'])
        valveDict[id]['value'] = value
        logger.info('GET valves/'+valve['name'])
        return jsonify(valve)

# PATCH localhost:5001/valves/farigola
# with body:
#{
#    "value": "0"
#}
@app.patch('/valves/<string:id>')
def patch_valves(id):
    logger.debug('PATCH valves/' + id)
    if not id in valveDict:
        return id + "not found in valve dictionary", 204
    else:
        valve = valveDict[id]

    if request.is_json:
        body = request.get_json()
        logger.debug('Body: ' + str(body))
    else:
        return {"error": "Request must be JSON"}, 415

    if not 'value' in body:
        return "value param not found", 400

    value = body['value']
    if (value != '0') and (value != '1'):
        return "value shall be '0' or '1'", 400

    if lock.acquire(blocking=False):
        logger.info('PATCH valves/' + valve['name'] + " = " + value)
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
    logger.debug("PUT reg/ " + str(body))

    if not request.is_json:
        return "body shall be json", 415

    if not 'valve' in body:
        return "not valve specified in body", 400

    if (not 'duration_s' in body) or (not str(body['duration_s']).isdigit()):
        return "duration_s missing or invalid", 400

    valve = str(body['valve'])
    duration_s = int(body['duration_s'])

    if not valve in valveDict:
        return 'unknown valve: ' + valve, 400

    if lock.acquire(blocking=False):
        logger.info('Watering ' + valve + ' during ' + str(duration_s) + ' seconds.')

        #execute blocking the REST response
        #ret = reg_task(valve, duration_s)
        #lock.release()

        # Execute the background task asynchronously
        executor.submit(reg_task, valve, duration_s)
        ret = "Scheduled " + valve + ' for ' + str(duration_s) + ' seconds.', 200
    else:
        ret = "already executing something", 500

    return ret

# returns app log in json format
@app.route('/log', methods=['GET'])
def log_endpoint():
    # Get the 'level' parameter from the query string (default to 'INFO' if not provided)
    level = request.args.get('level', 'INFO').upper()

    # Validate the logging level
    if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        return jsonify({'error': f'Invalid log level: {level}'}), 400

    # Filter logs by the specified level and higher priority levels
    min_priority = log_level_priority[level]
    filtered_logs = [entry for entry in list_handler.log_entries if log_level_priority[entry['level']] >= min_priority]

    # Return the filtered logs as part of the response
    return jsonify(filtered_logs), 200

### MQTT client ######################################################################
def UpdateValveDict(vDict):
    for v in vDict:
        if v in valveDict:
            if vDict[v] == valveDict[v]:
                logger.debug('Valve already exists: ' + str(v))
            else:
                logger.debug('Valve already exists: ' + str(v) + ' with different values. Updating it')
                del valveDict[v]
                valveDict[v] = vDict[v]
        else:
            logger.info('* Adding valve: ' + str(v))
            valveDict[v] = vDict[v]

def register_or_unregister_esp(esp, payload):
    if (payload == 'ON'):
        logger.info(esp + ' is ONLINE')
    elif (payload == 'OFF'):
        logger.info(esp + ' is OFFLINE')
        #remove esp entry in espdict
        if esp in espDict:
            logger.info('* Removing esp: ' + esp)
            del espDict[esp]
        else:
            logger.info('* Unknown esp: ' + esp)
        #remove valves from valveDict
        for v in list(valveDict):
            v_esp = valveDict[v]['esp']
            logger.debug('In ' + v_esp)
            if (v_esp == esp):
                logger.info('* Removing valve: ' + str(v))
                del valveDict[v]
            else:
                logger.debug('* '+ v + ': ' + v_esp + ' is not ' + esp)
    else:
        logger.error('unknown payload for ' + esp + ': ' + payload)

def update_esp_value(esp, key, value):
    oldValue = '0'
    if esp in espDict:
        if key in espDict[esp]:
            oldValue = espDict[esp][key]
        espDict[esp][key] = value
    else:
        newEspDict = {}
        newEspDict[key] = value
        espDict[esp] = newEspDict

    if (key == 'ip4'):
        if value == '0':
            logger.info('Invalid IP value for ' + esp)
        elif value == oldValue:
            logger.debug('Value for ' + key + ' in ' + esp + ' unchanged: ' + value)
        else:
            logger.info('Value for ' + key + ' in ' + esp + ' updated: ' + value)
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
        #logger.debug('MQTT: ' + topic + ", with body: " + payload)
        topic_list = str(topic).split('/')
        if len(topic_list) == 2:
            # a esp is online or offline
            # topic: esp/<espX>
            # payload: ON or OFF
            register_or_unregister_esp(topic_list[1], payload)
        elif len(topic_list) == 3:
            # a valve value has changed
            # topic: esp/<espX>/status
            # payload: <value>
            # TODO: can return an error!!!!!!!
            if topic_list[2] == 'status':
                update_valve_status(topic_list[1], payload)
            else:
                logger.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")
        elif len(topic_list) == 4:
            # an esp statistic has been reported
            # topic: esp/<espX>/ip or esp/<espX>/info
            if topic_list[2] == 'ip' or 'info':
                update_esp_value(topic_list[1], topic_list[3], payload)
            else:
                logger.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")
        elif len(topic_list) > 4:
            logger.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")
    else:
        logger.error('uncached topic: ' + topic + ' - ' + payload)

def GenerateServerInfoDict(rest_port):
    serverInfoDict = {}

    hostname=socket.gethostname()
    IPAddr=socket.gethostbyname(hostname)

    serverInfoDict['hostname'] = hostname
    serverInfoDict['ip'] = IPAddr
    serverInfoDict['port'] = rest_port

    return serverInfoDict

# init mqtt client
mqtt = MqttClient("reg_valves", ['esp/#'], on_mqtt_callback)
serverInfoDict = GenerateServerInfoDict(args.port)
mqtt.publish("reg/reg_valves/info", serverInfoDict, retain = True)
logger.info("MQTT client init successful")

## reg tasks #########################################################################################################
def reg_task(valve: str, duration_s: int):
    logger.info('watering ' + valve + ' for ' + str(duration_s) + ' seconds.')
    if not valve in valveDict:
        logger.error(' unknown valve ' + valve)
        lock.release()
        return 'unknown valve', 400

    if not 'main' in valveDict:
        logger.error('main valve not available')
        lock.release()
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
    print('###############check this line is duplicated############')
    logger.error('watering ' + valve + ' done.')
    lock.release()
    return 'watering ' + valve + ' done.', 200

#######################################################################################################################
if __name__ == "__main__":
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
