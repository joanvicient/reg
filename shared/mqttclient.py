#!/usr/bin/env python3
import paho.mqtt.client as mqtt 
import time
import socket
import logging

logger = logging.getLogger(__name__)

#require:
# pip install paho-mqtt

class MqttClient:
 
    def on_connect(self, client, userdata, flags, return_code):
        if return_code == 0:
            logger.debug("(free thread)connected to mqtt broker at " + self.broker_hostname)
            self.client.subscribe("ID")
            self.client.subscribe("ID?")
            for topic in self.topicList:
                self.client.subscribe(topic)
        else:
            logger.debug("(free thread)could not connect, return code:", return_code)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        if msg.topic == "ID?":
            self.publishID()
        if msg.topic == "ID":
            id, hostname = str(msg.payload).split(':')
            if not id in self.servers:
                self.servers[id] = hostname
        elif msg.topic in self.topicList:
            self.topicCallback(msg.topic, str(msg.payload))
        else:
            logger.debug(msg.topic+" "+str(msg.payload))

    def loop_publish_id(self):
        self.publishID()
        newThread = threading.Timer(30, self.loop_publish_id)
        newThread.start()

    def __init__(self, id, topicList, topicCallback):
        self.broker_hostname = "nasf8b4c9"
        #self.broker_hostname = "localhost"
        self.port = 1883
        self.id = id
        self.servers = {}
        self.topicList = topicList
        self.topicCallback = topicCallback

        self.client = mqtt.Client(self.id)
        self.client.on_connect=self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_hostname, self.port)
        #self.client.loop_forever() #blocks execution
        self.client.loop_start() #creates new thread
        #self.loop_publish_id()
        self.publish("ID?", self.id)

    def stop(self):
        self.client.loop_stop()

    def publish(self, topic, message):
        try:
            result = self.client.publish(topic, message)
            status = result[0]
            if status == 0:
                logger.debug("Message "+ message + " is published to topic " + topic)
            else:
                logger.error("Failed to send message to topic " + topic)
        except:
            logger.error("Error publishing")
#        finally:
#            self.client.loop_stop()

    def publishID(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        fqdn = socket.getfqdn()
        self.publish("ID", self.id + ':' + hostname)

    def getServers(self):
        return self.servers
