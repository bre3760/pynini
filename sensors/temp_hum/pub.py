import paho.mqtt.client as PahoMQTT
import time
import json
import requests
from datetime import datetime
import Adafruit_DHT
import sys
sys.path.append("../../")
from database.influxDB import InfluxDB
from database.query import ClientQuery


class TemperatureHumiditySensor:
    def __init__(self, sensor, influxDB, sensor_ip, sensor_port, catalog_ip, catalog_port):
        self.caseID, self.sensorID = sensor.split("-")
        self._paho_mqtt = PahoMQTT.Client(self.sensorID, False)
        self.influxDB = influxDB
        self.sensorIP = sensor_ip
        self.sensorPort = sensor_port
        self.category = "White"

        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        self.messageBroker = ""
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
        self.topic_temp = ""
        self.topic_hum= ""
        self.topicBreadType = json.loads(r.text)["breadType"]
        self.message = {
            'measurement': self.sensorID,
            'caseID': self.caseID,
            'timestamp': '',
            'value': '',
            'category': self.category
        }
        

    def start(self):
        # manage connection to broker
        self._paho_mqtt.username_pw_set(username="brendan", password="pynini")
        self._paho_mqtt.connect(self.messageBroker, 1883)
        self._paho_mqtt.loop_start()
        self._paho_mqtt.subscribe(self.topicBreadType, 2)

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic_temp)
        self._paho_mqtt.unsubscribe(self.topic_hum)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myPublish(self, topic, message):
        # publish a message with a certain topic
        print("message json.dumps to publish in myPublish", json.dumps(message))
        self._paho_mqtt.publish(topic, json.dumps(message), 2)
        self.influxDB.write(message)

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.messageBroker, rc))

    def registerDevice(self):
        sensor_dict = {}
        sensor_dict["sensorID"] = self.sensorID
        sensor_dict["ip"] = self.sensorIP
        sensor_dict["port"] = self.sensorPort
        sensor_dict["caseID"] = self.caseID
        sensor_dict["name"] = self.sensorID
        sensor_dict["last_seen"] = time.time()
        sensor_dict["dev_name"] = 'rpi'

        r = requests.post(f"http://{catalog_ip}:{catalog_port}/addSensor", json=sensor_dict)
        dict_of_topics = json.loads(r.text)['topic']
        print("dict_of_topics",dict_of_topics)
        self.topic_temp = dict_of_topics["topic_temp"]
        self.topic_hum = dict_of_topics["topic_hum"]
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

        requests.post(f"http://{catalog_ip}:{catalog_port}/removeDevice", json=sensor_dict)
        print("[{}] Device Removed from Catalog".format(
            int(time.time()),
        ))

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        print("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")

        if msg.topic == self.topicBreadType:
            self.category = json.loads(msg.payload)['category']
            print("category", self.category)

        try:
            data = json.loads(msg.payload)
            if msg.topic == self.topic_temp:
                self.insertDataTemp(data)
            elif msg.topic == self.topic_hum:
                self.insertDataHum(data)

            print("INFLUXDB", self.message)

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
        sql = "INSERT INTO temperature (TIMESTAMP, VALUE, TYPE) values (%s,%s,%s)"
        self.db.cursor.execute(sql, [data["timestamp"], data["value"], data["typology"]])
        self.db.db.commit()


if __name__ == "__main__":
    
    with open("config.json", 'r') as sensor_f:
        sensor_config = json.load(sensor_f)
        sensor_ip = sensor_config['sensor_ip']
        sensor_port = sensor_config['sensor_port']
        sensor_caseID = sensor_config["caseID"]
        catalog_ip = sensor_config['catalog_ip']
        catalog_port = sensor_config['catalog_port']
        influx_ip = sensor_config['influx_ip']
        influx_port = sensor_config['influx_port']




    dataInfluxDB = requests.get(f"http://{influx_ip}:{influx_port}/InfluxDB")
    influxDB = InfluxDB(json.loads(dataInfluxDB.text))
 

    sensor = TemperatureHumiditySensor(sensor_caseID +'-'+  'TempHum', influxDB, sensor_ip, sensor_port, catalog_ip, catalog_port )

    sensor.registerDevice()
    sensor.start()

    try:
        while True:
            # read temperature and humidity
            humidity, temperature = Adafruit_DHT.read_retry(11, 4)  # (sensor,pin)

            print('Temp: {0:0.1f} °C  Humidity: {1:0.1f} %'.format(temperature, humidity))

            payload_temp = {"caseID":sensor.caseID, "measurement": "temperature", "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "value": str(temperature), "category": sensor.category }
            time.sleep(1)
            payload_hum  = {"caseID":sensor.caseID, "measurement": "humidity", "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "value": str(humidity), "category": sensor.category}

            sensor.myPublish(sensor.topic_temp, payload_temp)
            sensor.myPublish(sensor.topic_hum, payload_hum)

            

            time.sleep(15)

    except KeyboardInterrupt:
        pass

    sensor.stop()
    sensor.removeDevice()

    c = ClientQuery(sensor.sensorID, sensor.category)
    c.start()




