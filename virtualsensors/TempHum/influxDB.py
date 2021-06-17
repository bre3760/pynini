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

    def best(self):

        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        white = Point("best").tag("category", "White").field("co2", 2.01).field("temperature", 28).field("humidity", 33).field("info", "https://www.allrecipes.com/recipe/20066/traditional-white-bread/")
        wheat = Point("best").tag("category", "Wheat").field("co2", 2.75).field("temperature", 30).field("humidity", 31).field("info", "https://bakingamoment.com/soft-whole-wheat-bread/")
        glutenfree = Point("best").tag("category", "Glutenfree").field("co2", 1.95).field("temperature", 27).field("humidity", 32).field("info", "https://www.glutenfreepalate.com/gluten-free-bread-recipe/")
        write_api.write(self.bucket, self.org, record=[white, wheat, glutenfree])

    def clean(self):
        start = "1970-01-01T00:00:00Z"
        stop = "2021-06-16T17:40:00Z"
        self.client.delete_api().delete(start, stop, '_measurement="temperature"', bucket=self.bucket, org=self.org)
        self.client.delete_api().delete(start, stop, '_measurement="humidity"', bucket=self.bucket, org=self.org)
        self.client.delete_api().delete(start, stop, '_measurement="co2"', bucket=self.bucket, org=self.org)

    def write(self, data):
        self.counter += 1
        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        p = Point(data["measurement"])\
            .tag("caseID", data["caseID"])\
            .tag("category", data["category"])\
            .tag("unit_of_measurement", data["unit_of_measurement"])\
            .field("value", data["value"])\
            .time(data["timestamp"], WritePrecision.NS) #.field("uniq", self.counter)
        write_api.write(self.bucket, self.org, record=p)

        write_api.close()
        
