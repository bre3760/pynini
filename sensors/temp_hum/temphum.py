import paho.mqtt.client as PahoMQTT
import time
import json
import requests
from datetime import datetime
# import Adafruit_DHT
import random
import sys
sys.path.append("../../")


class TemperatureHumiditySensor:
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
        self.messageBroker = ""
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
        self.topic_temp = ""
        self.topic_hum= ""
        self.topicBreadType = self.caseID + "/" +json.loads(r.text)["breadType"]
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
        #TODO: METTI PORTA MQTT DAL CATALOG
        self._paho_mqtt.connect(self.messageBroker, 1883)
        self._paho_mqtt.loop_start()
        self._paho_mqtt.subscribe(self.topicBreadType, 2)

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic_temp)
        self._paho_mqtt.unsubscribe(self.topic_hum)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myPublish(self, topic, message):
        # publish a message with a certain topic (measure/temperature or measure/humidity)
        case_specific_topic = self.caseID + "/" + topic 
        print(f"Publishing on topic {case_specific_topic}")

        self._paho_mqtt.publish(case_specific_topic, json.dumps(message), 2)

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.messageBroker, rc))

    def registerDevice(self):
        sensor_dict = {}
        sensor_dict["sensorID"] = self.sensorID
        sensor_dict["ip"] = self.sensorIP
        sensor_dict["port"] = self.sensorPort
        sensor_dict["caseID"] = self.caseID
        sensor_dict["name"] = self.sensorID
        sensor_dict["last_seen"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        sensor_dict["dev_name"] = 'rpi'

        print("sensor_dict", sensor_dict)

        r = requests.post(f"http://{catalog_ip}:{catalog_port}/addSensor", json=sensor_dict)

        dict_of_topics = json.loads(r.text)['topic']

        print("dict_of_topics",dict_of_topics)
        
        self.topic_temp = dict_of_topics["topic_temp"]
        self.topic_hum = dict_of_topics["topic_hum"]
        self.messageBroker = json.loads(r.text)['broker_ip_outside'] # use ip_outside when trying from other pc to rasp
        self.breadCategories = json.loads(r.text)["breadCategories"]
        ##########################################################################
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
        sensor_dict["topics"] = [self.caseID + "/" + self.topic_temp, self.caseID + "/" + self.topic_hum]

        print("sensor dict before db post request", sensor_dict)
        #sensor_dic viene mandato a db adaptor a cui si sottoscrive 
        r = requests.post(f"http://{influx_api_ip}:{influx_api_port}/db/addSensor", json=sensor_dict)

        print(f"Response (r) from post to db api {r}")
        ##########################################################################

        print( f"Device Registered on Catalog {sensor_dict['last_seen']}")

    def removeDevice(self):
        sensor_dict = {}
        sensor_dict['sensorID'] = self.sensorID
        sensor_dict["caseID"] = self.caseID
        sensor_dict["ip"] = self.sensorIP
        sensor_dict["port"] = self.sensorPort
        sensor_dict["name"] = self.sensorID
        sensor_dict["dev_name"] = 'rpi'

        requests.post(f"http://{catalog_ip}:{catalog_port}/removeDevice", json=sensor_dict)
        removalTime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print( f"Device Removed on Catalog {removalTime}")


    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        if msg.topic == self.topicBreadType:
            print("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")

            if json.loads(msg.payload)['bread_index'] != '':
                self.category = self.breadCategories[int(json.loads(msg.payload)['bread_index'])]
                print("bread_index", self.category)


if __name__ == "__main__":
    
    with open("config.json", 'r') as sensor_f:
        sensor_config = json.load(sensor_f)
        sensor_ip = sensor_config['sensor_ip']
        sensor_port = sensor_config['sensor_port']
        sensor_caseID = sensor_config["caseID"]
        catalog_ip = sensor_config['catalog_ip']
        catalog_port = sensor_config['catalog_port']

    sensor = TemperatureHumiditySensor(sensor_caseID +'-'+ 'TempHum', sensor_ip, sensor_port, catalog_ip, catalog_port)
    sensor.registerDevice()
    sensor.start()

    try:
        while True:
            # read temperature and humidity
            # humidity, temperature = Adafruit_DHT.read_retry(11, 4)  # (sensor,pin)
            humidity = round(random.uniform(30, 40),2)
            temperature = round(random.uniform(23, 30),2)
            if humidity < 100:

                print('Temp: {0:0.1f} °C  Humidity: {1:0.1f} %'.format(temperature, humidity))

                payload_temp = {"caseID":sensor.caseID, 
                                "measurement": "temperature", 
                                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), 
                                "value": temperature, 
                                "category": sensor.category,
                                "unit_of_measurement": "Celsius" }

                payload_hum  = {"caseID":sensor.caseID, 
                                "measurement": "humidity", 
                                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), 
                                "value": humidity, 
                                "category": sensor.category,
                                "unit_of_measurement":"Relative Humidity"}

                sensor.myPublish(sensor.topic_temp, payload_temp)
                time.sleep(1)
                sensor.myPublish(sensor.topic_hum, payload_hum)

            

            time.sleep(15) # publish every 15 seconds

    except KeyboardInterrupt:
        pass

    sensor.stop()
    sensor.removeDevice()

 


