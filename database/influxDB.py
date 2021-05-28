from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import json
import pandas as pd

token = "m--UwwUcp-7FJffZeWJO2XbJ84XfIKjg1kSzgHPsPF92ffajo4ipGR9bSVeDfKZrG9Pwl158FFqC9V42baUxGw=="
tokenPynini = "jgQI1omy9-K1AbNCqtWLJi_f3sx4QwLjULypPMPNpAdRRlTDf8musUMpwQitkPwXEr1Ht62O-1-a_DVJyYE5Hg=="
bucket = "Pynini"
url = "https://eu-central-1-1.aws.cloud2.influxdata.com"
#hi
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
        # devo inserire nel db i best value di co2, temp e hum per ciascuna categoria ed il link Google
        # bestdf = pd.DataFrame({'category': ["White", "Wheat", "Gluten-free", "Cereals"],
        #                       'co2': [2.35, 2.75, 3.10, 1.80],
        #                        'temperature': [28, 30, 27, 32],
        #                        'humidity': [32, 33, 31, 34]})
        # bestdf.set_index('category', inplace=True)
        # print("BESTDF", bestdf)

        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        white = Point("best").tag("category", "White").field("co2", 2.01).field("temperature", 28).field("humidity", 33).field("info", "https://www.allrecipes.com/recipe/20066/traditional-white-bread/")
        wheat = Point("best").tag("category", "Wheat").field("co2", 2.75).field("temperature", 30).field("humidity", 31).field("info", "https://bakingamoment.com/soft-whole-wheat-bread/")
        glutenfree = Point("best").tag("category", "Glutenfree").field("co2", 1.95).field("temperature", 27).field("humidity", 32).field("info", "https://www.glutenfreepalate.com/gluten-free-bread-recipe/")
        write_api.write(self.bucket, self.org, record=[white, wheat, glutenfree])

    def freeboard(self):

        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        pieChart = Point("freeboard").tag("category", "Freeboard").field("link", "127.0.0.1:8080")
        write_api.write(self.bucket, self.org, record=pieChart)


    def clean(self):
        start = "1970-01-01T00:00:00Z"
        stop = "2021-04-17T14:57:00Z"
        self.client.delete_api().delete(start, stop, '_measurement="best"', bucket=self.bucket, org=self.org)

    def write(self, data):
        self.counter += 1
        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        # p = Point(data["measurement"]).tag("category", data["category"]).field("value", data["value"]).field("uniq", self.counter).time(datetime.utcnow(), WritePrecision.NS)
        # da provare quando più sensori inseriscono dati in influxdb contemporaneamente -> in teoria dovrebbe incazzarsi e volere il campo uniq
        # avendo più field, la funzione get_field() ritorna per ogni entry tutti i fields
        p = Point(data["measurement"]).tag("caseID", data["caseID"]).tag("category", data["category"]).field("value", data["value"]).field("uniq", self.counter).time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(self.bucket, self.org, record=p)

        write_api.close()
        #tag are indexed while field are not

if __name__ == "__main__":

    data = requests.get("http://localhost:9090/InfluxDB")
    mydb = InfluxDB(json.loads(data.text))
    mydb.best()
    mydb.freeboard()
