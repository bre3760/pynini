import sys
sys.path.append('./')
import requests
import json
import os
import time
import paho.mqtt.client as PahoMQTT

"""Single file for controller"""


class CaseControlMQTT:
    def __init__(self, client_caseID, catalog_address, port_catalog, topics):

        # MQTT configuration from MYMQTT
        bIp = requests.get(f"http://{catalog_address}:{port_catalog}/broker_ip_outside")  #outside se no rasp
        bPort = requests.get(f"http://{catalog_address}:{port_catalog}/broker_port")

        self.broker =  json.loads(bIp.text)
        self.port =  json.loads(bPort.text)
        # self.notifier = notifier
        self.client_caseID = client_caseID
        self.initialTopics = topics
        self._isSubscriber = False
        self._topic = []
        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(client_caseID, False)
        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

        self.catalog_address = catalog_address
        self.port_catalog = str(port_catalog)
        self.allBreadTypes = []
        self.getAllBreadTypes()
        self.breadTypeChosen = self.allBreadTypes[0] # initialization
        self.minTemperature = self.getMinTemperatureThreshold()
        self.maxTemperature = self.getMaxTemperatureThreshold()
        self.maxHumidity = self.getMaxHumidityThreshold()
        self.minHumidity = self.getMinHumidityThreshold()
        self.maxC02 = self.getMaxCO2Threshold()
        self.default_value = -70 # default out of range values for initialization
        self.currentTemperature = 0 
        self.currentHumidity = 0
        self.currentCO2 = 0
        self.prevStateLamp = "off"
        self.prevStateFan = "off"

    def myOnConnect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to %s with result code: %d" % (self.broker, rc))
 

    def myPublish (self, topic, msg):
        print ("publishing '%s' with topic '%s'" % (msg, topic))
        self._paho_mqtt.publish(topic, msg, 2)


    def start(self):
        # manage connection to broker
        self._paho_mqtt.username_pw_set(username="brendan", password="pynini")
        self._paho_mqtt.connect(self.broker , self.port)
        self._paho_mqtt.loop_start()
        for topic in self.initialTopics:
            case_specific_topic = obj.client_caseID +"/"+ topic
            print(f"Subscribing to topic {case_specific_topic}")
            self._paho_mqtt.subscribe(case_specific_topic, 2)
        
		

    def stop (self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber
            self._paho_mqtt.unsubscribe(self._topic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()


    def myOnMessageReceived(self, paho_mqtt, userdata, msg_payload):
        print(f'In myOnMessageReceived received msg_payload under topic {msg_payload.topic}')
        topic = msg_payload.topic

        if topic == "measure/temperature":
            json_mex = json.loads(msg_payload)
            self.currentTemperature = json_mex["value"]
            if not self.isTemperatureValid():
                if self.prevStateFan != "off": # if fan was on turn it off
                    self.myPublish(self.client_caseID + "/" + "trigger/fan", json.dumps({"message":"off"}))
                    self.prevStateFan ="off"
                if self.prevStateLamp != "off":
                    self.myPublish(self.client_caseID + "/" +"trigger/lamp", json.dumps({"message":"off"}))
                    self.prevStateLamp = "off"

            
        if topic == "measure/humidity":
            json_mex = json.loads(msg_payload)
            # the received value of humidity is saved
            self.currentHumidity = json_mex["value"]
            if not self.isHumidityValid():
                if self.prevStateFan != "off": # if fan was on turn it off
                    self.myPublish(self.client_caseID + "/" + "trigger/fan", json.dumps({"message":"off"}))
                    self.prevStateFan ="off"
                if self.prevStateLamp != "off":
                    self.myPublish(self.client_caseID + "/" +"trigger/lamp", json.dumps({"message":"off"}))
                    self.prevStateLamp = "off"
                


        if topic == "measure/CO2":
            json_mex = json.loads(msg_payload)
            # the received value of co2 is saved
            self.currentCO2 = json_mex["value"]
            if not self.isCO2Valid():
                print("Co2 is not valid! Taking action")
                if self.prevStateFan != "off": # if fan was on turn it off
                    self.myPublish(self.client_caseID + "/" + "trigger/fan", json.dumps({"message":"off"}))
                    self.prevStateFan ="off"
                if self.prevStateLamp != "off":
                    self.myPublish(self.client_caseID + "/" +"trigger/lamp", json.dumps({"message":"off"}))
                    self.prevStateLamp = "off"


        if topic == "breadType/":
            if msg_payload: 
                json_mex = json.loads(msg_payload)
                indexBreadTypeChosen = int(json_mex["bread_index"])
                if self.breadTypeChosen != self.allBreadTypes[indexBreadTypeChosen]:
                    print("Case " + str(self.client_caseID)+ " now holds " + str(self.breadTypeChosen)+' bread')
                    setBreadtype = {}
                    setBreadtype['breadtype'] = self.breadTypeChosen
                    setBreadtype['caseID'] = self.client_caseID
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






if __name__ == '__main__':

    # open config file in controller folder
    with open("config.json", 'r') as f:
        config_dict = json.load(f)
        catalog_port = config_dict["catalog_port"]
        catalog_ip = config_dict["catalog_ip"]

    """
    The case controller needs to subscribe to:
        - temperature topic
        - humidity topic
        - bread type topic
    This will allow the control system to check if the values measured 
    are within the limits of the current configuration and if not be able 
    to activate the actuators to bring the setting back to normal values. 
    """

    topics = []  # initialization for topics already in use (case in which db is turned on later)
    try:
        # request to get all topics 
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
        dict_of_topics = json.loads(r.text)
    except:
        print("REST service not active")

    for key, value in dict_of_topics.items():
        if key == "TempHum" or key == "arduino":
            for k, v in value.items():
                if v not in topics:
                    topics.append(v)
        elif  key =="stats":
            pass
        else:
            if value not in topics:
                topics.append(value)

    if len(topics)>0:
        print("Topics that the controller will subscribe to: \n",topics)
    else:
        print(f"No active cases or devices, will subscribe when they are activated")
    
    r = requests.get(f"http://{catalog_ip}:{catalog_port}/cases")
    dict_of_cases = json.loads(r.text)

    list_of_cases = [x["caseID"] for x in dict_of_cases]
    print("Connected cases to the system: ", list_of_cases)

    controllers = [CaseControlMQTT(client_caseID, catalog_ip, catalog_port, topics) for client_caseID in list_of_cases]

    for obj in controllers:
        print(f"Obj, in controller {obj} starting...")
        obj.start()
        print(f"Started!")

    while True:
        pass
    