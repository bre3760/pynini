import paho.mqtt.client as mqtt
import json, time, datetime
import requests

class ThingSpeakConnector:

    def __init__(self, r, topics, headers):
        self.headers = headers
        self.pynini = json.loads(r.text)["name"]
        self.channel = json.loads(r.text)["channel"]
        self.write_key = json.loads(r.text)["write_key"]
        self.ID = self.pynini + "_TS-Adaptor"
        self.type = "TS-Adaptor"
        self.port1 = json.loads(r.text)["port1"]
        self.port2 = json.loads(r.text)["port2"]
        self.broker_address = json.loads(r.text)["broker_ip"]
        self.url = json.loads(r.text)["url"]
        self.topics = topics
        self.client_obj = mqtt.Client(self.ID)
        self.isSubscriber = True
        self.isPublisher = False
        self.field1_data = None  # co2
        self.timestamp = None
        self.field2_data = None  # temperature
        self.field3_data = None  # humidity

        self.client_obj.on_connect = self.connect_callback
        self.client_obj.on_message = self.message_callback


    # device starting
    def start(self):
        self.client_obj.username_pw_set(username="brendan", password="pynini")
        self.client_obj.connect(self.broker_address, int(self.port1), int(self.port2))
        self.client_obj.loop_start()

        for topic in self.topics:
            self.client_obj.subscribe(topic, qos=1)


    # device stopping
    def stop(self):
        for topic in self.topics:
            self.client_obj.unsubscribe(topic)
        self.client_obj.disconnect()
        print("Mi sono disconnesso")

    # callback for connection
    def connect_callback(self, client, userdata, flags, rc):
        if rc == 0:
            print("%s connected to broker %s." % (self.ID, self.broker_address))
            rc = 1

    # callback for messages
    def message_callback(self, client, userdata, message):
        if (message.topic == "measure/co2"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)

            self.field1_data = data['value']
            self.timestamp = data['timestamp']

            data_upload_json = json.dumps({ "api_key": self.write_key,
                                "channel_id": self.field3_data ,
                                "field1": self.field1_data
                                })


            if (self.field1_data != None):
                print("Publishing on TS _ co2:", data_upload_json)
                requests.post(url=self.url, data=data_upload_json, headers=self.headers)

        elif (message.topic == "measure/temperature"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(
                message.payload) + "'")
            data = json.loads(message.payload)

            self.field2_data = data['value']
            self.timestamp = data['timestamp']
            data_upload_json = json.dumps({ "api_key": self.write_key,
                                            "channel_id": self.field3_data ,
                                            "field2": self.field2_data
                                            })
            if (self.field2_data != None):
                print("Publishing on TS _ temp:", data_upload_json)
                requests.post(url=self.url, data=data_upload_json, headers=self.headers)

        elif (message.topic == "measure/humidity"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(
                message.payload) + "'")
            data = json.loads(message.payload)

            self.field3_data = data['value']
            self.timestamp = data['timestamp']

            data_upload_json = json.dumps({ "api_key": self.write_key,
                                            "channel_id": self.field3_data ,
                                            "field3": self.field3_data
                                            })

            if (self.field3_data != None):
                print("Publishing on TS _ humidity:", data_upload_json)
                requests.post(url=self.url, data=data_upload_json, headers=self.headers)

# main function
if __name__ == '__main__':
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'raw'}
        topics = []

        with open("config.json", 'r') as thingspeak_f:
            dict_config = json.load(thingspeak_f)
            catalog_ip = dict_config['catalog_ip']
            catalog_port = dict_config['catalog_port']

        data = requests.get(f"http://{catalog_ip}:{catalog_port}/thingspeak")
        r = requests.get(f"http://{catalog_ip}:{catalog_port}/topics")
        dict_topics = json.loads(r.text)

        for key, value in dict_topics.items():
            if key == "TempHum" or key == "arduino":
                for k, v in value.items():
                    if v not in topics:
                        topics.append(v)
            else:
                if value not in topics:
                    topics.append(value)

        tsa = ThingSpeakConnector(data, topics, headers)
        tsa.start()

    except KeyboardInterrupt:
        tsa.stop()