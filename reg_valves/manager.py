#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Class to manage valves
from esp32 import Esp32
import time 
import logging
import threading

logger = logging.getLogger(__name__)

class ValvesManager:
    def __init__(self):
        self._esps = {}
        self._esps_lock = threading.Lock()

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
