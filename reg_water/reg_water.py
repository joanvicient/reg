#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that handles the watering tasks
# it has a rest api to add, modify and remove tasks
# it also has cron task to water at the set time

#from valve import Valve
from flask import Flask, jsonify, request, redirect
from mqttclient import MqttClient
import socket
import logging
import argparse
import json
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time
import requests

# parser ############################################################################################################
parser = argparse.ArgumentParser(description='Handles task and provides a REST API to edit them.')
parser.add_argument('-p', '--port', type=int, help='REST server port', default=5002, dest="port")
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

# REST server ###############################################################################################################
#TODO: create and add yaml to repo: https://editor.swagger.io/
app = Flask(__name__)
app.url_map.strict_slashes = False
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# returns all tasks
@app.get('/tasks/')
def get_all_tasks():
    logger.info('GET ' + str(taskDict))
    return jsonify(taskDict)

#if existing task of the same valve at the same time, updates it
#else, adds a new task
@app.post('/tasks/')
def add_task():
    if not request.is_json:
        logger.error("body shall be json")
        return "body shall be json", 415

    body = request.get_json()
    logger.debug("POST reg/ " + str(body) + '. type: ' + str(type(body)))

    if type(body) == dict:
        task = body
    else:
        task = json.loads(body)

    #check required parameters
    if not 'valve' in task:
        logger.error("not valve specified in body")
        return "not valve specified in body", 400
    
    def is_valid_duration(var: int):
        # is an integer
        if not isinstance(var, int):
            logger.error("duration_s shall be a integer")
            return False
        
        # is lower or equal than 2 minutes
        if var > 120:
            logger.error("duration_s shall be lower or equal than 2 minutes")
            return False
        
        return True

    if not 'duration_s' in task:
        logger.error("duration_s missing")
        return "duration_s missing", 400
    duration_s = task['duration_s']
    if not is_valid_duration(duration_s):
        logger.error("duration_s invalid")
        return "duration_s invalid", 400

    def is_valid_weekday_list(var):
        # Check if the variable is a list
        if not isinstance(var, list):
            return False
    
        # Check if all elements in the list are integers and less than 7
        if all(isinstance(item, int) and item < 7 for item in var):
            return True
        else:
            return False

    if (not 'weekday' in task) or not is_valid_weekday_list(task['weekday']):
        return "weekday missing or invalid", 400

    def is_valid_hour(var):
        # is an integer
        if not isinstance(var, int):
            return False
        
        # is lower than 24h
        if var > 23:
            return False
        
        return True

    if (not 'hour' in task) or (not is_valid_hour(task['hour'])):
        return "hour missing or invalid", 400
    
    valve = str(task['valve'])
    hour = str(task['hour'])
    if valve+hour in taskDict:
        logger.info('removing old task')
        del taskDict[valve+hour]
    
    logger.info('adding task ' + valve + hour + ' : ' + str(task))
    taskDict[valve+hour] = task
    return 'added', 200

#removes the task for the same valve at the same time
@app.delete('/tasks/')
def del_task():
    if not request.is_json:
        return "body shall be json", 415

    body = request.get_json()
    logger.debug("PUT reg/ " + str(body))
    task = json.loads(body)

    #check required parameters
    if not 'valve' in task:
        return "not valve specified in body", 400

    if (not 'hour' in task) or (not str(task['hour']).isdigit()) or (int(task['hour']) > 23):
        return "hour missing or invalid", 400
    
    valve = str(task['valve'])
    hour = str(task['hour'])
    if valve+hour in taskDict:
        logger.info('removing old task')
        del taskDict[valve+hour]
        return 'removed', 200
    else:
        logger.error('Not found')
        return 'task not found', 400

# returns app log in json format
@app.get('/log/')
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

# home route that redirects to tasks page
@app.route("/")
def home():
    return redirect("/tasks")

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
mqtt = MqttClient("reg_water", ['reg/reg_valves/info'], on_mqtt_callback)
serverInfoDict = GenerateServerInfoDict(args.port)
mqtt.publish("reg/reg_water/info", serverInfoDict, retain = True)
logger.info("MQTT client init successful")

# SCHEDULER ######################################################################################################################
def water(valve : str, duration_s : int):
    with app.app_context():
        logger.info('Watering ' + valve + ' for ' + str(duration_s) + ' seconds')
        # TODO: try
        if reg_url == None:
            logger.error('reg_valve not available')
        else:
            headers = {'Content-Type': 'application/json'}
            body = { "valve" : valve, "duration_s" : duration_s}
            logger.debug('PUT ' + reg_url + ' ' + str(body))

            requests.put(reg_url, headers=headers, data=json.dumps(body))

def my_hourly_task():
    with app.app_context():
        logger.debug("Hourly task is running at " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

        # Get the current date and time
        now = datetime.now()
        current_weekday = now.weekday()
        current_hour = now.hour

        jobs = []
        for task_name in taskDict:
            task = taskDict[task_name]
            logger.debug(task)
            if current_weekday not in task['weekday']:
                logger.debug('not today')
                continue

            if current_hour != task['hour']:
                logger.debug('not now')
                continue

            jobs.append(task)

        #start jobs
        for j in jobs:
            water(j['valve'], j['duration_s'])
            time.sleep(60+j['duration_s'])

        logger.info('Watering done!')

def my_minutely_task():
    with app.app_context():
        logger.debug("Minutely task is running at " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        return

# Define the one-time task to be scheduled
# this task is called every day at 23:00
# it will add a new task for each valve
# it is a debug/develop function
def my_one_time_task():
    with app.app_context():
        logger.debug("One-time task is running at " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        r = requests.get(valves_url)
        valves = r.json()
        logger.debug('valves: ' + str(valves))
        for valve in valves:
            if valve != 'main':
                body = {}
                body['weekday'] = [0,1,2,3,4,5,6]
                body['hour'] = 23
                body['duration_s'] = 5
                body['valve'] = valve
                reg_water_url = 'http://localhost:' + str(args.port) + '/tasks/'
                r = requests.post(reg_water_url, json=json.dumps(body))
                logger.debug('POST ' + reg_water_url + ' ' + str(body) + ' - ' + str(r.status_code))
            else:
                pass

        logger.info('Watering!')
        my_hourly_task()
        logger.info('One-time task done!')

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(my_hourly_task, 'cron', minute=0)
#scheduler.add_job(my_minutely_task, 'cron', second=0)

# Schedule the one-time task to run a few seconds after the program starts
# debug task
# scheduler.add_job(my_one_time_task, 'date', run_date=datetime.now() + timedelta(seconds=5))

scheduler.start()

logger.info("Starting the scheduler at " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

#######################################################################################################################
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=args.port)

    #never gets that far
    print('')
    print('')
    print('DONE:')
    for t in taskDict:
        print('key: ' + t + ' - Value: '+ str(taskDict[t]))
