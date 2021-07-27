import paho.mqtt.client as PahoMQTT
import json
import time
import requests
import pandas as pd
import sys
sys.path.append("../../")

from datetime import datetime
import os

class co2Sensor:
	def __init__(self, sensor, sensor_ip, sensor_port, catalog_ip, catalog_port):
		self.caseID, self.sensorID = sensor.split("-")
		self._paho_mqtt = PahoMQTT.Client(self.sensorID, False)
		
		self.sensorIP = sensor_ip
		self.sensorPort = sensor_port
		self.category = "White"
		self.breadCategories = []

		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived
		self.messageBroker = ""
		r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
		self.topic = self.caseID + "/" + json.loads(r.text)["co2"]
		self.topicBreadType = self.caseID + "/" + json.loads(r.text)["breadType"]
		self.message = {
			'measurement': self.sensorID,
			'caseID': self.caseID,
			'timestamp': '',
			'value': '',
			'unit_of_measurement' : "ppm",
			'category': self.category
		}

	def start (self):
		''' manage connection to broker
			subscription to the topic related to the bread category: if the user changes it through the button,
			the sensor will receive a message on that topic to update its data
		'''
		self._paho_mqtt.username_pw_set(username="brendan", password="pynini")
		self._paho_mqtt.connect(self.messageBroker, 1883)
		self._paho_mqtt.loop_start()
		# subscribe to a topic
		self._paho_mqtt.subscribe(self.topicBreadType, 2)
		print("Subscribed to: ", self.topicBreadType)

	def stop(self):
		self._paho_mqtt.unsubscribe(self.topic)
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d" % (self.messageBroker, rc))

	def myPublish(self, message):
		'''
			sensor publishes on its topic (caseID/measure/sensor) the measurements and write data into influxDB
		'''
		case_specific_topic = self.caseID + "/" +  self.topic # example CCC2/measure/co2
		self._paho_mqtt.publish(case_specific_topic, json.dumps(message), 2)
		
		


	def myOnMessageReceived (self, paho_mqtt , userdata, msg):
		'''
			when a message is received on the topic "topicBreadType", it means that the bread category of the case is changed:
			the sensor has to be aware of this change.
			(Each bread category has its own thresholds)
		'''
		print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")

		if msg.topic == self.topicBreadType:
			if json.loads(msg.payload)['bread_index'] != '':
				self.category = self.breadCategories[int(json.loads(msg.payload)['bread_index'])]
				


	def registerDevice(self):
		'''
			register the device on the Catalog by sending a post request to it
		'''
		sensor_dict = {}
		sensor_dict["sensorID"] = self.sensorID
		sensor_dict["caseID"] = self.caseID
		sensor_dict["ip"] = self.sensorIP
		sensor_dict["port"] = self.sensorPort
		sensor_dict["last_seen"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		sensor_dict["dev_name"] = 'rpi'

		print("sensor_dict", sensor_dict)

		r = requests.post(f"http://{catalog_ip}:{catalog_port}/addSensor", json=sensor_dict)
		dict_of_topics = json.loads(r.text)['topic']
		print("dict_of_topics",dict_of_topics)
		self.topic = json.loads(r.text)['topic']
		self.messageBroker = json.loads(r.text)['broker_ip_outside'] # outside since it is dockerized
		self.breadCategories = json.loads(r.text)['breadCategories']

		print("[{}] Device Registered on Catalog".format(
			int(time.time()),
		))

	def removeDevice(self):
		'''
			remove the sensor from the list of active sensors in the catalog
		'''

		sensor_dict = {}
		sensor_dict['sensorID'] = self.sensorID
		sensor_dict["caseID"] = self.caseID
		sensor_dict["ip"] = self.sensorIP
		sensor_dict["port"] = self.sensorPort
		sensor_dict["name"] = self.sensorID
		sensor_dict["dev_name"] = 'rpi'

		requests.post(f"http://{catalog_ip}:{catalog_port}/removeSensor", json=sensor_dict)
		print("[{}] Device Removed from Catalog".format(
			int(time.time()),
		))

if __name__ == "__main__":

	# read the configuration from the specific config file
	with open("config.json", 'r') as sensor_f:
		sensor_config = json.load(sensor_f)
		sensor_ip = sensor_config['sensor_ip']
		sensor_port = sensor_config['sensor_port']
		# sensor_caseID = sensor_config["caseID"] # or os.getenv("caseID")
		sensor_caseID = os.getenv("caseID")
		catalog_ip = sensor_config['catalog_ip']
		catalog_port = sensor_config['catalog_port']

	print(f"catalog ip {catalog_ip}, catalog port {catalog_port}")

	sensor = co2Sensor(sensor_caseID +'-'+ 'co2', sensor_ip, sensor_port, catalog_ip, catalog_port )
	
	# sensor registers itself to the catalog and starts publishing
	sensor.registerDevice()
	sensor.start()

	df = pd.read_csv('co2.csv', sep=',', decimal=',', index_col=0)
	try:
		for row in df.iterrows():
			value = row[0]
			sensor.message["measurement"] = sensor.sensorID
			sensor.message["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
			sensor.message["value"] = value
			sensor.message["category"] = sensor.category
			sensor.message["unit_of_measurement"] = "ppm"
			sensor.myPublish(sensor.message)
			print('ho pubblicato:', sensor.message)

			time.sleep(10)
	except KeyboardInterrupt:
		pass

	sensor.stop()
	sensor.removeDevice()
