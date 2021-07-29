import paho.mqtt.client as PahoMQTT
import json
import time
import requests
import pandas as pd
import sys
sys.path.append("../../")
from datetime import datetime

class co2Sensor:
	"""
	The flow is the following:
	On boot the sensor reads its config file with catalog and self information
	Sensor class is then instantiated with the appropriate variables 
	init function creates the mqtt client
	a get request is made to the catalog api in order to retrieve the topics for the sensor.

	The registerdevice function of the sensor class is called, which sends two post requests:
	- the first to the catalog api in order to register the new sensor 
	- the second to the db api that allows the db mqtt client to know to which topics to subscribe to.
	"""



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
		#get broker info from catalog
		bIp = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_ip_outside")  #outside se no rasp
		bPort = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_port")
		self.messageBroker = json.loads(bIp.text)
		self.broker_port = json.loads(bPort.text)
		#get topics from catalog
		r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
		print("response from topics request", r.text)
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
		# self._paho_mqtt.unsubscribe(self.topic) #????
		self._paho_mqtt.unsubscribe(self.topicBreadType)
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d" % (self.messageBroker, rc))

	def myPublish(self, message):
		'''
			sensor publishes on its topic (caseID/measure/sensor) the measurements
		'''
		case_specific_topic = self.caseID + "/" +  self.topic # example CCC2/measure/co2
		print(f"Publishing on topic {case_specific_topic}")
		self._paho_mqtt.publish(case_specific_topic, json.dumps(message), 2)


	def myOnMessageReceived (self, paho_mqtt , userdata, msg):
		'''
			when a message is received on the topic "topicBreadType", it means that the bread category of the case is changed:
			the sensor has to be aware of this change
			(Each bread category has its own thresholds)
		'''
		print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")

		if msg.topic == self.topicBreadType:
			if json.loads(msg.payload)['bread_index'] != '':
				self.category = self.breadCategories[int(json.loads(msg.payload)['bread_index'])]
				print("bread_index",self.category)


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

		print("sensor_dict in registerDevice", sensor_dict)

		# send a post to the catalog to register the sensor
		r = requests.post(f"http://{catalog_ip}:{catalog_port}/addSensor", json=sensor_dict)

		print("R.text: ",  json.loads(r.text))

		dict_of_topics = json.loads(r.text)['topic']
		print("dict_of_topics",dict_of_topics)

		self.topic = json.loads(r.text)['topic']

		self.messageBroker = json.loads(r.text)['broker_ip_outside']
		self.breadCategories = json.loads(r.text)['breadCategories']


		# sencond post to db api to inform of new sensor added 
		# post al catalog per avere ip e porta del db 
		# getting useful information in order to contact db api
		influx_data = requests.get(f"http://{catalog_ip}:{catalog_port}/InfluxDB")
		print(f"Influx data response from catalog api, {influx_data.text}")
		# post al db per dire che si è connesso il sensore,
		# mandando topica in cui pubblica così che il servizio mqtt del db possa iscriversi
		influx_api_ip = json.loads(influx_data.text)["api_ip"]
		influx_api_port = json.loads(influx_data.text)["api_port"]
		print(f"Influx db api ip and port {influx_api_ip} {influx_api_port}")

		#Appendo la topica a topics
		sensor_dict["topics"] = [self.caseID + "/" + self.topic]
		print("sensor dict before db post request", sensor_dict)
		#sensor_dic viene mandato a db adaptor a cui si sottoscrive 
		try:
			r = requests.post(f"http://{influx_api_ip}:{influx_api_port}/db/addSensor", json=sensor_dict)

			print(f"Response (r) from post to db api {r}")
		except:
			print(f"DB is probably off, sorry, the topics of this sensor will be retireved \
					automatically when the DB is turned on")
			
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
		
		####post to remove from database
		influx_data = requests.get(f"http://{catalog_ip}:{catalog_port}/InfluxDB")
		print(f"Influx data response from catalog api, {influx_data.text}")
		# post al db per dire che si è connesso il sensore,
		# mandando topica in cui pubblica così che il servizio mqtt del db possa iscriversi
		influx_api_ip = json.loads(influx_data.text)["api_ip"]
		influx_api_port = json.loads(influx_data.text)["api_port"]
		print(f"Influx db api ip and port {influx_api_ip} {influx_api_port}")

		#Appendo la topica a topics
		sensor_dict["topics"] = [self.caseID + "/" + self.topic]
		print("sensor dict before db post request", sensor_dict)
		#sensor_dic viene mandato a db adaptor a cui si sottoscrive 
		r = requests.post(f"http://{influx_api_ip}:{influx_api_port}/db/removeSensor", json=sensor_dict)
		
		removalTime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		print( f"Device Removed on Catalog {removalTime}")

if __name__ == "__main__":

	# read the configuration from the specific config file
	with open("config.json", 'r') as sensor_f:
		sensor_config = json.load(sensor_f)
		sensor_ip = sensor_config['sensor_ip']
		sensor_port = sensor_config['sensor_port']
		sensor_caseID = sensor_config["caseID"]
		catalog_ip = sensor_config['catalog_ip']
		catalog_port = sensor_config['catalog_port']

	print(f"catalog ip {catalog_ip}, catalog port {catalog_port}")

	sensor = co2Sensor(sensor_caseID +'-'+ 'co2', sensor_ip, sensor_port, catalog_ip, catalog_port)
	
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

			time.sleep(15)
	except KeyboardInterrupt:
		pass

	sensor.stop()
	sensor.removeDevice()

