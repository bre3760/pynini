import json
import requests
from controller.MyMQTT import *

global CATALOG_ADDRESS
global CATEGORY
CATALOG_ADDRESS = "http://localhost:9090" # deciso che sarà una variabile globale, accessibile da tutti gli script di tutto il progetto
CATEGORY = 'White'

class CaseControl(object):
    def __init__(self, clientID, IP_broker, port_broker, IP_catalog, port_catalog, topic):

        self.clientID = clientID
        self.myMqttClient = MyMQTT(self.clientID, IP_broker, port_broker, topic)
        self.IP_catalog = IP_catalog
        self.port_catalog = port_catalog
        self.type = self.getBreadType() # la categoria di pane va ricercata nel catalog, nella teca
        self.minTemperature = self.getMinTemperatureThreshold()
        self.maxTemperature = self.getMaxTemperatureThreshold()
        self.maxHumidity = self.getMaxHumidityThreshold()
        self.minHumidity = self.getMinHumidityThreshold()
        self.maxC02 = self.getMaxCO2Threshold()
        self.currentTemperature = 20
        self.currentHumidity = 0
        self.currentCO2 = 0

    def run(self):

        print("running %s" % self.clientID)
        self.myMqttClient.start()

    def end(self):

        print("ending %s" % self.clientID)
        self.myMqttClient.stop()

    def notify(self, topic, msg):

        # print("%s received '%s' under topic '%s'" % (self.clientID, msg, topic))

        if topic == "trigger/threshold":
            # update of thresholds contained in the room catalog

            # if json_mex["msg"] == "timeout":
            self.timeOut = self.getTimeOut()
            # if json_mex["msg"] == "max_temp":
            self.maxTemperature = self.getMaxTemperatureThreshold()
            # if json_mex["msg"] == "min_temp":
            self.minTemperature = self.getMinTemperatureThreshold()
            self.maxHumidity = self.getMaxHumidityThreshold()
            self.controlHeating()

        if topic == "measure/temperature":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            # the received value of temperature is saved
            self.currentTemperature = value

        if topic == "measure/humidity":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            # the received value of humidity is saved
            self.currentHumidity = int(value)

        if topic == "measure/CO2":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            # the received value of humidity is saved
            self.currentCO2 = int(value)

    def getMaxTemperatureThreshold(self):
        try:
            threshold_URL = "http://" + self.IP_catalog + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            print("Maximum temperature allowed by " + self.clientID)
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["thresholds"]
            maxTemperature = threshold[CATEGORY]["max_temperature_th"]

        except requests.exceptions.RequestException as e:
            print(e)
            # if connection to the catalog fails, the max temperature allowed is set to a default value
            maxTemperature = 25

        return int(maxTemperature)

    def getMinTemperatureThreshold(self):

        try:
            threshold_URL = "http://" + self.IP_catalog + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            print("Minimum temperature allowed by " + self.clientID)

            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["thresholds"]
            minTemperature = threshold[CATEGORY]["min_temperature_th"]

        except requests.exceptions.RequestException as e:
            print(e)
            # if connection to the catalog fails, the minimum humidity allowed is set to a default value
            minTemperature = 15

        return int(minTemperature)

    def getMaxHumidityThreshold(self):
        try:
            threshold_URL = "http://" + self.IP_catalog + ":" + self.port_catalog + "/threshold"
            r = requests.get(threshold_URL)
            print("Maximum humidity allowed by " + self.clientID)
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["thresholds"]
            maxHumidity = threshold[CATEGORY]["max_humidity_th"]

        # if connection to the catalog fails, the max humidity allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)
            maxHumidity = 50

        return int(maxHumidity)

    def getMinHumidityThreshold(self):
        try:
            threshold_URL = "http://" + self.IP_catalog + ":" + self.port_catalog + "/threshold"
            r = requests.get(threshold_URL)
            print("Minimum humidity allowed by " + self.clientID)
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["thresholds"]
            minHumidity = threshold[CATEGORY]["min_humidity_th"]

        # if connection to the catalog fails, the min humidity allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)
            minHumidity = 0

        return int(minHumidity)

    def getMaxCO2Threshold(self):
        try:
            threshold_URL = "http://" + self.IP_catalog + ":" + self.port_catalog + "/threshold"
            r = requests.get(threshold_URL)
            print("Maximum CO2 allowed by " + self.clientID)
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["thresholds"]
            maxHumidity = threshold[CATEGORY]["max_co2_th"]

        # if connection to the catalog fails, the max co2 allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)
            maxco2 = 50

        return int(maxco2)

    def getBreadType(self):
        try:
            threshold_URL = "http://" + str(self.IP_catalog) + ":" + str(self.port_catalog) + "/thresholds"
            r = requests.get(threshold_URL)
            print("Bread in " + self.clientID)
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["thresholds"]
            name = threshold[CATEGORY]

        except requests.exceptions.RequestException as e:
            print(e)

        return name

    def isTemperatureValid(self):
        """method that checks if current temperature is valid: if it is, the method returns True, False otherwise"""
        if int(self.minTemperature) < self.currentTemperature < int(self.maxTemperature):
            return True
        else:
            return False

    def isHumidityValid(self):
        """method that checks if current humidity is valid: if it is, the method returns True, False otherwise"""
        if self.minHumidity < self.currentHumidity < self.maxHumidity:
            return True
        else:
            return False

    def isCO2Valid(self):
        """method that checks if current humidity is valid: if it is, the method returns True, False otherwise"""
        if self.currentCO2 < self.maxC02:
            return True
        else:
            return False

    def controlHeating(self):
        """method that, basing on the current temperature or humidity or co2, sends alerts or complement tha status of the cooling system"""

        print('bella')

    def getTimeOut(self):

        pippo = "ciao"
        print("work in progress")

        return pippo