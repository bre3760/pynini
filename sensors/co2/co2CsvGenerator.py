import pandas as pd
import random

df = pd.DataFrame()
values = []

i = 0
while i < 40: #144 per simulare 1 gg
    v = random.uniform(0.5, 5)
    values.append(v)
    i += 1

i = 0
while i < 5: #144 per simulare 1 gg
    v = random.uniform(5, 7)
    values.append(v)
    i += 1

i = 0
while i < 100: 
    v = random.uniform(0.5, 5)
    values.append(v)
    i += 1

df['value'] = values

print(df.head())

df.to_csv('co2.csv', index=False)

df=pd.read_csv('co2.csv', sep=',', decimal=',', index_col=0)
#print(df.head())

df.index=pd.to_datetime(df.index,unit='s')

for i in df.index:
    for j in df.loc[i].items():
        print(i,j[1])

