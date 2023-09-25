#!/usr/bin/env python3
import paho.mqtt.client as mqtt 
import time
import socket

#require:
# pip install paho-mqtt

class MqttClient:
 
    def on_connect(self, client, userdata, flags, return_code):
        if return_code == 0:
            print("connected")
        else:
            print("could not connect, return code:", return_code)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))
        print(client)
        print(userdata)
        print(msg)

    def __init__(self, id):
        self.broker_hostname = "nasf8b4c9"
        #self.broker_hostname = "localhost"
        self.port = 1883
        self.id = id

        self.client = mqtt.Client(self.id)
        self.client.on_connect=self.on_connect
        self.client.on_message = self.on_message
        self.client.subscribe(self.id)
        self.client.connect(self.broker_hostname, self.port)
        #self.client.loop_forever() #blocks execution
        self.client.loop_start() #creates new thread
        while True:
            self.publishID()
            time.sleep(10)

        self.client.loop_stop()

    def publish(self, topic, message):
        try:
            result = self.client.publish(topic, message)
            status = result[0]
            if status == 0:
                print("Message "+ message + " is published to topic " + topic)
            else:
                print("Failed to send message to topic " + topic)
        except:
            print("Error publishing")
#        finally:
#            self.client.loop_stop()

    def publishID(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        fqdn = socket.getfqdn()
        #print("Publishing ip: " + ip_address + " of server: " + hostname + ". fqdn: " + fqdn)
        self.publish("ID", self.id + ':' + hostname)
