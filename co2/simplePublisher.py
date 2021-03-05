import paho.mqtt.client as PahoMQTT
import time
import pandas as pd
import json

class MyPublisher:
	def __init__(self, clientID):
		self.clientID = clientID
		# create an instance of paho.mqtt.client
		self._paho_mqtt = PahoMQTT.Client(self.clientID, False) 
		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self.messageBroker = 'broker.emqx.io' #'localhost'

	def start (self):
		#manage connection to broker
		self._paho_mqtt.connect(self.messageBroker, 1883)
		self._paho_mqtt.loop_start()

	def stop (self):
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

	def myPublish(self, topic, message):
		# publish a message with a certain topic
		self._paho_mqtt.publish(topic, message, 2)

	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d (publisher)" % (self.messageBroker, rc))



if __name__ == "__main__":
	test = MyPublisher("MyPublisher")
	test.start()
	df=pd.read_csv('co2.csv',sep=',',decimal=',',index_col=0)
	df.index=pd.to_datetime(df.index,unit='s')
	#GATEWAY_NAME="VirtualBuilding"
	for i in df.index:
		for j in df.loc[i].items():
			#nodeID=j[0]
			value=j[1]
			#if nodeID=='Power':
				#measurement="Power"
			#else:
				#measurement="Temperature"
			payload={
						#"location":str(GATEWAY_NAME),
						"measurement":'co2',
						#"node":str(nodeID),
						"time_stamp":str(i),
						"value":value}
			test.myPublish('co2', json.dumps(payload))
			print('ho pubblicato')
			time.sleep(0.1)

	test.stop()


