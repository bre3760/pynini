import paho.mqtt.client as PahoMQTT
import json
import time
import requests
import pandas as pd
from telegramBot.sensors_db import SensorsDB

global CATALOG_ADDRESS
global CATEGORY
CATALOG_ADDRESS = "http://localhost:9090" # deciso che sarà una variabile globale, accessibile da tutti gli script di tutto il progetto
CATEGORY = 'White'

class co2Sensor:
	def __init__(self, sensorID, db):
		# create an instance of paho.mqtt.client
		self.sensorID =  sensorID
		self._paho_mqtt = PahoMQTT.Client(sensorID, False)
		self.db = db
		self.sensorIP =  "172.20.10.10"
		self.sensorPort = 8080
		self.caseID = "CCC2"

		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived
		self.messageBroker = ""
		self.topic = ""
		self.message = {
			'measurement': self.sensorID,
			'timestamp': '',
			'value': '',
		}
		#self.sensorPort = self.catalogPort

		# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# s.connect(("8.8.8.8", 80))
		# self.address = s.getsockname()[0]


	def start (self):
		#manage connection to broker
		self._paho_mqtt.connect(self.messageBroker, 1883)
		self._paho_mqtt.loop_start()
		# subscribe for a topic
		# self._paho_mqtt.subscribe(self.topic, 2)

	def stop (self):
		self._paho_mqtt.unsubscribe(self.topic)
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d (subscriber)" % (self.messageBroker, rc))

	def myPublish(self, topic, message):
		# publish a message with a certain topic
		self._paho_mqtt.publish(topic, message, 2)

	def myOnMessageReceived (self, paho_mqtt , userdata, msg):
		# A new message is received
		print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")
		try:
			data=json.loads(msg.payload)
			data["typology"] = CATEGORY
			self.insertData(data)

		except Exception as e:
			print (e)

	def insertData(self, data):
		'''
		:param data: dictionary whose keys represent the time, the value of the measurement and the type of bread
		:return: record these data in the table related to the sensor
		'''
		sql ="INSERT INTO co2 (TIMESTAMP, VALUE, TYPE) values (%s,%s,%s)"
		self.db.cursor.execute(sql,[data["timestamp"], data["value"], data["typology"]])
		self.db.db.commit()

	def registerDevice(self):
		'''
		register the device on the Room Catalog by sending a post request to it
		'''
		sensor_dict = {}
		sensor_dict["case_ID"] = self.caseID
		sensor_dict["ip"] = self.sensorIP
		sensor_dict["port"] = self.sensorPort
		sensor_dict["name"] = self.sensorID
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
		sensor_dict["ip"] = self.sensorIP
		sensor_dict["port"] = self.sensorPort
		sensor_dict["name"] = self.sensorID
		sensor_dict["dev_name"] = 'rpi'

		requests.post("http://localhost:9090/removeDevice", json=sensor_dict)
		print("[{}] Device Removed from Catalog".format(
			int(time.time()),
		))

if __name__ == "__main__":

	dataDB = requests.get("http://localhost:9090/db")
	db = SensorsDB(json.loads(dataDB.text))
	db.start()

	sensor = co2Sensor('co2', db)
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
			sensor.myPublish(sensor.topic, json.dumps(sensor.message))
			print('ho pubblicato')
			time.sleep(10)

	sensor.stop()
	sensor.removeDevice()
