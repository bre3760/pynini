import paho.mqtt.client as PahoMQTT
import time
import json
from ThingSpeak.sensors_db import SensorsDB

class MySubscriber:
		def __init__(self, clientID, db):
			self.clientID = clientID
			# create an instance of paho.mqtt.client
			self._paho_mqtt = PahoMQTT.Client(clientID, False)
			self.db = db

			# register the callback
			self._paho_mqtt.on_connect = self.myOnConnect
			self._paho_mqtt.on_message = self.myOnMessageReceived
			self.topic = 'co2'
			self.messageBroker = 'broker.emqx.io' #'localhost'
			#self.client = InfluxDBClient('localhost', 8086, 'root', 'root', clientID)
			#if {'name': clientID} not in self.client.get_list_database():
					#self.client.create_database(clientID)


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

		def myOnMessageReceived (self, paho_mqtt , userdata, msg):
			# A new message is received
			print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")
			try:
				data=json.loads(msg.payload)
				json_body = [
					{
					"measurement": data['measurement'],
					#"tags":
					#	{
						#"node": data['node'],
						#"location": data['location']
					#	},
					"time": data['time_stamp'],
					"fields":
						{
						"value":data['value']
						}
					}
				]
				self.insertData(json_body[0])
				#self.client.write_points(json_body,time_precision='s')
			except Exception as e:
				print (e)

		def insertData(self, data):
			print("SONO IN INSERT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
			print(data["time"], data["fields"]["value"])
			sql ="INSERT INTO CO2 (TIMESTAMP, VALUE) values (%s,%s)"
			self.db.cursor.execute(sql,[data["time"], data["fields"]["value"]])
			self.db.mydb.commit()

# mycursor.execute(sql)

if __name__ == "__main__":
	db = SensorsDB()
	db.start()
	test = MySubscriber('co2_sensor', db)
	test.start()
	while (True):
		pass