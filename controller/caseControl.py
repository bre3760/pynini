import json
import requests
from controller.MyMQTT import *


class CaseControl(object):
    def __init__(self, clientID, broker_ip, broker_port, catalog_address, port_catalog, caseID):

        self.clientID = clientID
        self.myMqttClient = MyMQTT(self.clientID, broker_ip, broker_port, self)
        self.catalog_address = catalog_address
        self.port_catalog = str(port_catalog)
        self.caseID = caseID
        self.allBreadTypes = []
        self.getAllBreadTypes()
        self.breadTypeChosen = self.allBreadTypes[0]
        self.minTemperature = self.getMinTemperatureThreshold()
        self.maxTemperature = self.getMaxTemperatureThreshold()
        self.maxHumidity = self.getMaxHumidityThreshold()
        self.minHumidity = self.getMinHumidityThreshold()
        self.maxC02 = self.getMaxCO2Threshold()
        self.default_value = -69 # default out of range values for initialization
        self.currentTemperature = 0 
        self.currentHumidity = 0
        self.currentCO2 = 0
        
    def run(self):
        print("running %s" % self.clientID)
        self.myMqttClient.start()

    def end(self):
        print("ending %s" % self.clientID)
        self.myMqttClient.stop()

    def notify(self, topic, msg_payload):
        print(f'In Notify received msg_payload: {msg_payload}, under topic {topic}')

        if topic == "measure/temperature":
            json_mex = json.loads(msg_payload)
            self.currentTemperature = json_mex["value"]

        if topic == "measure/humidity":
            json_mex = json.loads(msg_payload)
            # the received value of humidity is saved
            self.currentHumidity = json_mex["value"]

        if topic == "measure/CO2":
            json_mex = json.loads(msg_payload)
            # the received value of co2 is saved
            self.currentCO2 = json_mex["value"]

        if topic == "breadType/":
            if msg_payload: 
                json_mex = json.loads(msg_payload)
                indexBreadTypeChosen = int(json_mex["bread_index"])
                if self.breadTypeChosen != self.allBreadTypes[indexBreadTypeChosen]:
                    print("Case " + str(self.clientID)+ " now holds " + str(self.breadTypeChosen)+' bread')
                    setBreadtype = {}
                    setBreadtype['breadtype'] = self.breadTypeChosen
                    setBreadtype['caseID'] = self.clientID
                    requests.post("http://" + self.catalog_address + ":" + self.port_catalog + "/setBreadtype", json=setBreadtype)
                    self.minTemperature = self.getMinTemperatureThreshold()
                    self.maxTemperature = self.getMaxTemperatureThreshold()
                    self.maxHumidity = self.getMaxHumidityThreshold()
                    self.minHumidity = self.getMinHumidityThreshold()
                    self.maxC02 = self.getMaxCO2Threshold()
                    # change thresholds based on breadtype

    def getAllBreadTypes(self):
        """
        method that gets the possible bread categories from the catalog
        """
        r = requests.get(f"http://{self.catalog_address}:{self.port_catalog}/breadCategories")
        self.allBreadTypes = json.loads(r.text)

    def getCatalog(self):
        """
        method that gets the catalog address and the port from the configuration JSON file
        """
        with open("config.json", 'r') as f:
            config_dict = json.load(f)
            catalog_port = config_dict["catalog_port"]
            catalog_address = config_dict["catalog_address"]
        return catalog_address, catalog_port

    def getMaxTemperatureThreshold(self):
        """
        method that gets the upper bound for temperature value for specified bread type.        
        """
        maxTemperature = 40
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text

            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    maxTemperature = int(th["max_temperature_th"])

        except requests.exceptions.RequestException as e:
            print(e)
            # if connection to the catalog fails, the max temperature allowed is set to a default value
        return (maxTemperature)

    def getMinTemperatureThreshold(self):
        """
        method that gets the lower bound for temperature value for specified bread type.        
        """
        minTemperature = 10
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text
            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    minTemperature = int(th["min_temperature_th"])

        except requests.exceptions.RequestException as e:
            print(e)
            # if connection to the catalog fails, the minimum humidity allowed is set to a default value
        print(f"Minimum temperature from threshold {minTemperature}, {type(minTemperature)}")
        return minTemperature

    def getMaxHumidityThreshold(self):
        """
        method that gets the upper bound for humidity value for specified bread type.        
        """
        maxHumidity = 70
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text

            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    maxHumidity = int(th["max_humidity_th"])

        # if connection to the catalog fails, the max humidity allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)

        return int(maxHumidity)

    def getMinHumidityThreshold(self):
        """
        method that gets the lower bound for humidity value for specified bread type.        
        """
        minHumidity = 0
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text

            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    minHumidity = int(th["min_humidity_th"])

        # if connection to the catalog fails, the min humidity allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)

        return (minHumidity)

    def getMaxCO2Threshold(self):
        """
        method that gets the upper bound for co2 value for specified bread type.        
        """
        maxco2 = 6
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text
            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    maxco2 = float(th["max_co2_th"]) 
        # if connection to the catalog fails, the max co2 allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)
            
        return (maxco2)

    def getMinCO2Threshold(self):
        """
        method that gets the lower bound for co2 value for specified bread type.        
        """
        minco2 = 0.5
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text
            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    minco2 = float(th["min_co2_th"])
        # if connection to the catalog fails, the max co2 allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)

        return (minco2)

    def isTemperatureValid(self):
        """
        method that checks if current temperature is valid: 
        if it is, the method returns True, False otherwise
        """
        if self.currentTemperature != self.default_value:
            if self.minTemperature < self.currentTemperature < self.maxTemperature:
                return True
            else:
                return False
        else:
            pass

    def tooHot(self):
        """
        method that checks if the case temperature exceeds its upper bound
         if it is, the method returns True, False otherwise   
        """
        if self.currentTemperature != self.default_value:
            if self.currentTemperature > self.maxTemperature:
                return True
            else:
                return False
        else:
            pass

    def tooCold(self):
        """
        method that checks if the case temperature in under the lower bound
         if it is, the method returns True, False otherwise
        """
        if self.currentTemperature != self.default_value:

            if self.currentTemperature < self.minTemperature:
                return True
            else:
                return False
        else:
            pass


    def isHumidityValid(self):
        """
        method that checks if current humidity is valid: 
        if it is, the method returns True, False otherwise
        """
        if self.currentHumidity != self.default_value:

            if self.minHumidity < self.currentHumidity < self.maxHumidity:
                return True
            else:
                return False
        else:
            pass
    
    def tooHumid(self):
        """
        method that checks if current humidity is higher then the max threshold: 
        if it is, the method returns True, False otherwise
        """
        if self.currentHumidity != self.default_value:

            if self.currentHumidity > self.maxHumidity:
                return True
            else:
                return False
        else:
            pass

    def tooNotHumid(self):
        """
        method that checks if current humidity is lower then the min threshold: 
        if it is, the method returns True, False otherwise
        """
        if self.currentHumidity != self.default_value:

            if self.currentHumidity < self.minHumidity:
                return True
            else:
                return False
        else:
            pass

    def isCO2Valid(self):
        """
        method that checks if current humidity is valid: 
        if it is, the method returns True, False otherwise
        """
        if self.currentCO2 != self.default_value:

            if self.currentCO2 < self.maxC02:
                return True
            else:
                return False
        else:
            pass
        
    def tooMuchCo2(self):
        """
        method that checks if current co2 level is higher then the max threshold: 
        if it is, the method returns True, False otherwise
        """
        if self.currentCO2 != self.default_value:

            if self.currentCO2 > self.maxC02:
                return True
            else:
                return False
        else:
            pass


 
