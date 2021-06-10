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
            #msg = str.replace(msg_payload, "'", '"')
            json_mex = json.loads(msg_payload)
            value = json_mex["value"]
            int_value = value.split(".")[0]
            self.currentTemperature = int(int_value)

        if topic == "measure/humidity":
            #msg = str.replace(msg_payload, "'", '"')
            json_mex = json.loads(msg_payload)
            value = json_mex["value"]
            int_value = value.split(".")[0]
            # the received value of humidity is saved
            self.currentHumidity = int(int_value)

        if topic == "measure/CO2":
            # msg = str.replace(msg_payload, "'", '"')
            json_mex = json.loads(msg_payload)
            value = json_mex["value"]
            # the received value of co2 is saved
            self.currentCO2 = int(value)

        if topic == "breadType/":
            if msg_payload: 
                json_mex = json.loads(msg_payload)
                print("JSSSSONNMEEEXX BREADTYPE", json_mex)
                indexBreadTypeChosen = int(json_mex["bread_index"])
                if self.breadTypeChosen != self.allBreadTypes[indexBreadTypeChosen]:
                    print("Case " + str(self.clientID)+ " now holds " + str(self.breadTypeChosen)+' bread')
                    setBreadtype = {}
                    setBreadtype['breadtype'] = self.breadTypeChosen
                    setBreadtype['caseID'] = self.clientID
                    requests.post("http://" + self.catalog_address + ":" + self.port_catalog + "/setBreadtype", json=setBreadtype)
                    print('CHANGING THRESHOLDS...')
                    self.minTemperature = self.getMinTemperatureThreshold()
                    self.maxTemperature = self.getMaxTemperatureThreshold()
                    self.maxHumidity = self.getMaxHumidityThreshold()
                    self.minHumidity = self.getMinHumidityThreshold()
                    self.maxC02 = self.getMaxCO2Threshold()
                    # change thresholds based on breadtype

    def getAllBreadTypes(self):
        r = requests.get(f"http://{self.catalog_address}:{self.port_catalog}/breadCategories")
        self.allBreadTypes = json.loads(r.text)

    def getCatalog(self):
        with open("config.json", 'r') as f:
            config_dict = json.load(f)
            catalog_port = config_dict["catalog_port"]
            catalog_address = config_dict["catalog_address"]
        return catalog_address, catalog_port

    def getMaxTemperatureThreshold(self):
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

        return minTemperature

    def getMaxHumidityThreshold(self):
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
        maxco2 = 50
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text
            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    maxco2 = int(th["max_co2_th"])
        # if connection to the catalog fails, the max co2 allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)
            
        return (maxco2)

    def getMinCO2Threshold(self):
        minco2 = 50
        try:
            threshold_URL = "http://" + self.catalog_address + ":" + self.port_catalog + "/thresholds"
            r = requests.get(threshold_URL)
            threshold = r.text
            obj = json.loads(threshold) # list of the thresholds
            for th in obj:
                if th["type"] == self.breadTypeChosen:
                    minco2 = int(th["min_co2_th"])
        # if connection to the catalog fails, the max co2 allowed is set to a default value
        except requests.exceptions.RequestException as e:
            print(e)

        return (minco2)

    def getBreadTypeThresholds(self):
        try:
            threshold_URL = "http://" + str(self.catalog_address) + ":" + str(self.port_catalog) + "/thresholds"
            r = requests.get(threshold_URL)
            print("Bread in " + self.clientID)
            threshold = r.text
            obj = json.loads(threshold)
            threshold = obj["thresholds"]
            name = threshold[self.breadTypeChosen]

        except requests.exceptions.RequestException as e:
            print(e)

        return name

    def isTemperatureValid(self):
        """
        method that checks if current temperature is valid: 
        if it is, the method returns True, False otherwise
        """
        if self.minTemperature < self.currentTemperature < self.maxTemperature:
            return True
        else:
            return False

    def tooHot(self):
        if self.currentTemperature > self.maxTemperature:
            return True
        else:
            return False

    def tooCold(self):
        if self.currentTemperature < self.minTemperature:
            return True
        else:
            return False


    def isHumidityValid(self):
        """
        method that checks if current humidity is valid: 
        if it is, the method returns True, False otherwise
        """
        if self.minHumidity < self.currentHumidity < self.maxHumidity:
            return True
        else:
            return False
    
    def tooHumid(self):
        if self.currentHumidity > self.maxHumidity:
            return True
        else:
            return False

    def tooNotHumid(self):
        if self.currentHumidity < self.minHumidity:
            return True
        else:
            return False

    def isCO2Valid(self):
        """
        method that checks if current humidity is valid: 
        if it is, the method returns True, False otherwise
        """
        if self.currentCO2 < self.maxC02:
            return True
        else:
            return False
    
    def tooMuchCo2(self):
        if self.currentCO2 > self.maxC02:
            return True
        else:
            return False


 
