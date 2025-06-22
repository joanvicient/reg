#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import logging
import json
import os

logger = logging.getLogger(__name__)

#require:
# pip install paho-mqtt

class MqttClient:
 
    def on_connect(self, client, userdata, flags, return_code):
        if return_code == 0:
            logger.debug("(free thread)connected to mqtt broker at " + self.broker_hostname)
        else:
            logger.debug("(free thread)could not connect, return code:", return_code)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        logger.debug(msg.topic+" "+str(msg.payload))
        self.topicCallback(msg.topic, msg.payload.decode("utf-8", "strict"))

    def __init__(self, id, topicList, topicCallback):
        self.broker_hostname = "192.168.1.10"
        self.port = 1883
        self.id = id
        self.topicList = topicList
        self.topicCallback = topicCallback

        #get mqtt broker hostname from env
        if 'MQTT_BROKER_HOST' in os.environ:
            self.broker_hostname = os.environ['MQTT_BROKER_HOST']
            logger.debug("MQTT_BROKER_HOST set to " + self.broker_hostname)
        if 'MQTT_BROKER_PORT' in os.environ:
            self.port = int(os.environ['MQTT_BROKER_PORT'])
            logger.debug("MQTT_BROKER_PORT set to " + str(self.port))

        self.client = mqtt.Client(self.id)
        self.client.on_connect=self.on_connect
        self.client.on_message = self.on_message
        self.client.will_set("reg/"+self.id, payload="OFF", qos=0, retain=True)
        self.client.connect(self.broker_hostname, self.port)
        #self.client.loop_forever() #blocks execution
        self.client.loop_start() #creates new thread
        #self.loop_publish_id()
        for topic in topicList:
            self.client.subscribe(topic)

        self.client.publish("reg/"+self.id,payload="ON", qos=0, retain=True)

    def stop(self):
        self.client.loop_stop()

    def publish(self, topic, message, retain = False):
        try:
            if type(message) == dict:
                message = json.dumps(message)

            result = self.client.publish(topic, message, retain=retain)
            status = result[0]
            if status == 0:
                logger.debug("Message "+ message + " is published to topic " + topic)
            else:
                logger.error("Failed to send message to topic " + topic)
        except OSError:
        #except Exception. as e:
            logger.error("Error publishing")
#        finally:
#            self.client.loop_stop()
