import paho.mqtt.client as PahoMQTT
import json, time
from datetime import datetime
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

    # add post for when new sensor connects TODO
    def POST(self, *uri, **params):
        global db_connector
        res = {}
        # if len(uri) == 1 and uri[0] == 'addSensor':
        #     # add new sensor to the self.catalog
        #     new_device_info = json.loads(cherrypy.request.body.read())
        #     print("In POST of db api", new_device_info)
             
        #     try:
        #         sensorID = new_device_info['sensorID']
        #         caseID = new_device_info['caseID']
        #         ip = new_device_info['ip']
        #         port = new_device_info['port']
        #         last_seen = new_device_info['last_seen']
        #         dev_name = new_device_info['dev_name']
        #         topics = new_device_info["topics"] # a list is sent

        #         for topic in topics:
        #             db_connector.client_obj.subscribe(topic, qos=2)
                
        #         res["status"] = "ok"

        #         # MQTT client should subscribe to topic caseID/measure/sensorID

        #         return res

        #     except KeyError:
        #         raise cherrypy.HTTPError(400, 'Bad request')
        if len(uri) == 2 and uri[0] == 'db' and  uri[1] == 'addSensor':
            # add new sensor to the self.catalog
            new_device_info = json.loads(cherrypy.request.body.read())
            print("In POST of db api", new_device_info)
             
            try:
                sensorID = new_device_info['sensorID']
                caseID = new_device_info['caseID']
                ip = new_device_info['ip']
                port = new_device_info['port']
                last_seen = new_device_info['last_seen']
                dev_name = new_device_info['dev_name']
                topics = new_device_info["topics"] # a list is sent

                for topic in topics:
                    print(f"Subscribing to topic {topic}")
                    db_connector.client_obj.subscribe(topic, qos=2)
                
                res["status"] = "ok"
                print(f"Before return")

                # MQTT client should subscribe to topic caseID/measure/sensorID

                return res

            except KeyError:
                raise cherrypy.HTTPError(400, 'Bad request')
            

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
        
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/broker_ip_outside")
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


        print("Topiche a cui DB conn è sottoscritto su accensione: ", self.topics)
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
        #TODO split on the caseID if the + does not work
        caseID, level1, level2 = message.topic.split("/")
        topic_wo_case = level1 + "/" + level2
        print("TOPIC WO CASE: ",topic_wo_case)
        if (topic_wo_case == "measure/co2"):
            print("Topic:'" + message.topic + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)
            self.sendToDB(data)

        elif (topic_wo_case == "measure/temperature"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)
            self.sendToDB(data)

        elif (topic_wo_case== "measure/humidity"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)
            self.sendToDB(data)

            
        
    def sendToDB(self, data):
        
        write_api = self.client.write_api(write_options=SYNCHRONOUS) 
        
        print("type of ",type( data["caseID"]))
        print("type of ",type( data["category"]))
        print("type of ",type( data["value"]))
        print("type of ",type( data["unit_of_measurement"]))

        p = Point(data["measurement"])\
            .tag("caseID", data["caseID"])\
            .tag("category", data["category"])\
            .tag("unit_of_measurement", data["unit_of_measurement"])\
            .field("value", data["value"])\
            .time(data["timestamp"], WritePrecision.NS) 

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

    
    # retrieve all cases in the system
    r = requests.get(f"http://{catalog_ip}:{catalog_port}/cases")
    dict_of_cases = json.loads(r.text)
    list_of_cases = [x["caseID"] for x in dict_of_cases]

    #
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

    all_topics_to_subscribe_to = []
    
    print("Connected cases id: ", list_of_cases)
    for case_id in list_of_cases:
        for topic in topics:
            case_specific_topic = case_id +"/"+ topic
            all_topics_to_subscribe_to.append(case_specific_topic)


    print("topicheeeeee: ", all_topics_to_subscribe_to)

    db_connector = DBConnectorMQTT(influx_data, all_topics_to_subscribe_to, "DB")

    db_connector.start()

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
