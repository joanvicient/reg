#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import threading
from task import Task
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import pickle
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.lock = threading.Lock()

        #using pickle to save and restore the tasks
        self._pickle_name = None
        self._init_pickle()
    
        # Initialize the scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.my_watering_task, 'cron', minute=0)
        self.scheduler.start()

    def get_tasks(self):
        with self.lock:
            return self.tasks
    
    def add_task(self, task: Task):
        #TODO revisar els lock

        #TODO: valves hauria de validar que existeix la valvula i retornar OK o error.
        # i llavors encuar la comanda de reg.
        with self.lock:
            for t in self.tasks.values():
                if t.is_the_same(task):
                    t.copy_from_task(task)
                    self._save_pickle()
                    logger.info(f"Updated task: {task}")
                    return True
            
            task_id = f"{task.valve}_{task.hour}"
            self.tasks[task_id] = task
            self._save_pickle()
            logger.info(f"Added task: {task}")
            return True

    def rm_task(self, task_id: str):
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                self._save_pickle()
                logger.info(f"Removed task: {task_id}")
                return True
            return False

    def my_watering_task(self):
        with self.lock:
            logger.debug("Watering task is running at " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

            jobs = []
            #logger.debug('taskDict: ' + str(taskDict))
            for task in self.tasks.values():
                if not task.active_now():
                    logger.debug(task.valve + ' not today')
                else:
                    if self.water(task.valve, task.duration):
                        logger.info(f"Watered {task.valve} for {task.duration} seconds")
                    else:
                        logger.error(f"Failed to water {task.valve}")

            logger.info('Watering done!')

    def water(self, valve: str, duration: int):
        logger.info(f"Watering {valve} for {duration} seconds")
        try:
            url = f"http://192.168.0.34:8080/reg/valves/{valve}/water"
            r = requests.post(url)
            r.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Failed to water {valve}: HTTP {e.response.status_code} - {e.response.text}")
            else:
                logger.error(f"Failed to water {valve}: {type(e).__name__} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to water {valve}: Unexpected error - {type(e).__name__}: {str(e)}")
            return False

    def _init_pickle(self):
        if os.path.isdir('/data') and os.access('/data', os.W_OK):
            self._pickle_name = '/data/autosave.pickle'
        elif os.access('.', os.W_OK):
            self._pickle_name = 'autosave.pickle'
        else:
            self._pickle_name = '/tmp/autosave.pickle'

        logger.info(f"Using autosave file {self._pickle_name}")
        self._load_pickle()

    def _load_pickle(self):
        """Loads the dictionary from a file if it exists."""
        if os.path.exists(self._pickle_name):
            with open(self._pickle_name, 'rb') as file:
                return pickle.load(file)
        return {}

    def _save_pickle(self):
        """Saves the dictionary to a file."""
        with open(self._pickle_name, 'wb') as file:
            pickle.dump(dict(self.tasks), file)

#########3 tests ##################

if __name__ == '__main__':
    task_manager = TaskManager()

    from datetime import datetime
    now = datetime.now()
    current_weekday = now.weekday()
    current_hour = now.hour
    task1 = Task("non_existing_valve1", current_hour, [current_weekday], 1)
    task2 = Task("non_existing_valve2", current_hour, [current_weekday+1], 1)
    task3 = Task("non_existing_valve3", current_hour, [current_weekday], 1)
    task4 = Task("non_existing_valve4", current_hour+2, [current_weekday], 1)

    task_manager.add_task(task1)
    task_manager.add_task(task2)
    task_manager.add_task(task3)
    task_manager.add_task(task4)
    task_manager.my_watering_task()

    print("Task 1 and 3 should have reported a error regarding valve not found")
    print("Task 2 and 4 should not have been reported")
