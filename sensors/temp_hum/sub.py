import paho.mqtt.client as PahoMQTT
import time
import json

class MySubscriber:
		def __init__(self, clientID):
			self.clientID = clientID
			# create an instance of paho.mqtt.client
			self._paho_mqtt = PahoMQTT.Client(clientID, False)

			# register the callback
			self._paho_mqtt.on_connect = self.myOnConnect
			self._paho_mqtt.on_message = self.myOnMessageReceived
			self.topic = "breadType/"  #'measure/temperature'
			self.messageBroker = '127.0.0.1'


		def start (self):
			self._paho_mqtt.username_pw_set(username="brendan", password="pynini")

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
			print ("Connected to %s with result code: %d" % (self.messageBroker, rc))

		def myOnMessageReceived (self, paho_mqtt, userdata, msg):
			# A new message is received
			print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")
			try:
				data=json.loads(msg.payload)
				json_body = {
					"time": data['time_stamp'],
					"data_t_h":data['data_t_h']
					}
			except Exception as e:
				print(e)

if __name__ == "__main__":
	test = MySubscriber('pynini')
	test.start()
	while(True):
		pass