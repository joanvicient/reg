#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging
import requests
import threading

from valve import Valve

logger = logging.getLogger(__name__)

MIN_VALVE_FETCH_SECONDS = 60

class Esp32:
    def __init__(self, name):
        self.name = name

        self.status = 'OFF'
        self.ip1 = None
        self.ip2 = None
        self.ip3 = None
        self.ip4 = None
        self.uptime = None
        self.rssi = None

        self.valves_fetched = datetime.now() - timedelta(seconds=MIN_VALVE_FETCH_SECONDS+1)
        self.valves = {}
        self.valves_lock = threading.Lock()
        logger.debug(f"ESP32 {self.name} created")

################## public methods for esp ##################

    def get_ip(self) -> str | None:
        if not all([self.ip1, self.ip2, self.ip3, self.ip4]):
            logger.debug(f"ESP32 {self.name} IP not set yet")
            return None
        
        logger.debug(f"ESP32 {self.name} IP: {self.ip1}.{self.ip2}.{self.ip3}.{self.ip4}")
        return f"{self.ip1}.{self.ip2}.{self.ip3}.{self.ip4}"

    def set_value(self, key: str, value: str):
        logger.debug(f"Setting {key} to {value}")
        if key == "status":
            self._set_status(value)
            return True
        elif key == "ip1":
            self.ip1 = value
        elif key == "ip2":
            self.ip2 = value
        elif key == "ip3":
            self.ip3 = value
        elif key == "ip4":
            self.ip4 = value
        elif key == "uptime":
            self.uptime = value
        elif key == "rssi":
            self.rssi = value
        elif key == "none":
            # nothing to do
            return True
        else:
            logger.error(f"Invalid key: {key} from {self.name}")
            return False
        
        return self._fetch_valves()
    
    def get_json(self) -> dict:
        return {
            "name": self.name,
            "ip": self.get_ip(),
            "status": self.status,
            "uptime": self.uptime,
            "rssi": self.rssi,
            "valves": self.get_valves()
        }

################## public methods for valves ##################

    def get_valves_json(self) -> dict:
        logger.debug(f"Getting valves for ESP32 {self.name}")
        with self.valves_lock:
            valves = {}
            for name, valve in self.valves.items():
                valves[name] = valve.get_json()
            return valves

    def get_valve_json(self, name: str) -> dict:
        logger.debug(f"Getting valve {name} for ESP32 {self.name}")
        with self.valves_lock:
            if not name in self.valves:
                logger.error(f"Valve {name} not found")
                return {}
            
            return self.valves[name].get_json()

    def get_valves(self) -> list[str]:
        logger.debug(f"Getting valves for ESP32 {self.name}")
        with self.valves_lock:
            return list(self.valves.keys())

    def open_valve(self, name: str) -> bool:
        logger.debug(f"Opening valve {name} on ESP32 {self.name}")
        with self.valves_lock:
            if not name in self.valves:
                logger.error(f"Valve {name} not found")
                return False

            return self.valves[name].activate()
        
    def close_valve(self, name: str) -> bool:
        logger.debug(f"Closing valve {name} on ESP32 {self.name}")
        with self.valves_lock:
            if not name in self.valves:
                logger.error(f"Valve {name} not found")
                return False

            return self.valves[name].deactivate()

    def get_valve_status(self, name: str) -> bool | None:
        logger.debug(f"Getting valve status {name} on ESP32 {self.name}")
        with self.valves_lock:
            if not name in self.valves:
                logger.error(f"Valve {name} not found")
                return None

            return self.valves[name].get_status()

################## private methods for esp ##################

    def _set_status(self, status: str) -> None:
        self.status = status
        if status == "OFF":
            logger.debug("Removing valves and enabling fetch")
            self.valves_fetched = datetime.now() - timedelta(seconds=MIN_VALVE_FETCH_SECONDS+1)
            with self.valves_lock:
                self.valves = {}

    def _fetch_valves(self) -> None:
        ip = self.get_ip()
        if not ip:
            #logger.debug(f"ESP32 IP not set yet for {self.name}")
            return False

        is_expired = datetime.now() - self.valves_fetched > timedelta(seconds=MIN_VALVE_FETCH_SECONDS)
        if not is_expired:
            logger.debug(f"ESP32 {self.name} checked recently")
            return True
        else:
            self.valves_fetched = datetime.now()

        #https://codebeautify.org/jsonviewer
        url = "http://" + ip + "/json"
        try:
            r = requests.get(url)
            if r.status_code == requests.codes.ok:
                data = r.json()
                sensors = data["Sensors"]
                for sensor in sensors:
                    taskName = str(sensor['TaskName'])
                    taskType = sensor['Type']
                    if not taskType == 'Switch input - Switch':
                        logger.debug(f'skipping "{taskName}" sensor in {ip}')
                        continue

                    gpio = str(sensor["TaskValues"][0]["Name"])
                    value = str(sensor["TaskValues"][0]["Value"])

                    if gpio.isdigit():
                        logger.debug(f'{taskName} at {ip}, gpio {gpio}: {value}')
                        valve = Valve(taskName, ip, gpio, self.name, int(value))
                        self._add_or_update_valve(valve)
                    else:
                        logger.info(f'Missconfigured {taskName} at {ip}')
            else:
                logger.error('exception on GET ' + url + ": " + r.reason + " (" + str(r.status_code) + ")")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed to {url}: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to {url}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed to {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching valves from {url}: {e}")

    def _add_or_update_valve(self, valve: Valve) -> bool:
        with self.valves_lock:
            if not valve.name in self.valves:
                self.valves[valve.name] = valve
                logger.info(f"Added {valve.name} in {self.name}")
            else:
                logger.debug(f"Valve {valve.name} in {self.name} already exists, updating not implemented yet")
        
        return True

#################### testing #########################

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    esp = Esp32("test")

    esp.set_value("status", "ON")
    esp.set_value("uptime", "aaaaaa")
    esp.set_value("rssi", "-124")

    if esp.get_ip() != None:
        print("ERROR: ESP32 IP should not be set yet")
        exit(1)

    esp.set_value("ip1", "192")
    esp.set_value("ip2", "168")
    esp.set_value("ip3", "0")

    if esp.get_ip() != None:
        print("ERROR: ESP32 IP should not be set yet")
        exit(1)

    esp.set_value("ip4", "146")

    if esp.get_ip() == None:
        print("ERROR: ESP32 IP should be set now")
        exit(1)

    print("Testing valve detection")
    valves = esp.get_valves()
    print("valves: ", valves)

    if len(valves) == 0:
        print("ERROR: ESP32 should have at least one valve")
        exit(1)

    v = valves[0]

    print("Printing esp json")
    print(esp.get_json())
    print()

    print(f"Printing valve {v} json")
    print(esp.get_valve_json(v))
    print()

    print("Testing valve open command")
    esp.open_valve(v)
    status = esp.get_valve_status(v)
    print(f"Valve {v} status: {status}")
    if status != True:
        print("ERROR: Valve should be open")
        exit(1)

    print("Testing valve close command")
    esp.close_valve(v)
    status = esp.get_valve_status(v)
    print(f"Valve {v} status: {status}")
    if status != False:
        print("ERROR: Valve should be closed")
        exit(1)

    print("Testing valve removal")
    esp.set_value("status", "OFF")
    valves = esp.get_valves()
    if len(valves) != 0:
        print("ERROR: Valve should be removed")
        exit(1)
    
    print("Test finished OK")
