import paho.mqtt.client as PahoMQTT
import json
import time
import requests
import pandas as pd


class Button():
    def __init__(self, sensor):
        # create an instance of pahqtt.client
        self.caseID, self.sensorID = sensor.split("-")
        self._paho_mqtt = PahoMQTT.Client(self.sensorID, False)

        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        #self._paho_mqtt.on_message = self.myOnMessageReceived
        self.messageBroker = "broker.emqx.io"
        self.topic = "breadType/"
        self.message = {'category': 'White'}


    def start(self):
        # manage connection to broker
        self._paho_mqtt.connect(self.messageBroker, 1883)
        self._paho_mqtt.loop_start()
        # subscribe for a topic
        self._paho_mqtt.subscribe(self.topic, 2)
        print("Subscribed to: ", self.topic)


    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()


    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.messageBroker, rc))


    def myPublish(self):
        # publish a message with a certain topic
        print("sto pubblicando sulla topica %s: ", self.topic, self.message)
        self._paho_mqtt.publish(self.topic, json.dumps(self.message), 2)


if __name__ == "__main__":
    categories = ["White", "Wheat", "Gluten-free", "Sales Statistics"]
    button = Button('CCC2-button')
    button.start()

for c in categories:
    button.message['category'] = c
    button.myPublish()
    time.sleep(20)

