#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Class to interact with wemos

# Requirements:
# python -m pip install --upgrade pip
# pip install requests

import logging
import requests
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Set urllib3 logger to WARNING to suppress debug messages
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

MIN_REFRESH_TIME_SECONDS = 60
MAX_ACTIVE_TIME_SECONDS = 60

class Valve:
    def __init__(self, name: str, ip: str, gpio: int, esp: str, status: int, auto_deactivate_time: int = MAX_ACTIVE_TIME_SECONDS):
        self.name = name
        self.ip = ip
        self.gpio = gpio
        self.esp = esp

        self._is_active = int(status) != 0
        self._status_updated = datetime.now()

        self._timer = None
        self._auto_deactivate_time = auto_deactivate_time

        self._lock = threading.Lock()
        logger.debug('created valve ' + self.name + ' at ' + self.ip + ', gpio ' + str(self.gpio) + '. Active: ' + str(self._is_active))
    
    def __str__(self):
        return self.name
        #return f"{self.name} in {self.esp} ({self.ip}) at gpio {self.gpio}"

    def get_json(self) -> dict:
        return {
            "name": self.name,
            "ip": self.ip,
            "gpio": self.gpio,
            "esp": self.esp,
            "status": self._is_active,
            "auto_deactivate_time": self._auto_deactivate_time
        }

    def get_status(self) -> bool:
        is_expired = datetime.now() - self._status_updated > timedelta(seconds=MIN_REFRESH_TIME_SECONDS)
        if self._is_active == None or is_expired:
            self._fetch_status()

        return self._is_active

    def activate(self) -> bool:
        logger.debug('Activating valve ' + self.name)
        return self._setValue(1)

    def deactivate(self) -> bool:
        return self._setValue(0)

    def _setValue(self, value: int) -> bool:
        toReturn = False
        logger.debug('Setting gpio ' + str(self.gpio) + ' to ' + str(value))
        with self._lock:
            self._is_active = None
            self._status_updated = 0
            try:
                url = ("http://" + self.ip + "/control?cmd=GPIO," + str(self.gpio) + "," + str(value))
                r = requests.get(url, timeout=0.5)
                if r.status_code == requests.codes.ok:
                    state = r.json()["state"]
                    logger.debug('GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ") - Valve state = " + str(state))
                    
                    # Update internal state, there is a bug in the ESP32 firmware that returns the old state
                    self._is_active = bool(value)
                    self._status_updated = datetime.now()

                    # if active, update timer for auto-disable
                    if self._is_active:
                        self._setAutoDeactivateTimer()

                    toReturn = True

                else:
                    logger.error('GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ")")

            except Exception as e:
                logger.error("exception on GET " + url + ": " + e.__class__.__name__)

        return toReturn

    def _fetch_status(self) -> bool:
        toReturn = False
        logger.debug('Fetching status of gpio ' + str(self.gpio))
        with self._lock:
            self._is_active = None
            self._status_updated = 0
            try:
                url = ("http://" + self.ip + "/control?cmd=Status,GPIO," + str(self.gpio))
                r = requests.get(url, timeout=0.5)
                if r.status_code == requests.codes.ok:
                    state = r.json()["state"]
                    logger.debug('GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ") - Valve state = " + str(state))

                    # Update internal state
                    self._is_active = bool(state)
                    self._status_updated = datetime.now()

                    toReturn = True

                else:
                    logger.error('GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ")")

            except Exception as e:
                logger.error("exception on GET " + url + ": " + e.__class__.__name__)

        return toReturn
    
    def _setAutoDeactivateTimer(self) -> None:
        # Cancel·la qualsevol temporitzador anterior (per seguretat)
        if self._timer:
            self._timer.cancel()

        # Programa la desactivació després de self._auto_deactivate_time
        self._timer = threading.Timer(self._auto_deactivate_time, self.deactivate)
        self._timer.daemon = True  # no bloqueja la sortida del programa
        self._timer.start()

if __name__ == '__main__':
    import time
    MAX_TIME = 2
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    v = Valve('freses', '192.168.0.146', 15, "someESP32", 0, auto_deactivate_time=MAX_TIME)

    print("Printing valve json")
    print(v.get_json())
    print()

    print("Testing valve activation")
    v.activate()
    time.sleep(1)
    if not v.get_status():
        logger.error("Valve should have been activated")
        exit(1)
    else:
        logger.info("Valve was correctly activated")
    time.sleep(1)

    print("Testing valve deactivation")
    v.deactivate()
    time.sleep(1)
    if v.get_status():
        logger.error("Valve should have been deactivated")
        exit(1)
    else:
        logger.info("Valve was correctly deactivated")
    time.sleep(1)

    print("Testing valve automatic deactivation")
    v.activate()
    time.sleep(MAX_TIME + 2)
    if v.get_status():
        logger.error("Valve should have been deactivated automatically")
        exit(1)
    else:
        logger.info("Valve was correctly deactivated automatically")

    print("Testing valve automatic deactivation after some activations")
    v.activate()
    time.sleep(MAX_TIME * 0.75)
    v.activate()
    time.sleep(MAX_TIME * 0.75)
    v.activate()
    time.sleep(MAX_TIME * 0.75)
    if not v.get_status():
        logger.error("Valve should be still active")
        exit(1)
    time.sleep(MAX_TIME)
    if v.get_status():
        logger.error("Valve should have been deactivated automatically")
        exit(1)
    else:
        logger.info("Valve was correctly deactivated automatically")
        exit(0)
