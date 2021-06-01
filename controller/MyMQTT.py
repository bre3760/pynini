import paho.mqtt.client as PahoMQTT
from time import time, sleep

class MyMQTT:
	def __init__(self, clientID, broker, port, notifier):
		self.broker = broker
		self.port = port
		self.notifier = notifier
		self.clientID = clientID
		self._isSubscriber = False
		self._topic = []
		# print(self.topic)
		# create an instance of paho.mqtt.client
		self._paho_mqtt = PahoMQTT.Client(clientID, False)
		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived

	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d" % (self.broker, rc))

	def myOnMessageReceived (self, paho_mqtt, userdata, msg):
		print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")
		if msg.topic == "breadType/":
			print(f'breadType chosen!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! {msg.payload}')
		self.notifier.notify(msg.topic, str(msg.payload))

	def myPublish (self, topic, msg):
		print ("publishing '%s' with topic '%s'" % (msg, topic))
		self._paho_mqtt.publish(topic, msg, 2)
		
	def mySubscribe (self, topic):
		print ("subscribing to %s" % (topic))
		self._paho_mqtt.subscribe(topic, 2)
		self._isSubscriber = True
		self._topic = topic

	def start(self):
		# manage connection to broker
		self._paho_mqtt.username_pw_set(username="brendan", password="pynini")

		self._paho_mqtt.connect(self.broker , self.port)
		self._paho_mqtt.loop_start()

	def stop (self):
		if (self._isSubscriber):
			# remember to unsuscribe if it is working also as subscriber
			self._paho_mqtt.unsubscribe(self._topic)

		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()


