import pandas as pd
import random
from datetime import datetime
from datetime import timedelta
year = 2021
month = 7
day = 1
days = []
white = []
wheat = []
glutenfree = []
price_white = []
price_wheat = []
price_glutenfree = []

# startTime = "06-17" + "-" + str(year) 
startTime = f"{day}-{month}-{year}"

"""
script that creates the history of purchases for different bread types
the dataframe has the following structure
# date, number sold white, number sold wheat, number sold glutenfree
unit of measurement: €/kg
"""
for i in range(0,30):
    if i == 0:
        # time_dt = datetime.strptime(startTime, "%m-%d-%Y")
        time_dt = datetime.strptime(startTime, "%d-%m-%Y")    
    else:
        time_dt = datetime.strptime(days[-1] , "%d-%m-%Y") + timedelta(days=1)


    days.append(time_dt.strftime("%d-%m-%Y"))
    white.append(random.uniform(100, 250))
    wheat.append(random.uniform(50, 150))
    glutenfree.append(random.uniform(20, 100))

    price_white.append(random.uniform(1, 3))
    price_wheat.append(random.uniform(1, 4))
    price_glutenfree.append(random.uniform(1.5, 5.5))




purchase_qnt_DF = pd.DataFrame()

purchase_qnt_DF["date"] = days
purchase_qnt_DF["White"] = white
purchase_qnt_DF["Wheat"] = wheat
purchase_qnt_DF["Glutenfree"] = glutenfree

purchase_qnt_DF.to_csv("purchase_qnt.csv", index=False)


purchase_prices_DF = pd.DataFrame()
purchase_prices_DF["date"] = days
purchase_prices_DF["White"] = price_white
purchase_prices_DF["Wheat"] = price_wheat
purchase_prices_DF["Glutenfree"] = price_glutenfree

purchase_prices_DF.to_csv("purchase_prices.csv", index=False)

