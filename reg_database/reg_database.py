#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# init python that stores iformation
# this information can be load and saved using a REST api
# this rest api is found at port 5000

#requirements:
# pip install Flask

from flask import Flask, jsonify, request
import logging
import sys

#---------------------------------------------------
app = Flask(__name__)

#---------------------------------------------------
valves = { }
#valves = {'Tomates': {'gio': '5', 'hostname': 'esp24.lan'}, 'carbasso': {'gio': '15', 'hostname': 'esp22.lan'}, 'main': {'gio': '2', 'hostname': 'esp22.lan'}, 'petita': {'gio': '2', 'hostname': 'esp21.lan'}, 'raim': {'gio': '15', 'hostname': 'esp21.lan'}}


@app.get('/valves')
def get_all_valves():
    logging.debug('GET ' + str(valves))
    return jsonify(valves)

@app.get('/valves/<string:id>')
def get_valves(id):
    logging.debug("GET id: " + id)
    if id in valves:
        #print(id + " exists")
        return jsonify(valves[id])
    else:
        #print(id + ' do not exists')
        return "Not found", 204

@app.post('/valves')
def add_valves():
    if request.is_json:
        valve = request.get_json()
        logging.debug("Posting " + str(valve))
        valves.update(valve)
        return valve, 201
    
    return {"error": "Request must be JSON"}, 415

#---------------------------------------------------
if __name__ == "__main__":
    #init logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    app.run()
