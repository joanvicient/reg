#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api import ValveApi
from manager import ValvesManager
from mqtt_discoverer import MqttDiscoverer
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    valves_manager = ValvesManager()
    valves_discoverer = MqttDiscoverer(valves_manager)
    app = ValveApi(valves_manager)
    app.run()
