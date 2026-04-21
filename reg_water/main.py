#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api import TaskApi
from task_manager import TaskManager
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    task_manager = TaskManager()
    app = TaskApi(task_manager)
    app.run()
