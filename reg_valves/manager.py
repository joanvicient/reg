#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Class to manage valves
from esp32 import Esp32
import time 
import logging
import threading
import uuid
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job:
    def __init__(self, valve_name: str, duration: int = 20):
        self.id = str(uuid.uuid4())
        self.valve_name = valve_name
        self.duration = duration
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error_message = None

    def to_dict(self):
        return {
            "id": self.id,
            "valve_name": self.valve_name,
            "duration": self.duration,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }

class ValvesManager:
    def __init__(self):
        self._esps = {}
        self._esps_lock = threading.Lock()
        self._jobs = []
        self._jobs_lock = threading.Lock()
        self._job_thread = None
        self._stop_job_thread = False

#################### private helper methods ########################################

    def _get_all_valves(self) -> list[str]:
        """Get all valves from all ESP32s (must be called with lock)"""
        valves = []
        for esp in self._esps.values():
            valves.extend(esp.get_valves())
        return valves

    def _get_all_valves_json(self) -> dict:
        """Get all valves JSON from all ESP32s (must be called with lock)"""
        valves = {}
        for esp in self._esps.values():
            valves.update(esp.get_valves_json())
        return valves

    def _get_esp_name(self, valve) -> str | None:
        """Get ESP name for valve (must be called with lock)"""
        logger.debug(f"Getting ESP for valve {valve}")
        for esp in self._esps.values():
            if valve in esp.get_valves():
                return esp.name
        return None

#################### valves management ###############################################

    def get_valves_list(self) -> list[str]:
        logger.debug("Getting valves list")
        with self._esps_lock:
            return self._get_all_valves()
    
    def get_valves_json(self) -> dict:
        with self._esps_lock:
            return self._get_all_valves_json()
    
    def get_valve_json(self, valve_name: str) -> dict:
        logger.debug(f"Getting valve JSON for {valve_name}")
        with self._esps_lock:
            esp = self._get_esp_name(valve_name)
            if esp is None:
                logger.error(f"Valve {valve_name} not found")
                return {}
            return self._esps[esp].get_valve_json(valve_name)

    def test_valve(self, valve_name: str, duration = 2) -> bool:
        logger.debug(f"Testing valve {valve_name}")
        with self._esps_lock:
            esp = self._get_esp_name(valve_name)
            if esp is None:
                logger.error(f"Valve {valve_name} not found")
                return False
            
            esp_obj = self._esps[esp]
            
            try:
                success = True
                success = success and esp_obj.open_valve(valve_name)
                time.sleep(duration)
                success = success and esp_obj.close_valve(valve_name)
                logger.info(f"Testing valve {valve_name} success: {success}")
                return success

            except Exception as e:
                logger.error(f"Error testing valve {valve_name}: {e}")
                esp_obj.close_valve(valve_name)
                return False

    def water_valve(self, valve_name: str, duration: int = 20) -> bool:
        logger.debug(f"Watering valve {valve_name}")
        with self._esps_lock:
            esp = self._get_esp_name(valve_name)
            if esp is None:
                logger.error(f"Valve {valve_name} not found")
                return False
            
            esp_valve = self._esps[esp]

            esp = self._get_esp_name("main")
            if esp is None:
                logger.error(f"Main valve not found")
                return False
            
            esp_main = self._esps[esp]

            try:
                success = True
                success = success and esp_valve.open_valve(valve_name)
                time.sleep(1)
                success = success and esp_main.open_valve("main")
                time.sleep(duration)
                success = success and esp_main.close_valve("main")
                time.sleep(2)
                success = success and esp_valve.close_valve(valve_name)
                logger.info(f"Watering valve {valve_name} success: {success}")
                return success

            except Exception as e:
                logger.error(f"Error watering valve {valve_name}: {e}")
                return False

###################### ESP management #############################################

    def get_esp32_list(self) -> list[str]:
        logger.debug("Getting ESP32 list")
        with self._esps_lock:
            return list(self._esps.keys())
    
    def get_esp32_json(self) -> list[dict]:
        logger.debug("Getting ESP32 JSON")
        with self._esps_lock:
            return [esp.get_json() for esp in self._esps.values()]

    def set_esp_value(self, name: str, key: str, value: str) -> bool:
        logger.debug(f"Setting ESP {name} value {key} to {value}")
        with self._esps_lock:
            if name not in self._esps:
                esp = Esp32(name)
                self._esps[name] = esp
            
            esp_obj = self._esps[name]
            
            return esp_obj.set_value(key, value)

#################### job management ##############################################

    def add_job(self, valve_name: str, duration: int = 20) -> str:
        """Add a new watering job and return job ID"""
        job = Job(valve_name, duration)

        with self._jobs_lock:
            self._jobs.append(job)

        # Start job processor thread if not running
        if self._job_thread is None or not self._job_thread.is_alive():
            self._start_job_processor()

        logger.info(f"Added job {job.id} for valve {valve_name}")
        return job.id

    def get_jobs(self) -> list[dict]:
        """Get all jobs"""
        with self._jobs_lock:
            return [job.to_dict() for job in self._jobs]

    def get_job(self, job_id: str) -> dict:
        """Get a specific job"""
        with self._jobs_lock:
            for job in self._jobs:
                if job.id == job_id:
                    return job.to_dict()
        return {}

    def _start_job_processor(self):
        """Start the background job processor thread"""
        self._stop_job_thread = False
        self._job_thread = threading.Thread(target=self._process_jobs, daemon=True)
        self._job_thread.start()
        logger.info("Started job processor thread")

    def _process_jobs(self):
        """Background thread to process pending jobs"""
        while not self._stop_job_thread:
            job_to_process = None

            with self._jobs_lock:
                # Find first pending job
                for job in self._jobs:
                    if job.status == JobStatus.PENDING:
                        job_to_process = job
                        job.status = JobStatus.RUNNING
                        job.started_at = datetime.now()
                        break

            if job_to_process:
                logger.info(f"Processing job {job_to_process.id} for valve {job_to_process.valve_name}")

                # Execute the watering
                success = self.water_valve(job_to_process.valve_name, job_to_process.duration)

                with self._jobs_lock:
                    job_to_process.completed_at = datetime.now()
                    if success:
                        job_to_process.status = JobStatus.COMPLETED
                        logger.info(f"Job {job_to_process.id} completed successfully")
                    else:
                        job_to_process.status = JobStatus.FAILED
                        job_to_process.error_message = "Watering operation failed"
                        logger.error(f"Job {job_to_process.id} failed")
            else:
                # No pending jobs, sleep briefly
                time.sleep(1)

################ test #################################################

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    manager = ValvesManager()

    print("Add first test esp: it contains main valve")
    manager.set_esp_value("test", "status", "ON")
    manager.set_esp_value("test", "uptime", "aaaaaa")
    manager.set_esp_value("test", "rssi", "-124")
    manager.set_esp_value("test", "ip1", "192")
    manager.set_esp_value("test", "ip2", "168")
    manager.set_esp_value("test", "ip3", "0")
    manager.set_esp_value("test", "ip4", "169")

    print("Add second test esp")
    manager.set_esp_value("test2", "status", "ON")
    manager.set_esp_value("test2", "uptime", "aaaaaa")
    manager.set_esp_value("test2", "rssi", "-124")
    manager.set_esp_value("test2", "ip1", "192")
    manager.set_esp_value("test2", "ip2", "168")
    manager.set_esp_value("test2", "ip3", "0")
    manager.set_esp_value("test2", "ip4", "146")

    print(f"ESP32 list: {manager.get_esp32_list()}")
    print(f"ESP32 json: {manager.get_esp32_json()}")


    valves = manager.get_valves_list()
    print(f"Valves list: {valves}")
    if len(valves) < 2:
        print("ERROR: valves not found")
        exit(1)


    print(f"Valves json: {manager.get_valves_json()}")
    print(f"Valve {valves[0]}: {manager.get_valve_json(valves[0])}")
    print(f"Valve {valves[1]}: {manager.get_valve_json(valves[1])}")

    print("")
    for v in valves:
        if v != "main":
            print(f"Testing {v} valve: {manager.test_valve(v, duration = 2) and 'OK' or 'FAIL'}")

    for v in valves:
        if v != "main":
            print(f"Testing water valve: {manager.water_valve(valves[1], duration = 2) and 'OK' or 'FAIL'}")

    print("Check there have been no errors.")
    print("Check that at least one valve was been tested and watered.")
    print("Done")
