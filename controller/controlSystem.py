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
        catalog_address = config_dict["catalog_address"]


    broker_url = "http://" + catalog_address + ":" + str(catalog_port) + "/broker"

    # the broker IP and port are requested to the catalog REST service
    try:
        r = requests.get("http://localhost:9090/broker_ip")
        print("Broker IP and port obtained from Catalog")
        broker_ip = json.loads(r.text)
        r = requests.get("http://localhost:9090/broker_port")
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
        r = requests.get("http://localhost:9090/topics")
        dict_of_topics = json.loads(r.text)
    except:
        print("REST service not active")

    for key, value in dict_of_topics.items():
        if key == "TempHum" or key == "arduino":
            # for k, v in value.items():
            #     topics.append(v)
            continue
        else:
            topics.append(value)
    print("topics that the controller subscribed to: \n",topics)


    # initiate class of CaseControl which houses all necessary functions
    case_controller = CaseControl("Case controller", broker_ip, broker_port, catalog_address, catalog_port, topics)
    case_controller.run()

    # subscribe the case controller to all topics
    # no need to subscribe to trigger topics but could always be helpful to 
    # know their status
    for topic in topics:
        
        case_controller.myMqttClient.mySubscribe(topic)


    while 1:
        """
        control system algorithm that continually checks if the values are within the desired ranges
        """
        if not case_controller.isTemperatureValid():
            case_controller.myMqttClient.myPublish("trigger/fan",json.dumps({"message":"on"}))
            # print("Ho accceso la ventola")
        else:
            case_controller.myMqttClient.myPublish("trigger/fan",json.dumps({"message":"off"}))
            # print("Ho spento la ventola")


        # if not case_controller.isCO2Valid():
        #     case_controller.myMqttClient.myPublish("trigger/lamp", json.dumps({"message": "on"}))
        #     # print("Ho acceso la lampada")
        # else:
        #     case_controller.myMqttClient.myPublish("trigger/lamp", json.dumps({"message": "off"}))
        #     # print("Ho spento la lampada")

        time.sleep(5)
        
            
        
        
        
        
        
