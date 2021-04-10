import paho.mqtt.client as PahoMQTT
import time
import json
import requests
from datetime import datetime
from telegramBot.sensors_db import SensorsDB
import Adafruit_DHT

global CATALOG_ADDRESS
global CATEGORY
CATALOG_ADDRESS = "http://localhost:9090" # deciso che sarà una variabile globale, accessibile da tutti gli script di tutto il progetto
CATEGORY = 'White'

class TemperatureHumiditySensor:
    def __init__(self, sensorID):
        self.sensorID = sensorID
        self._paho_mqtt = PahoMQTT.Client(sensorID, False)
        self.sensorIP = "192.168.1.2"
        self.sensorPort = 8080

        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        self.messageBroker = ""  # will get after post request where device registers
        self.topic_temp = ""  # will get after post request where device registers
        self.topic_hum = ""
        self.message = {
            'measurement': self.sensorID,
            'timestamp': '',
            'value': '',
        }

    def start(self):
        # manage connection to broker
        self._paho_mqtt.username_pw_set(username="brendan", password="pynini")
        self._paho_mqtt.connect(self.messageBroker, 1883)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic_temp)
        self._paho_mqtt.unsubscribe(self.topic_hum)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myPublish(self, topic, message):
        # publish a message with a certain topic
        self._paho_mqtt.publish(topic, message, 2)

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.messageBroker, rc))

    def registerDevice(self):
        sensor_dict = {}
        sensor_dict["ip"] = self.sensorIP
        sensor_dict["port"] = self.sensorPort
        sensor_dict["name"] = self.sensorID
        sensor_dict["last_seen"] = time.time()
        sensor_dict["dev_name"] = 'rpi'

        r = requests.post("http://localhost:9090/addSensor", json=sensor_dict)
<<<<<<< HEAD

        self.topic_temp = json.loads(r.text)['topic']['topic_temp']
        self.topic_hum = json.loads(r.text)['topic']['topic_hum']
=======
        dict_of_topics = json.loads(r.text)['topic']
        print("dict_of_topics",dict_of_topics)
        self.topic_temp = dict_of_topics["topic_temp"]
        self.topic_hum = dict_of_topics["topic_hum"]
>>>>>>> 2bd309b71d23a63f34604be878f0952b3fd597ba

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

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        print("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")
        try:
            data = json.loads(msg.payload)
            data["typology"] = CATEGORY
            if msg.topic == self.topic_temp:
                self.insertDataTemp(data)
            elif msg.topic == self.topic_hum:
                self.insertDataHum(data)

        except Exception as e:
            print(e)

    def insertDataTemp(self, data):
        '''
        :param data: dictionary whose keys represent the time, the value of the measurement and the type of bread
        :return: record these data in the table related to the sensor
        '''
        sql = "INSERT INTO temperature (TIMESTAMP, VALUE, TYPE) values (%s,%s,%s)"
        self.db.cursor.execute(sql, [data["timestamp"], data["value"], data["typology"]])
        self.db.db.commit()

    def insertDataHum(self, data):
        '''
        :param data: dictionary whose keys represent the time, the value of the measurement and the type of bread
        :return: record these data in the table related to the sensor
        '''
        sql = "INSERT INTO humidity (TIMESTAMP, VALUE, TYPE) values (%s,%s,%s)"
        self.db.cursor.execute(sql, [data["timestamp"], data["value"], data["typology"]])
        self.db.db.commit()


if __name__ == "__main__":

    dataDB = requests.get("http://localhost:9090/db")
    db = SensorsDB(json.loads(dataDB.text))
    db.start()
    db.db.commit()

    sensor = TemperatureHumiditySensor('TempHum', db)
    sensor.registerDevice()
    sensor.start()

    try:
        while True:
            # read temperature and humidity
            humidity, temperature = Adafruit_DHT.read_retry(11, 4)  # (sensor,pin)

            print('Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(temperature, humidity))

            payload_temp = {"measurement": "temperature", "timestamp": datetime.utcnow().isoformat(),
                            "value": temperature}
            payload_hum = {"measurement": "humidity", "timestamp": datetime.utcnow().isoformat(), "value": humidity}

            sensor.myPublish(sensor.topic_temp, json.dumps(payload_temp))
            sensor.myPublish(sensor.topic_hum, json.dumps(payload_hum))

            time.sleep(10)

    except KeyboardInterrupt:
        pass

    sensor.stop()
    sensor.removeDevice()
