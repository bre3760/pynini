import paho.mqtt.client as PahoMQTT
import time
import json
from datetime import datetime
import Adafruit_DHT

class MyPublisher:
	def __init__(self, clientID):
		self.clientID = clientID
		# create an instance of paho.mqtt.client
		self._paho_mqtt = PahoMQTT.Client(self.clientID, False)
		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self.messageBroker = 'localhost'

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
		print ("Connected to %s with result code: %d" % (self.messageBroker, rc))





pub = MyPublisher("MyPublisher")
pub.start()

sensor_data = {'temperature': 0, 'humidity': 0}

try:
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(11, 4) #(sensor,pin)

        print('Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(temperature, humidity))

        sensor_data['temperature'] = temperature
        sensor_data['humidity'] = humidity
        payload={"time_stamp":datetime.utcnow().isoformat(),"data_t_h":sensor_data}
        print(payload)
        pub.myPublish('pynini/temperature_humidity', json.dumps(payload))
       
        time.sleep(1)
        
except KeyboardInterrupt:
    pass
        
pub.stop()
