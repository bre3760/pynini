import paho.mqtt.client as PahoMQTT
import json, time, datetime
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import cherrypy

"""
This module is a MQTT subscriber that will subscribe to all topics for the sensors of the cases connected, 
when a message is published by a sensor it will immediately check which one and then use 
MQTT to upload the data to influx db cloud.
For the telegram bot it will use rest apis. 
"""

class DBConnectorREST:
    
    exposed = True
    def __init__(self, config_data):
        self.api_ip = json.loads(config_data.text)["api_ip"]      
        self.api_port = json.loads(config_data.text)["api_port"]    
        

    def GET(self,*uri,**params):
        if uri[0]=="getData":             

            print("In getData")
            query = f'from(bucket: "Pynini")|> range(start: -3d)|> filter(fn: (r) => r.caseID == "{params["caseID"]}") |> filter(fn: (r) => r["_measurement"] == "{params["sensor"]}") |> filter(fn: (r) => r.category == "{params["category"]}")'
            print(f"query is {query}")
            result = self.client.query_api().query(org=self.org, query=query)
            results = []
            values = []
            res = []
            for table in result:
                for record in table.records:
                    results.append((record.get_field(), record.get_value()))
                    if record.get_field() == 'value':
                        values.append(record.get_value())

            for v in values:
                w = float(v)
                res.append(round(w, 2))

            print(f"Results from query {results}, {res}")
            return res
            

class DBConnectorMQTT:
    def __init__(self, influx_data, topics, ID):
        # cloud db configuration
        # self.pynini = json.loads(.text)["name"]
        self.ID = ID

        self.url = json.loads(influx_data.text)["url"]
        self.token = json.loads(influx_data.text)["token"]
        self.bucket = json.loads(influx_data.text)["bucket"]
        self.org = json.loads(influx_data.text)['org']
        self.client = InfluxDBClient(
            self.url,
            self.token,
            self.org
        )
        
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_ip")
        print(r.text)
        self.broker_address = json.loads(r.text)
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_port")

        self.broker_port = json.loads(r.text)
        self.topics = topics
        self.client_obj = PahoMQTT.Client(self.ID)


        # register the callback
        self.client_obj.on_connect = self.connect_callback
        self.client_obj.on_message = self.message_callback

    # callback for connection
    def connect_callback(self, client, userdata, flags, rc):
        if rc == 0:
            print("%s connected to broker %s." % (self.ID, self.broker_address))
            rc = 1


    def start(self):
        self.client_obj.username_pw_set(username="brendan", password="pynini")
        self.client_obj.connect(self.broker_address, self.broker_port)
        self.client_obj.loop_start()

        for topic in self.topics:
            self.client_obj.subscribe(topic, qos=2)
        print(f"Connected and subscribed")


    # device stopping
    def stop(self):
        for topic in self.topics:
            self.client_obj.unsubscribe(topic)
        self.client_obj.disconnect()
        print("Disconnected from broker")


    # callback for messages
    def message_callback(self, client, userdata, message):
        if (message.topic == "+/measure/co2"):
            print("Topic:'" + message.topic + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)
            self.sentToDB(data)

        elif (message.topic == "measure/temperature"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)
            self.sentToDB(data)

        elif (message.topic == "measure/humidity"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)
            self.sentToDB(data)

            
        
    def sendToDB(self, data):
        
        write_api = self.client.write_api(write_options=SYNCHRONOUS) 
        
        print("type of ",type( data["caseID"]))
        print("type of ",type( data["category"]))
        print("type of ",type( data["value"]))
        print("type of ",type( data["unit_of_measurement"]))

        
        p = Point(data["measurement"]).tag("caseID", data["caseID"]).tag("category", data["category"]).tag("unit_of_measurement", data["unit_of_measurement"]).field("value", data["value"]).time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(self.bucket, self.org, record=p)
        print("Data sent to the db")
        
        write_api.close()
        

# main function
if __name__ == '__main__':
    headers = {'Content-type': 'application/json', 'Accept': 'raw'}
    topics = []

    with open("config.json", 'r') as dbconfig:
        dict_config = json.load(dbconfig)
        catalog_ip = dict_config['ip']
        catalog_port = dict_config['port']
        list_of_wanted_topics = dict_config["list_of_wanted_topics"]

    # get all information in order to connect to the db
    influx_data = requests.get(f"http://{catalog_ip}:{catalog_port}/InfluxDB")


    #RITORNA TOKEN URL BUCKET
    
    # retrieve the topics from the catalog
    r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
    dict_topics = json.loads(r.text)


    for key, value in dict_topics.items():
        if key in list_of_wanted_topics:
            if key == "TempHum": # add arduino here for expansion (key=="arduino")
                for k, v in value.items():
                    if v not in topics:
                        topics.append(v)
            else:
                topics.append(value)

    print("topicheeeeee: ", topics)

    db_connector = DBConnectorMQTT(influx_data, topics, "DB")



    db_connector_api = DBConnectorREST(influx_data)

    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.tree.mount(db_connector_api, '/db', conf)
    cherrypy.server.socket_host = db_connector_api.api_ip
    cherrypy.server.socket_port = db_connector_api.api_port
    cherrypy.engine.start()
