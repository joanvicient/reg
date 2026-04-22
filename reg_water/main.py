#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api import TaskApi
from task_manager import TaskManager
import logging
import os

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    #get reg_valves hostname and port from env
    valves_host = "nasf8b4c9.local"
    valves_port = "5501"
    if 'REG_VALVES_HOST' in os.environ:
        valves_host = os.environ['REG_VALVES_HOST']
        logging.info("REG_VALVES_HOST set to " + valves_host)
    if 'REG_VALVES_PORT' in os.environ:
        valves_port = os.environ['REG_VALVES_PORT']
        logging.info("REG_VALVES_PORT set to " + valves_port)

    task_manager = TaskManager(valves_host, valves_port)
    app = TaskApi(task_manager)
    app.run()
