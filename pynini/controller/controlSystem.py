from caseControl import CaseControl
import requests
import json
import os

global CATALOG_ADDRESS
CATALOG_ADDRESS = "0.0.0.0"

cur_path = os.path.dirname(__file__)
catalog_path = os.path.join(cur_path, '..', 'catalog', 'catalog2.json')

with open(catalog_path, 'r') as f:
    config_dict = json.load(f)
    catalog_port = config_dict["catalog_port"]

print("pippo")
broker_url = "http://" + CATALOG_ADDRESS + ":" + str(catalog_port) + "/broker"
print("pippo")
# the broker IP and port are requested to the room catalog
r = requests.get("http://localhost:9090/broker_ip")
print("Broker IP and port obtained from Catalog")
broker_IP = json.loads(r.text)
r = requests.get("http://localhost:9090/broker_port")
broker_port = json.loads(r.text)


print("IP and PORT", broker_IP, broker_port)
# Case Controller: init, start and subscription of measurment topics
topics = []
r = requests.get("http://localhost:9090/topics")
dict_of_topics = json.loads(r.text)

for key, value in dict_of_topics.items():
    if key == "TempHum":
        for k, v in value.items():
            topics.append(v)
    else:
        topics.append(value)
print("topics",topics)

r = requests.get("http://localhost:9090/cases")
dict_of_cases = json.loads(r.text)

list_of_cases = [x["case_ID"] for x in dict_of_cases]
print("Connected cases id: ", list_of_cases)

controllers = [CaseControl(i, broker_IP, broker_port, CATALOG_ADDRESS, catalog_port, topics) for i in list_of_cases]

#case_controller = CaseControl("CCC1", broker_IP, broker_port, CATALOG_ADDRESS, catalog_port, topics)
for obj in controllers:
    obj.run()

    for topic in topics:
        obj.myMqttClient.mySubscribe(topic)

# multithreading: ciascun thread si occupa di una teca (caseID) e cotrolla che le funzioni isValid diano true, altrimenti attiva gli attuatori
""" 
while 1:
    if not case_controller.isTemperatureValid():
        case_controller.myMqttClient.myPublish("trigger/fan",json.dumps({"message":"on"}))
        print("Ho accceso la ventola")

    if not case_controller.isCO2Valid():
        case_controller.myMqttClient.myPublish("trigger/", json.dumps({"message": "on"}))
        print("Ho acceso la lampada")
        
     """
    
    
    
    
