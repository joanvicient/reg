#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import socket
from mqttclient import MqttClient

logger = logging.getLogger(__name__)

class MqttDiscoverer:
    def __init__(self, manager):
        self.manager = manager

        id = self._generate_id()
        self.mqtt = MqttClient(id, ['esp/#'], self._on_mqtt_callback)
        logger.info("MQTT client init successful")

    def _generate_id(self) -> str:
        hostname = socket.gethostname()
        return f"reg/valves_at_{hostname}"

    def _on_mqtt_callback(self, topic: str, payload: str):
        logger.debug('MQTT: ' + topic + ", with body: " + payload)
        if (topic[0:4] == 'esp/'):
            topic_list = str(topic).split('/')
            if len(topic_list) == 2:
                # a esp is online or offline
                # topic: esp/<espX>
                # payload: ON or OFF
                name = topic_list[1]
                status = payload
                self.manager.set_esp_value(name, "status", status)

            elif len(topic_list) == 3:
                # a valve value has changed
                # topic: esp/<espX>/status
                # topic: esp/<espX>/<planta>/<gpio>
                # payload: <value>
                if topic_list[2] == 'status':
                    # TODO: can return an error!!!!!!!
                    # update_valve_status(topic_list[1], payload)
                    logger.debug('Not using MQTT: ' + topic + ", with body: " + payload)
                else:
                    logger.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")

            elif len(topic_list) == 4:
                # an esp statistic has been reported
                # topic: esp/<espX>/ip or esp/<espX>/info
                name = topic_list[1]
                key = topic_list[3]
                value = payload
                self.manager.set_esp_value(name, key, value)

            else:
                logger.error('MQTT: ' + topic + ", with body: " + payload + " NOT understood")

        else:
            logger.error('uncached topic: ' + topic + ' - ' + payload)

if __name__ == "__main__":
    import time
    class FakeManager:
        def set_esp_value(self, name: str, key: str, value: str) -> bool:
            print(f"Setting ESP {name} value {key} to {value}")
            return True

    mqtt_discoverer = MqttDiscoverer(FakeManager())
    time.sleep(20)
    print("Done, a few messages should have been written")
