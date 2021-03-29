from mqtt_temperature.caseControl import CaseControl
import time
import requests
import json


# IP of room catalog
catalog_IP = '172.20.10.11'
# port of room catalog
catalog_port = '9090'
# URL of catalog
broker_url = "http://" + catalog_IP + ":" + catalog_port + "/broker"
# the broker IP and port are requested to the room catalog
r = requests.get(broker_url)
print("Broker IP and port obtained from Room Catalog")
obj = json.loads(r.text)
broker_IP = obj["broker"]
broker_port = obj["port"]


# Case Controller: init, start and subscription of measurment topics

case_controller = CaseControl("Case controller", broker_IP, broker_port, catalog_IP, catalog_port)
case_controller.run()
case_controller.myMqttClient.mySubscribe("trigger/threshold")
case_controller.myMqttClient.mySubscribe("measure/temperature")
case_controller.myMqttClient.mySubscribe("measure/humidity")
case_controller.myMqttClient.mySubscribe("measure/CO2")