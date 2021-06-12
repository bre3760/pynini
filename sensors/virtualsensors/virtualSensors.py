import paho.mqtt.client as PahoMQTT
import json
import time
import requests
import pandas as pd
import sys
import os
sys.path.append("../../")
from database.influxDB import InfluxDB
from database.query import ClientQuery
from datetime import datetime

class co2Sensor:
	def __init__(self, sensor, influxDB, sensor_ip, sensor_port, catalog_ip, catalog_port):
		self.caseID = os.getenv("caseID")
		self.sensorID = os.getenv("sensorID")

		self._paho_mqtt = PahoMQTT.Client(self.sensorID, False)
		self.influxDB = influxDB
		self.sensorIP = sensor_ip
		self.sensorPort = sensor_port
		self.category = "White"
		self.breadCategories = []
		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived
		self.messageBroker = ""
		r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
		self.topic = ""
		self.topicBreadType = self.caseID + "/" + json.loads(r.text)["breadType"]
		self.message = {
			'measurement': self.sensorID,
			'caseID': self.caseID,
			'timestamp': '',
			'value': '',
			'category': self.category
		}

	def start (self):
		#manage connection to broker
		self._paho_mqtt.username_pw_set(username="brendan", password="pynini")
		self._paho_mqtt.connect(self.messageBroker, 1883)
		self._paho_mqtt.loop_start()
		# subscribe to a topic
		self._paho_mqtt.subscribe(self.topicBreadType, 2)
		print("Subscribed to: ", self.topicBreadType)

	def stop (self):
		self._paho_mqtt.unsubscribe(self.topic)
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d" % (self.messageBroker, rc))

	def myPublish(self, message):
		# publish a message with a certain topic
		case_specific_topic = self.caseID + "/" +  self.topic # example CCC2/measure/co2
		self._paho_mqtt.publish(case_specific_topic, json.dumps(message), 2)
		self.influxDB.write(message)
		print("su influx", message)
	#	self.influxDB.clean()

	def myOnMessageReceived (self, paho_mqtt , userdata, msg):
		# A new message is received
		print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")

		if msg.topic == self.topicBreadType:
			if json.loads(msg.payload)['bread_index'] != '':
				self.category = self.breadCategories[int(json.loads(msg.payload)['bread_index'])]
				print("bread_index",self.category)


	def registerDevice(self):
		'''
		register the device on the Room Catalog by sending a post request to it
		'''
		sensor_dict = {}
		sensor_dict["sensorID"] = self.sensorID
		sensor_dict["caseID"] = self.caseID
		sensor_dict["ip"] = self.sensorIP
		sensor_dict["port"] = self.sensorPort
		sensor_dict["last_seen"] = time.time()
		sensor_dict["dev_name"] = 'rpi'

		print("type sensor_dict", sensor_dict, type(sensor_dict))
		r = requests.post(f"http://{catalog_ip}:{catalog_port}/addSensor", json=sensor_dict)
		print("json.loads(r.text)", json.loads(r.text))
		self.topic = json.loads(r.text)['topic']
		self.messageBroker = json.loads(r.text)['broker_ip']
		self.breadCategories = json.loads(r.text)['breadCategories']

		print("[{}] Device Registered on Catalog".format(
			int(time.time()),
		))

	def removeDevice(self):

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







class TemperatureHumiditySensor:
	def __init__(self, sensor, influxDB, sensor_ip, sensor_port, catalog_ip, catalog_port):
		self.caseID = os.getenv("caseID")
		self.sensorID = os.getenv("sensorID")
		self._paho_mqtt = PahoMQTT.Client(self.sensorID, False)
		self.influxDB = influxDB
		self.sensorIP = sensor_ip
		self.sensorPort = sensor_port
		self.category = "White"
		self.breadCategories = []
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived
		self.messageBroker = ""
		r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
		self.topic_temp = ""
		self.topic_hum= ""
		self.topicBreadType = self.caseID + "/" +json.loads(r.text)["breadType"]
		self.message = {
			'measurement': self.sensorID,
			'caseID': self.caseID,
			'timestamp': '',
			'value': '',
			'category': self.category
		}
        

	def start(self):
		# manage connection to broker
		self._paho_mqtt.username_pw_set(username="brendan", password="pynini")
		self._paho_mqtt.connect(self.messageBroker, 1883)
		self._paho_mqtt.loop_start()
		self._paho_mqtt.subscribe(self.topicBreadType, 2)

	def stop(self):
		self._paho_mqtt.unsubscribe(self.topic_temp)
		self._paho_mqtt.unsubscribe(self.topic_hum)
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

	def myPublish(self, topic, message):
		# publish a message with a certain topic (measure/temperature or measure/humidity)
		case_specific_topic = self.caseID + "/" + topic # example CCC2/measure/co2
		self._paho_mqtt.publish(case_specific_topic, json.dumps(message), 2)
		self.influxDB.write(message)
		print("su influx", message)


	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
		print("Connected to %s with result code: %d" % (self.messageBroker, rc))

	def registerDevice(self):
		sensor_dict = {}
		sensor_dict["sensorID"] = self.sensorID
		sensor_dict["ip"] = self.sensorIP
		sensor_dict["port"] = self.sensorPort
		sensor_dict["caseID"] = self.caseID
		sensor_dict["name"] = self.sensorID
		sensor_dict["last_seen"] = time.time()
		sensor_dict["dev_name"] = 'rpi'

		r = requests.post(f"http://{catalog_ip}:{catalog_port}/addSensor", json=sensor_dict)
		dict_of_topics = json.loads(r.text)['topic']
		print("dict_of_topics",dict_of_topics)
		self.topic_temp = dict_of_topics["topic_temp"]
		self.topic_hum = dict_of_topics["topic_hum"]
		self.messageBroker = json.loads(r.text)['broker_ip']
		self.breadCategories = json.loads(r.text)["breadCategories"]
		print("[{}] Device Registered on Catalog".format(
			int(time.time()),
		))

	def removeDevice(self):
		sensor_dict = {}
		sensor_dict["ip"] = self.sensorIP
		sensor_dict["port"] = self.sensorPort
		sensor_dict["name"] = self.sensorID
		sensor_dict["dev_name"] = 'rpi'

		requests.post(f"http://{catalog_ip}:{catalog_port}/removeDevice", json=sensor_dict)
		print("[{}] Device Removed from Catalog".format(
			int(time.time()),
		))

	def myOnMessageReceived(self, paho_mqtt, userdata, msg):
		# A new message is received
		print("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")

		if msg.topic == self.topicBreadType:
			if json.loads(msg.payload)['bread_index'] != '':
				self.category = self.breadCategories[int(json.loads(msg.payload)['bread_index'])]
				print("bread_index", self.category)

if __name__ == "__main__":
	
	with open("config.json", 'r') as sensor_f:
		sensor_config = json.load(sensor_f)
		sensor_ip = sensor_config['sensor_ip']
		sensor_port = sensor_config['sensor_port']
		sensor_caseID = sensor_config["caseID"]
		catalog_ip = sensor_config['catalog_ip']
		catalog_port = sensor_config['catalog_port']

	dataInfluxDB = requests.get(f"http://{catalog_ip}:{catalog_port}/InfluxDB")
	influxDB = InfluxDB(json.loads(dataInfluxDB.text))

	Co2 = co2Sensor(sensor_caseID +'-'+ 'co2', influxDB, sensor_ip, sensor_port, catalog_ip, catalog_port )
	Co2.registerDevice()
	Co2.start()


	sensor = TemperatureHumiditySensor(sensor_caseID +'-'+  'TempHum', influxDB, sensor_ip, sensor_port, catalog_ip, catalog_port )
	sensor.registerDevice()
	sensor.start()

	df = pd.read_csv('co2.csv', sep=',', decimal=',', index_col=0)
	df.index = pd.to_datetime(df.index, unit='s')

	df_temphum = pd.read_csv('temphum.csv', sep=',', decimal=',', index_col=0)
	df_temphum.index = pd.to_datetime(df.index, unit='s')

	for i in df.index:
		for j in df.loc[i].items():
			value = j[1]
			Co2.message["measurement"] = Co2.sensorID
			Co2.message["timestamp"] = str(i)
			Co2.message["value"] = value
			Co2.message["category"] = Co2.category
			Co2.myPublish(Co2.message)
			print('ho pubblicato:', Co2.message)

			time.sleep(10)

	Co2.stop()
	Co2.removeDevice()

	c = ClientQuery(Co2.sensorID, Co2.category, Co2.caseID)
	c.start()
