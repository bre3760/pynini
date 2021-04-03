from controller.caseControl import CaseControl
import requests
import json

global CATALOG_ADDRESS
CATALOG_ADDRESS = "172.20.10.11"

#catalog = requests.get(CATALOG_ADDRESS).json()
#catalog_port = catalog["catalog_port"]
with open('../catalog/catalog.json', 'r') as f:
    config_dict = json.load(f)
    #local_topic = config_dict['network_name']
    catalog_port = config_dict["catalog_port"]

# IP of catalog
# catalog_IP = '172.20.10.11'
# port of catalog
# catalog_port = '9090'
# URL of catalog
broker_url = "http://" + CATALOG_ADDRESS + ":" + catalog_port + "/broker"
# the broker IP and port are requested to the room catalog
r = requests.get(broker_url)
print("Broker IP and port obtained from Catalog")
obj = json.loads(r.text)
broker_IP = obj["broker"]
broker_port = obj["port"]

# Case Controller: init, start and subscription of measurment topics

case_controller = CaseControl("Case controller", broker_IP, broker_port, CATALOG_ADDRESS, catalog_port)
case_controller.run()

# case_controller.myMqttClient.mySubscribe("button")
case_controller.myMqttClient.mySubscribe("trigger/threshold")
case_controller.myMqttClient.mySubscribe("measure/temperature")
case_controller.myMqttClient.mySubscribe("measure/humidity")
case_controller.myMqttClient.mySubscribe("measure/CO2")