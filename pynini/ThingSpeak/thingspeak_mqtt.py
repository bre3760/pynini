import paho.mqtt.client as mqtt
import json, time, datetime
import requests

# devo collegarmi alle topiche solo dei sensori attivi:
# interrogo il catalog per capire quali sono i sensori attivi

class ThingSpeakConnector:

    def __init__(self, r, topics):

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
            # json_body = [
            #     {
            #         "measurement": data['measurement'],
            #         "time": data['time_stamp'],
            #         "fields":
            #             {
            #                 "value": data['value']
            #             }
            #     }
            # ]
            self.field1_data = data['value']
            self.timestamp = data['time_stamp']

        elif (message.topic == "measure/temperature"):
             print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(
                 message.payload) + "'")
             data = json.loads(message.payload)
             # json_body = [
             #     {
             #         "measurement": data['measurement'],
             #         "time": data['time_stamp'],
             #         "fields":
             #             {
             #                 "value": data['value']
             #             }
             #     }
             # ]
             self.field2_data = data['value']
             self.timestamp = data['time_stamp']

        elif (message.topic == "measure/humidity"):
             print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(
                 message.payload) + "'")
             data = json.loads(message.payload)
             # json_body = [
             #     {
             #         "measurement": data['measurement'],
             #         "time": data['time_stamp'],
             #         "fields":
             #             {
             #                 "value": data['value']
             #             }
             #     }
             # ]
             self.field3_data = data['value']
             self.timestamp = data['time_stamp']

def dataAcquisition():
    data = requests.get("http://localhost:9090/thingspeak")
    #devices_list = requests.get("http://localhost:9090/activeDev")
    #active_devices = []
    #for dev in json.loads(devices_list.text):
    #    active_devices.append(dev['name'])
    #print(active_devices)
    active_devices = []

    return data, active_devices

# main function
if __name__ == '__main__':

    headers = {'Content-type': 'application/json', 'Accept': 'raw'}
    #cnt+=1
    topics = []
    data, active_devices = dataAcquisition()
    r = requests.get("http://localhost:9090/topics")
    #print(json.loads(r.text))
    dict_of_topics = json.loads(r.text)
    print("dict_of_topics",dict_of_topics)
    topics.append(dict_of_topics["co2"])
    topics.append(dict_of_topics['TempHum']["topic_temp"])
    topics.append(dict_of_topics['TempHum']["topic_hum"])
    tsa = ThingSpeakConnector(data, topics)
    tsa.start()

    t = 0
    while t < 500:
        data_upload_json = json.dumps({"api_key": tsa.write_key,
                                       "channel_id": tsa.channel,
                                       #"created_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                       #"entry_id": cnt,
                                       #"created_at": tsa.timestamp,
                                       "field1": tsa.field1_data, #,
                                       "field2": tsa.field2_data,
                                       "field3": tsa.field3_data
                                       })

        print(tsa.field1_data, tsa.field2_data, tsa.field3_data)
        # if (tsa.field1_data != None):
        if (tsa.field1_data != None or tsa.field2_data != None or tsa.field3_data != None):
            print("Publishing on TS:", data_upload_json)
            requests.post(url=tsa.url, data=data_upload_json, headers=headers)

        tsa.field1_data = None
        tsa.field2_data = None
        tsa.field3_data = None

        time.sleep(10)  # check for updates every 30sec
        #cnt += 1  # update the entry id
        t += 1

    tsa.stop()