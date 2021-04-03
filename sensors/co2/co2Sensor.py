import paho.mqtt.client as PahoMQTT
import json
import time
import requests
import pandas as pd
from telegramBot.sensors_db import SensorsDB

global CATALOG_ADDRESS
CATALOG_ADDRESS = "http://localhost:9090" # "172.20.10.11"

class co2Sensor:
		def __init__(self, clientID, db):
			self.clientID = clientID
			# create an instance of paho.mqtt.client
			self._paho_mqtt = PahoMQTT.Client(clientID, False)
			self.db = db
			# register the callback
			self._paho_mqtt.on_connect = self.myOnConnect
			self._paho_mqtt.on_message = self.myOnMessageReceived

			#config_dict = json.load(open("configFile.json"))
			self.topic = ""
			self.sensorID = "co2"
			#self.messageBroker = config_dict.get("messageBroker")
			self.message = {
				'measurement': self.sensorID,
				'timestamp': '',
				'value': '',
			}
			self.sensorIP = CATALOG_ADDRESS
			#self.sensorPort = self.catalogPort

			# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			# s.connect(("8.8.8.8", 80))
			# self.address = s.getsockname()[0]


		def start (self):
			#manage connection to broker
			self._paho_mqtt.connect(self.messageBroker, 1883)
			self._paho_mqtt.loop_start()
			# subscribe for a topic
			self._paho_mqtt.subscribe(self.topic, 2)

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
				json_body = [
					{
					"measurement": data['measurement'],
					"time": data['time_stamp'],
					"value": data['value'],
					"typology": 'Standard'
					}
				]
				self.insertData(json_body[0])
				#self.client.write_points(json_body,time_precision='s')
			except Exception as e:
				print (e)

		def insertData(self, data):
			print("SONO IN INSERT!")
			print(data["time"], data["value"], data["type"])
			sql ="INSERT INTO CO2 (TIMESTAMP, VALUE, TYPE) values (%s,%s,%s)"
			self.db.cursor.execute(sql,[data["time"], data["value"], data["type"]])
			self.db.mydb.commit()

		def registerDevice(self):
			"""
			register the device on the Room Catalog by sending a post request to it.
			"""
			sensor_dict = {}
			sensor_dict["ip"] = self.sensorIP
			#sensor_dict["port"] = self.sensorPort
			sensor_dict["name"] = self.sensorID
			sensor_dict["last_seen"] = time.time()
			sensor_dict["dev_name"] = 'rpi'

			r = requests.post("http://localhost:9090/addDevice", json=sensor_dict)
			print("r",  json.loads(r.text)['topic'])
			self.topic = json.loads(r.text)['topic']
			self.messageBroker = json.loads(r.text)['broker_ip']

			print("[{}] Device Registered on Catalog".format(
				int(time.time()),
			))

# mycursor.execute(sql)

if __name__ == "__main__":

	# la prima volta il catalog deve essere letto come json per ricavare il suo indirizzo, no?
	# catalog = requests.get(CATALOG_ADDRESS).json()
	#broker_port = catalogue["port"]

	with open('../../catalog/catalog.json', 'r') as f:
		catalog_dict = json.load(f)
		#local_topic = catalog_dict['network_name'] + '/' + catalog_dict['room_name']
		# ip = catalog_dict["ip_address"]
		# port = catalog_dict["catalog_port"]
		# print("catalog_dict", catalog_dict)

	db = SensorsDB()
	db.start()

	sensor = co2Sensor('co2_sensor', db)
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