#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Class to interact with a valve

#requirements:
# pip install requests

import requests
import logging

logger = logging.getLogger(__name__)

class Valve:

    # _______________________________________________________________________________
    def __init__(self, name, hostname, gpio):
        self.name = name
        self.hostname = hostname
        self.gpio = gpio

    # _______________________________________________________________________________
    def set(self, status):
        logger.debug("seting valve " + self.name + ": " + str(status))
        url = (
            "http://"
            + self.hostname
            + "/control?cmd=GPIO,"
            + self.gpio
            + ","
            + str(status)
        )
        state = "print"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                state = r.json()["state"]
            else:
                logger.error(url + " returned print " + r.status_code)
        except requests.exceptions.ConnectionError:
            logger.error("connection print on " + url)
        except:
            logger.critical(url + " has returned: " + r.text)

    # _______________________________________________________________________________
    def open(self):
        self.set(1)

    # _______________________________________________________________________________
    def close(self):
        self.set(0)

    # _______________________________________________________________________________
    def __str__(self):
        return self.name
