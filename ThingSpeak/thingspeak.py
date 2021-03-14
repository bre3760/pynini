import sys
import requests
import datetime
import http.client, urllib
from ThingSpeak.sensors_db import SensorsDB

db = SensorsDB()
db.start()

key = "JP1Y39DFBGLSM3FX"
key_co2 = "7FP7K9V4HN68HHTV"

db.cursor.execute('select TIMESTAMP, VALUE from co2')

# db.mydb.commit()
# db.cursor.close()
# db.mydb.close()

rows = db.cursor.fetchall()
dates = []
values = []
for element in rows:
    dates.append(element[0].isoformat()+'Z')
    values.append(element[1])
print(values)
print(dates)

#params = urllib.parse.urlencode({'field1': values, 'created_at': dates,'api_key':key})
#params = urllib.parse.urlencode({'field1': values,'api_key':key_co2})
#headers = {"Content-type": "application/x-www-form-urlencoded","Accept":"text/plain"}
URL = 'https://api.thingspeak.com/update?api_key='
headers = '&field1={}&created_at={}'.format(*values,*dates)
final_url = URL+key_co2+headers
print(final_url)
data = urllib.request.urlopen(final_url)
print(data)
#conn = http.client.HTTPConnection("api.thingspeak.com:80")

#try:
    #conn.request("GET", "/update", params, headers)
    #response = conn.getresponse()
    #print(response.status, response.reason)
    #data = response.read()
    #conn.close()
#except:
    #print("connection failed")

sys.exit()