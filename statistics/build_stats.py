import random 
import pandas as pd
from datetime import datetime, timedelta
from influxDB import InfluxDB
import requests
import json
from datetime import timedelta
"""
script that creates the history of purchases for different bread types
the dataframe has the following structure
# date, number sold white, number sold wheat, number sold glutenfree
unit of measurement: €/kg
"""
year = 2020
days = []
white = []
wheat = []
glutenfree = []
price_white = []
price_wheat = []
price_glutenfree = []

startTime = "2020-01-01 0:0:0"
for i in range(0,365):
    if i == 0:
       time = datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
    else:
        time = days[-1] + timedelta(days=1)
        # cerca quanto vale un giorno in unixtime
        # datetime + timedelta(1)
    days.append(time)
    white.append(random.uniform(100, 250))
    wheat.append(random.uniform(50, 150))
    glutenfree.append(random.uniform(20, 100))

    price_white.append(random.uniform(1, 3))
    price_wheat.append(random.uniform(1, 4))
    price_glutenfree.append(random.uniform(1.5, 5.5))


purchaseDF = pd.DataFrame()
purchaseDF["date"] = days
purchaseDF["qnt_sold_white"] = white 
purchaseDF["qnt_sold_wheat"] = wheat
purchaseDF["qnt_sold_glutenfree"] = glutenfree
purchaseDF["price_white"] = price_white
purchaseDF["price_wheat"] = price_wheat
purchaseDF["price_glutenfree"] = price_glutenfree

purchaseDF.to_csv("purchase_history.csv")

with open("config.json", 'r') as f:
		config = json.load(f)
		catalog_ip = config['catalog_ip']
		catalog_port = config['catalog_port']

# retrieve data needed to access InfluxDB
dataInfluxDB = requests.get(f"http://{catalog_ip}:{catalog_port}/InfluxDB")
influxDB = InfluxDB(json.loads(dataInfluxDB.text))

# create a dict in which collect day, quantity of bread sold and price of each typology
data = {}
for index, row in purchaseDF.iterrows():
    data['statistics'] = 'statistics'
    data['date'] = row['date']
    data['qnt_sold_white'] = row['qnt_sold_white']
    data['qnt_sold_wheat'] = row['qnt_sold_wheat']
    data['qnt_sold_glutenfree'] = row['qnt_sold_glutenfree']
    data['price_white'] = row['price_white']
    data['price_wheat'] = row['price_wheat']
    data['price_glutenfree'] = row['price_glutenfree']
    # store data into InfluxDB
    influxDB.write(data)