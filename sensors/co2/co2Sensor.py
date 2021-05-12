import paho.mqtt.client as PahoMQTT
import json
import time
import requests
import pandas as pd
from database.influxDB import InfluxDB
from database.query import ClientQuery

# sensore pubblica su topi ca measurement/co2 e si sottoscrive alla topica breadType in cui il bottone pubblica il cambiamento di categoria
# di default il sensore suppone di essere nella teca White

# NOOOOOOOOOOOOO: ogni componente ha il proprio config da cui prende ip e porta
# global CATALOG_ADDRESS
# CATALOG_ADDRESS = "http://localhost:9090" # deciso che sarà una variabile globale, accessibile da tutti gli script di tutto il progetto

class co2Sensor:
	def __init__(self, sensor, influxDB):
		# create an instance of pahqtt.client
		self.caseID, self.sensorID = sensor.split("-")
		self._paho_mqtt = PahoMQTT.Client(self.sensorID, False)
		self.influxDB = influxDB
		self.sensorIP =  "172.20.10.08"
		self.sensorPort = 8080
		self.category = "White"

		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived
		self.messageBroker = ""
		r = requests.get("http://localhost:9090/topics")
		self.topic = ""
		self.topicBreadType = json.loads(r.text)["breadType"]
		self.message = {
			'measurement': self.sensorID,
			'caseID': self.caseID,
			'timestamp': '',
			'value': '',
			'category': self.category
		}

	def start (self):
		#manage connection to broker
		self._paho_mqtt.connect(self.messageBroker, 1883)
		self._paho_mqtt.loop_start()
		# subscribe for a topic
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
		self._paho_mqtt.publish(self.topic, json.dumps(message), 2)
		self.influxDB.write(message)
		print("su influx", message)
	#	self.influxDB.clean()

	def myOnMessageReceived (self, paho_mqtt , userdata, msg):
		# A new message is received
		print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")

		if msg.topic == self.topicBreadType:
			self.category = json.loads(msg.payload)['category']
			print("category",self.category)

		try:
			data=json.loads(msg.payload)
			print("INFLUXDB", self.message)

		except Exception as e:
			print(e)

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

		r = requests.post("http://localhost:9090/addSensor", json=sensor_dict)
		print("json.loads(r.text)", json.loads(r.text))
		self.topic = json.loads(r.text)['topic']
		self.messageBroker = json.loads(r.text)['broker_ip']

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

		requests.post("http://localhost:9090/removeSensor", json=sensor_dict)
		print("[{}] Device Removed from Catalog".format(
			int(time.time()),
		))

if __name__ == "__main__":

	with open("config.json", 'r') as f:
		config = json.load(f)
	ip = config['ip']
	port = config['port']

	dataInfluxDB = requests.get(f"http://{ip}:{port}/InfluxDB")
	influxDB = InfluxDB(json.loads(dataInfluxDB.text))

	sensor = co2Sensor('CCC2-co2', influxDB)
	sensor.registerDevice()
	sensor.start()

	df = pd.read_csv('co2.csv', sep=',', decimal=',', index_col=0)
	df.index = pd.to_datetime(df.index, unit='s')
	for i in df.index:
		for j in df.loc[i].items():
			value = j[1]
			sensor.message["measurement"] = sensor.sensorID
			sensor.message["timestamp"]	= str(i)
			sensor.message["value"]	= value
			sensor.message["category"] = sensor.category
			sensor.myPublish(sensor.message)
			print('ho pubblicato:', sensor.message)
			
			time.sleep(10)

	sensor.stop()
	sensor.removeDevice()

	c = ClientQuery(sensor.sensorID, sensor.category, sensor.caseID)
	c.start()
