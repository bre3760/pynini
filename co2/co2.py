import pytz
import pandas as pd
import random
from datetime import date, datetime, timezone

startUnixTime_datetime = (datetime(2020, 10, 1, tzinfo=None))
eu = pytz.timezone('Europe/Rome')
startUnixTime_datetimeEU = eu.localize(startUnixTime_datetime)
startUnixTime = startUnixTime_datetimeEU.timestamp()

df = pd.DataFrame()
dataTime = []
values = []

i = 0
t = int(startUnixTime)
while i < 144: #144 per simulare 1 gg
    dataTime.append(t) #600 per avere un rilevamento ogni 10 min
    t += 600
    v = random.uniform(0.5, 5)
    values.append(v)
    i += 1

df['dataTime'] = dataTime
df['values'] = values

print(df.head())

df.to_csv('co2.csv', index=False)

df=pd.read_csv('co2.csv',sep=',',decimal=',',index_col=0)
#print(df.head())

df.index=pd.to_datetime(df.index,unit='s')

for i in df.index:
    for j in df.loc[i].items():
        print(i,j[1])

