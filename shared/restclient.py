#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import requests
import json
import logging

logger = logging.getLogger(__name__)

class RestClient:
 
    server = "127.0.0.1"
    port = "5000"

    def __init__(self):
        self.urlbase = "http://" + self.server + ':' + self.port + '/'

    def get(self, item):
        url = self.urlbase + str(item)
        try:
            ret = requests.get(url)
            if ret.ok:
                return json.loads(ret.content)
            else:
                logging.error('requests error(get): ' + str(ret.status_code))
                return None

        except Exception as e:
            logger.critical(e)
            return None

    def getValves(self):
        return self.get('valves')

    def post(self, item, data):
        url = self.urlbase + str(item)

        try:
            ret = requests.post(url, json=data)
            if ret.ok:
                return True
            else:
                logger.error('request error(post):' + str(ret.status_code))
                return False
            
        except Exception as e:
            logger.critical('Exception in ' + __file__ )
            logger.critical(e)
            return False
        
    def postValves(self, valves):
        self.post('valves', valves)
