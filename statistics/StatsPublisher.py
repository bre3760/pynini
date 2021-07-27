import random 
import pandas as pd
from datetime import datetime
from datetime import timedelta
import requests
import json
import paho.mqtt.client as PahoMQTT
import time

"""
script that creates the history of purchases for different bread types
the dataframe has the following structure
# date, number sold white, number sold wheat, number sold glutenfree
unit of measurement: €/kg
"""



class statsPublisher:
    def __init__(self, catalog_ip, catalog_port, clientID):
        
        
        self.messageBroker = ""
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")   #forse non usata 
        self.topic_price = json.loads(r.text)["stats"]["topic_price"]
        self.topic_quantity= json.loads(r.text)["stats"]["topic_quantity"]
        
        self.broker_port =  ""

        self.clientID = clientID
        #self.category = category

        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(self.clientID,True) 
        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect

        self.message = {
            'measurement': self.clientID,
            'timestamp': '',
            'value': '',
        }
		

    def start(self):
    #manage connection to broker
        self._paho_mqtt.username_pw_set(username="brendan", password="pynini")

        self._paho_mqtt.connect(self.messageBroker, self.broker_port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myPublish(self, topic, message):
        # "topic_price": "stats/price",
        # "topic_quantity": "stats/quantity"
        # publish a message with a certain topic
        self._paho_mqtt.publish(topic, json.dumps(message, 2))

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print ("Connected to %s with result code: %d" % (self.messageBroker, rc))

    def registerStats(self):
        influx_data = requests.get(f"http://{catalog_ip}:{catalog_port}/InfluxDB")
        influx_api_ip = json.loads(influx_data.text)["api_ip"]
        influx_api_port = json.loads(influx_data.text)["api_port"]
        topics_dics = {}
        topics_dics["topics"] = [self.topic_price, self.topic_quantity]

        r = requests.post(f"http://{influx_api_ip}:{influx_api_port}/db/addStats", json=topics_dics)

        print(f"Response (r) from post to db api {r}")




if __name__ == "__main__":
    
    with open("config.json", 'r') as stats_f:
        stats_config = json.load(stats_f)
        catalog_ip = stats_config['catalog_ip']
        catalog_port = stats_config['catalog_port']
        

    test = statsPublisher(catalog_ip, catalog_port, "Stats")
    test.start()

    

    df_prices = pd.read_csv("purchase_prices.csv")

    df_prices = pd.read_csv("pc.csv")

    for i in range(len(df_prices.index)):
        date_time_obj = datetime.strptime(df_prices.iloc[i]["date"], '%m-%y')


        to_publish_white = {
            "category": "White", "timestamp":date_time_obj, "price" : df_prices.iloc[i]["White"]
        }
        
        test.myPublish(test.topic_price, to_publish_white) #pubblico valore del prezzo in corrispondenza 
        time.sleep(1)

        to_publish_wheat = {
            "category": "Wheat", "timestamp":date_time_obj, "price" : df_prices.iloc[i]["Wheat"]
        }

        test.myPublish(test.topic_price, to_publish_wheat) #pubblico valore del prezzo in corrispondenza 
        time.sleep(1)

        to_publish_glutenfree = {
            "category": "Glutenfree", "timestamp":date_time_obj, "price" : df_prices.iloc[i]["Glutenfree"]
        }          
        test.myPublish(test.topic_price, to_publish_glutenfree) #pubblico valore del prezzo in corrispondenza 
        time.sleep(1)


    df_quantity = pd.read_csv("purchase_history.csv")
    for i in range(len(df_quantity.index)):
        date_time_obj = datetime.strptime(df_quantity.iloc[i]["date"], '%m-%y')


        to_publish_white = {
            "category": "White", "timestamp":date_time_obj, "price" : df_quantity.iloc[i]["White"]
        }
        
        test.myPublish(test.topic_quantity, to_publish_white) #pubblico valore del prezzo in corrispondenza 
        time.sleep(1)

        to_publish_wheat = {
            "category": "Wheat", "timestamp":date_time_obj, "price" : df_quantity.iloc[i]["Wheat"]
        }

        test.myPublish(test.topic_quantity, to_publish_wheat) #pubblico valore del prezzo in corrispondenza 
        time.sleep(1)

        to_publish_glutenfree = {
            "category": "Glutenfree", "timestamp":date_time_obj, "price" : df_quantity.iloc[i]["Glutenfree"]
        }          
        test.myPublish(test.topic_quantity, to_publish_glutenfree) #pubblico valore del prezzo in corrispondenza 
        time.sleep(1)

    test.stop()





