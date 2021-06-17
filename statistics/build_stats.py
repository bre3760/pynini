import random 
import pandas as pd
from datetime import datetime, timedelta
from influxDB import InfluxDB
import requests
import json
from datetime import timedelta
import time
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

startTime = "2021-06-17 00:00:00"
for i in range(0,7):
    if i == 0:
        time_dt = datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")  
        print("START TIME IS: ", time_dt, type(time_dt))
    else:
        time_dt = datetime.strptime(days[-1] , "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
        print("START AFTER ZERO TIME IS: ", time_dt, type(time_dt))

    print("BEFORE ADDING TO DAYS: ",  time_dt, type(time_dt))
    print("WHAT IS ADDED TO DAYS: ", time_dt.strftime("%Y-%m-%d %H:%M:%S") , type(time_dt.strftime("%Y-%m-%d %H:%M:%S")))

    days.append(time_dt.strftime("%Y-%m-%d %H:%M:%S"))
    white.append(random.uniform(100, 250))
    wheat.append(random.uniform(50, 150))
    glutenfree.append(random.uniform(20, 100))

    price_white.append(random.uniform(1, 3))
    price_wheat.append(random.uniform(1, 4))
    price_glutenfree.append(random.uniform(1.5, 5.5))


purchaseDF = pd.DataFrame()
# purchaseDF["..."] = "..." # ti riempie la colonna per intero se il dataframe ha già una struttura
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
    data['measurement'] = 'statistics'
    data['date'] = row['date']
    data['qnt_sold_white'] = row['qnt_sold_white']
    data['qnt_sold_wheat'] = row['qnt_sold_wheat']
    data['qnt_sold_glutenfree'] = row['qnt_sold_glutenfree']
    data['price_white'] = row['price_white']
    data['price_wheat'] = row['price_wheat']
    data['price_glutenfree'] = row['price_glutenfree']
    # store data into InfluxDB


    influxDB.write(data)
