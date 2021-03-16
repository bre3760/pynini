import paho.mqtt.client as mqtt
import json, time, datetime
import requests

file = open("configFile.json", "r")
jsonString = file.read()
file.close()
data = json.loads(jsonString)
url = data["resourceCatalog"]["url"]
channel = data["resourceCatalog"]["channel"]
write_key = data["resourceCatalog"]["write_key"]
broker_address = data["resourceCatalog"]["broker_address"]
port1 = data["resourceCatalog"]["port1"]
port2 = data["resourceCatalog"]["port2"]
name = data["resourceCatalog"]["name"]


class ThingSpeakConnector():

    def __init__(self):

        global name
        global channel
        global url
        global write_key
        global broker_address

        self.pynini = name
        self.channel = channel
        self.write_key = write_key
        self.ID = self.pynini + "_TS-Adaptor"
        self.type = "TS-Adaptor"

        self.broker_address = broker_address

        self.client_obj = mqtt.Client(self.ID)

        self.isSubscriber = True
        self.isPublisher = False

        self.field1_data = None  # co2
        self.timestamp = None
        #self.field2_data = None  # temperature
        #self.field3_data = None  # humidity

        self.client_obj.on_connect = self.connect_callback
        self.client_obj.on_message = self.message_callback

    # device starting
    def start(self):

        global port1
        global port2

        self.client_obj.connect(self.broker_address, int(port1), int(port2))
        self.client_obj.loop_start()

        self.client_obj.subscribe("co2", qos=1)  # subscribe to know co2
        #self.client_obj.subscribe("temperature", qos=1)  # subscribe to know temperature
        #self.client_obj.subscribe("humidity", qos=1)  # subscribe to know humidity

    # device stopping
    def stop(self):
        self.client_obj.unsubscribe("co2")
        #self.client_obj.unsubscribe("temperature")
        #self.client_obj.unsubscribe("humidity")
        self.client_obj.disconnect()
        print("Mi sono disconnesso")

    # callback for connection
    def connect_callback(self, client, userdata, flags, rc):
        if rc == 0:
            print("%s connected to broker %s." % (self.ID, self.broker_address))
            rc = 1

    # callback for messages
    def message_callback(self, client, userdata, message):
        if (message.topic == "co2"):
            print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(message.payload) + "'")
            data = json.loads(message.payload)
            json_body = [
                {
                    "measurement": data['measurement'],
                    "time": data['time_stamp'],
                    "fields":
                        {
                            "value": data['value']
                        }
                }
            ]
            self.field1_data = data['value']
            self.timestamp = data['time_stamp']

            # elif (message.topic == "temperature"):
            #     print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(
            #         message.payload) + "'")
            #     data = json.loads(message.payload)
            #     json_body = [
            #         {
            #             "measurement": data['measurement'],
            #             "time": data['time_stamp'],
            #             "fields":
            #                 {
            #                     "value": data['value']
            #                 }
            #         }
            #     ]
            #     self.field2_data = data['value']
            #     self.timestamp = data['time_stamp']

            # elif (message.topic == "humidity"):
            #     print("Topic:'" + message.topic + "', QoS: '" + str(message.qos) + "' Message: '" + str(
            #         message.payload) + "'")
            #     data = json.loads(message.payload)
            #     json_body = [
            #         {
            #             "measurement": data['measurement'],
            #             "time": data['time_stamp'],
            #             "fields":
            #                 {
            #                     "value": data['value']
            #                 }
            #         }
            #     ]
            #     self.field3_data = data['value']
            #     self.timestamp = data['time_stamp']


# main function

headers = {'Content-type': 'application/json', 'Accept': 'raw'}
#cnt = 1

tsa = ThingSpeakConnector()
tsa.start()

t = 0
while t < 500:
    data_upload_json = json.dumps({"api_key": tsa.write_key,
                                   "channel_id": tsa.channel,
                                   #"created_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                   #"entry_id": cnt,
                                   "created_at": tsa.timestamp,
                                   "field1": tsa.field1_data,
                                   #"field2": tsa.field2_data
                                   })

    print(tsa.field1_data)
    if (tsa.field1_data != None):
    #if (tsa.field1_data != None or tsa.field2_data != None):
        print("Publishing on TS:", data_upload_json)
        requests.post(url=url, data=data_upload_json, headers=headers)

    tsa.field1_data = None  # users
    #tsa.field2_data = None  # items

    time.sleep(10)  # check for updates every 30sec
    #cnt += 1  # update the entry id
    t += 1

tsa.stop()