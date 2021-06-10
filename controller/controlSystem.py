import sys
sys.path.append('../')
from controller.caseControl import CaseControl
import requests
import json
import os
import time


cur_path = os.path.dirname(__file__)
catalog_path = os.path.join(cur_path, '..', 'catalog', 'catalog2.json')

if __name__ == '__main__':

    # open config file in controller folder
    with open("config.json", 'r') as f:
        config_dict = json.load(f)
        catalog_port = config_dict["catalog_port"]
        catalog_ip = config_dict["catalog_ip"]
        caseID = config_dict["caseID"]


    broker_url = "http://" + catalog_ip + ":" + str(catalog_port) + "/broker"

    # the broker IP and port are requested to the catalog REST service
    try:
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_ip")
        print("Broker IP and port obtained from Catalog")
        broker_ip = json.loads(r.text)
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_port")
        broker_port = json.loads(r.text)
    except:
        print("REST service of catalog was not reachable")


    print("IP and PORT", broker_ip, broker_port)
    # Case Controller: init, start and subscription of measurment topics
    """
    The case controller needs to subscribe to:
        - temperature topic
        - humidity topic
        - bread type topic
    This will allow the control system to check if the values measured 
    are within the limits of the current configuration and if not be able 
    to activate the actuators to bring the setting back to normal values. 

    """

    topics = []
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
        else:
            if value not in topics:
                topics.append(value)

    print("topics that the controller subscribed to: \n",topics)


    
    r = requests.get(f"http://{catalog_ip}:{catalog_port}/cases")
    dict_of_cases = json.loads(r.text)

    list_of_cases = [x["caseID"] for x in dict_of_cases]
    print("Connected cases id: ", list_of_cases)

    controllers = [CaseControl(i, broker_ip, broker_port, catalog_ip, catalog_port, topics) for i in list_of_cases]

    for obj in controllers:
        obj.run()

        for topic in topics:
            obj.myMqttClient.mySubscribe(topic)

    # initiate class of CaseControl which houses all necessary functions
    #case_controller = CaseControl("Case controller", broker_ip, broker_port, catalog_ip, catalog_port, caseID)
    #case_controller.run()

    # subscribe the case controller to all topics
    # no need to subscribe to trigger topics but could always be helpful to 
    # know their status
    #for topic in topics:
    #    case_controller.myMqttClient.mySubscribe(topic)

    prevStateLamp = "off"
    prevStateFan = "off"
    currentStateLamp = False
    currentStateFan = False
    while 1:
        """
        control system algorithm that continually checks if the values are within the desired ranges
        """
        for obj in controllers:
           

            if obj.isTemperatureValid():
                if prevStateFan != "off": # if fan was on turn it off
                    obj.myMqttClient.myPublish("trigger/fan", json.dumps({"message":"off"}))
                    prevStateFan ="off"
                if prevStateLamp != "off":
                    obj.myMqttClient.myPublish("trigger/lamp", json.dumps({"message":"off"}))
                    prevStateLamp = "off"
            else:
                if obj.tooHot():
                    if prevStateFan != "on":
                        obj.myMqttClient.myPublish("trigger/fan", json.dumps({"message":"on"}))
                        prevStateFan = "on"
                if obj.tooCold():
                    if prevStateLamp != "on":
                        obj.myMqttClient.myPublish("trigger/lamp", json.dumps({"message":"on"}))
                        prevStateLamp = "on"

            if obj.isHumidityValid():
                if prevStateFan != "off": # if fan was on turn it off
                    obj.myMqttClient.myPublish("trigger/fan", json.dumps({"message":"off"}))
                    prevStateFan ="off"
                if prevStateLamp != "off":
                    obj.myMqttClient.myPublish("trigger/lamp", json.dumps({"message":"off"}))
                    prevStateLamp = "off"
                else:
                    if obj.tooHumid():
                        if prevStateFan != "on":
                            obj.myMqttClient.myPublish("trigger/fan", json.dumps({"message":"on"}))
                            prevStateFan = "on"            

            if obj.isCO2Valid():
                if prevStateFan != "off": # if fan was on turn it off
                    obj.myMqttClient.myPublish("trigger/fan", json.dumps({"message":"off"}))
                    prevStateFan ="off"
                else:
                    if prevStateFan != "on":
                        obj.myMqttClient.myPublish("trigger/fan", json.dumps({"message":"on"}))
                        prevStateFan = "on"

            
         

        time.sleep(7)
        
            
        
        
        
        
        
