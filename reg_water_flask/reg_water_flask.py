#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# website that allows to create and remove watering tasks

#from valve import Valve
from flask import Flask, render_template, request, redirect, url_for
from mqttclient import MqttClient
import socket
import logging
import argparse
import json
import requests

# parser ############################################################################################################
parser = argparse.ArgumentParser(description='Handles task and provides a REST API to edit them.')
parser.add_argument('-p', '--port', type=int, help='REST server port', default=5003, dest="port")
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
taskDict = {}
valves_url = None
reg_url = None
tasks_url = None

### MQTT client ######################################################################
def on_mqtt_callback(topic, payload):
    if (topic == 'reg/reg_valves/info'):
        a = json.loads(payload)
        reg_valve_ip = str(a['ip'])
        reg_valve_port = str(a['port'])
        global valves_url
        valves_url = 'http://' + reg_valve_ip + ':' + reg_valve_port + '/valves/'
        global reg_url
        reg_url = 'http://' + reg_valve_ip + ':' + reg_valve_port + '/reg/'
        logging.info('valves_url: ' + valves_url + ' reg_url: ' + reg_url)
    elif (topic == 'reg/reg_water/info'):
        a = json.loads(payload)
        reg_tasks_ip = str(a['ip'])
        reg_tasks_port = str(a['port'])
        global tasks_url
        tasks_url = 'http://' + reg_tasks_ip + ':' + reg_tasks_port + '/tasks/'
        logging.info('tasks_url: ' + tasks_url)
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

# init mqtt client
mqtt = MqttClient("reg_water_flask", ['reg/reg_valves/info', 'reg/reg_water/info'], on_mqtt_callback)
serverInfoDict = GenerateServerInfoDict(args.port)
mqtt.publish("reg/reg_water_flask/info", serverInfoDict, retain = True)
logger.info("MQTT client init successful")

#######################################################################################################################
app = Flask(__name__)

@app.route('/')
def index():
    response = requests.get(tasks_url)
    tasks = response.json()
    logger.debug(str(type(tasks)) + ' ' + str(tasks))
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_item():
    valve = request.form['valve']
    duration_s = request.form['duration_s']
    weekday = str(request.form['week_day_list']).split(',')
    hour = request.form['hour']

    new_item = {
        'valve': valve,
        'duration_s': int(duration_s),
        'weekday': [int(x) for x in weekday],
        'hour': int(hour)
    }
    logger.debug('POST ' + tasks_url + ' --> ' + str(new_item))
    response = requests.post(tasks_url, json=new_item)
    if response.status_code == 200:
        return redirect(url_for('index'))
    else:
        return 'Error: Item could not be created', response.status_code

@app.route('/delete', methods=['POST'])
def delete_item():
    #TODO: get valve and hour from parameters
    item = {
        'valve': 'tomates',
        'hour': 4
    }
    logger.debug('DELETE ' + tasks_url + ' --> ' + str(item))
    response = requests.delete(tasks_url, json=item)
    if response.status_code == 200:
        return redirect(url_for('index'))
    else:
        return 'Error: Item could not be deleted', response.status_code



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=args.port)

