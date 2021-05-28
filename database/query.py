from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import json

class ClientQuery():
    def __init__(self, sensor, category, caseID):
        self.sensor = sensor
        self.caseID = caseID
        self.category = category
        dataInfluxDB = requests.get("http://localhost:9090/InfluxDB")
        self.url = json.loads(dataInfluxDB.text)['url']
        self.token = json.loads(dataInfluxDB.text)['token']
        self.bucket = json.loads(dataInfluxDB.text)['bucket']
        self.org = "s272608@studenti.polito.it"
        self.counter = 0
        print("self: ",self.url, self.token, self.org, self.bucket)

        self.client = InfluxDBClient(
            self.url,
            self.token,
            self.org
        )

    def getData(self):
        query = f'from(bucket: "Pynini")|> range(start: -3d)|> filter(fn: (r) => r.caseID == "{self.caseID}") |> filter(fn: (r) => r["_measurement"] == "{self.sensor}") |> filter(fn: (r) => r.category == "{self.category}")'
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

        print("results", results, res)
        return res


    def getBest(self):
        query = f'from(bucket: "Pynini")|> range(start: -3d)|> filter(fn: (r) => r["_measurement"] == "best") |> filter(fn: (r) => r.category == "{self.category}")'
        result = self.client.query_api().query(org=self.org, query=query)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))
                if record.get_field() == 'temperature' and self.sensor == 'temperature':
                    res = int(record.get_value())
                elif record.get_field() == 'humidity' and self.sensor == 'humidity':
                    res = int(record.get_value())
                elif record.get_field() == 'co2' and self.sensor == 'co2':
                    res = int(record.get_value())
                elif record.get_field() == 'info' and self.sensor == 'info':
                    res = record.get_value()

        return res

    def getLink(self):
        query = f'from(bucket: "Pynini")|> range(start: -3d)|> filter(fn: (r) => r["_measurement"] == "best") |> filter(fn: (r) => r.category == "{self.category}")'
        result = self.client.query_api().query(org=self.org, query=query)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))
                if record.get_field() == 'info':
                    res = record.get_value()

        return res

    def getFreeboard(self):
        query = f'from(bucket: "Pynini")|> range(start: -3d)|> filter(fn: (r) => r.category == "Freeboard")'
        result = self.client.query_api().query(org=self.org, query=query)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))
                if record.get_field() == 'link':
                    res = record.get_value()

        print("resultsFreeboard", res)
        return res

    def end(self):
        self.client.close()

if __name__ == "__main__":
     c = ClientQuery('co2', 'White', 'CCC2')
     values = c.getData()
     print("getData CCC2", values)
     res = c.getBest()