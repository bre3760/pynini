from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import json
import pandas as pd

class InfluxDB():
    def __init__(self, data):
        self.url = data['url']
        self.token = data['token']
        self.bucket = data['bucket']
        self.org = "s272608@studenti.polito.it"
        self.counter = 0
        print("self: ",self.url, self.token, self.org, self.bucket)

        self.client = InfluxDBClient(
            self.url,
            self.token,
            self.org
        )

    def clean(self):
        print("cleaning")
        start = "1970-01-01T00:00:00Z"
        stop = "2021-06-18T20:00:00Z"
        self.client.delete_api().delete(start, stop, '_measurement="qnt_sold_white"', bucket=self.bucket, org=self.org)
        self.client.delete_api().delete(start, stop, '_measurement="sold"', bucket=self.bucket, org=self.org)

    def write(self, data):
        self.counter += 1
        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        # data(measurements):  statistics
        # all : {'measurement': 'statistics', 'caseID': 'CCC2', 'date': '2020-01-07 00:00:00', 'qnt_sold_white': 134.3840279612282, 'qnt_sold_wheat': 139.51923131000075, 'qnt_sold_glutenfree': 65.40952906091167, 'price_white': 1.043666011339177, 'price_wheat': 2.4199700282781307, 'price_glutenfree': 2.8194173884965275}

        #date, number sold white, number sold wheat, number sold glutenfree 
        # json_body = {
        #     "measurement": "statistics",
        #     "tags": {"qnt_sold_white": data["qnt_sold_white"]},
        #     "fields": {"qnt_sold_white": data["qnt_sold_white"]}, 
        #     "time": data["date"]}
        # write_api.write(self.bucket, self.org, [json_body])
        #print("data(measurements): ", data["measurement"])
        print("\n")
        print("all :", data)

        p = Point('sold')\
            .field("value", data["qnt_sold_white"])\
            .tag("date", data["date"])
            
        write_api.write(self.bucket, self.org, record=p)

        write_api.close()


# test when you want to delete db
# # # retrieve data needed to access InfluxDB
# dataInfluxDB = requests.get(f"http://0.0.0.0:9090/InfluxDB")
# influxDB = InfluxDB(json.loads(dataInfluxDB.text))
# influxDB.clean()

        
