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
        start = "1970-01-01T00:00:00Z"
        stop = "2021-06-16T17:40:00Z"
        self.client.delete_api().delete(start, stop, '_measurement="statistics"', bucket=self.bucket, org=self.org)

    def write(self, data):
        self.counter += 1
        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        #date, number sold white, number sold wheat, number sold glutenfree 
        p = Point("statistics").tag("date",  data["date"])\
            .field("qnt_sold_white", data["qnt_sold_white"])\
            .field("qnt_sold_wheat", data["qnt_sold_wheat"])\
            .field("qnt_sold_glutenfree", data["qnt_sold_glutenfree"])\
            .field("price_white", data["price_white"])\
            .field("price_wheat", data["price_wheat"])\
            .field("price_glutenfree", data["price_glutenfree"])
        # p = Point(data["statistics"])\
        #     .tag("date", data["date"])\
        #     .tag("qnt_sold_white", data["qnt_sold_white"])\
        #     .tag("qnt_sold_wheat", data["qnt_sold_wheat"])\
        #     .tag("qnt_sold_glutenfree", data["qnt_sold_glutenfree"])\
        #     .tag("price_white", data["price_white"])\
        #     .tag("price_wheat", data["price_wheat"])\
        #     .tag("price_glutenfree", data["price_glutenfree"]).\
        #     field("value", data.index())
        write_api.write(self.bucket, self.org, record=p)

        write_api.close()

    
        
