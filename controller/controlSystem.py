import sys
sys.path.append('../')
from controller.caseControl import CaseControl
import requests
import json
import os
import time

if __name__ == '__main__':

    # open config file in controller folder
    with open("config.json", 'r') as f:
        config_dict = json.load(f)
        catalog_port = config_dict["catalog_port"]
        catalog_ip = config_dict["catalog_ip"]


    broker_url = "http://" + catalog_ip + ":" + str(catalog_port) + "/broker_ip"
    print(broker_url)
    # the broker IP and port are requested to the catalog REST service
    try:
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_ip_outside")
        print("Broker IP and port obtained from Catalog")
        broker_ip = json.loads(r.text)
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_port")
        broker_port = json.loads(r.text)
        print(f"Inside try condition, broker ip and broker port {broker_ip} {broker_port}")
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
        elif  key =="stats":
            pass
        else:
            if value not in topics:
                topics.append(value)

    print("topics that the controller subscribed to: \n",topics)

    
    r = requests.get(f"http://{catalog_ip}:{catalog_port}/cases")
    dict_of_cases = json.loads(r.text)

    list_of_cases = [x["caseID"] for x in dict_of_cases]
    print("Connected cases id: ", list_of_cases)

    controllers = [CaseControl(client_id, broker_ip, broker_port, catalog_ip, catalog_port, topics) for client_id in list_of_cases]

    for obj in controllers:
        print(f"Obj, in controller {obj}")
        for topic in topics:
            case_specific_topic = obj.clientID +"/"+ topic
            obj.myMqttClient.mySubscribe(case_specific_topic)
        obj.run()




            
        
        
        
        
        
