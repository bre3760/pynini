import sys
import cherrypy
import json
import time
import datetime
import socket

sys.path.insert(0, "../")

class Catalog(object):
    exposed = True

    def __init__(self, config_data):
        self.catalog = config_data
        pass

    def GET(self, *uri, **params):
        if uri[0] == "active_arduino":
            active_arduino = []
            for d in self.catalog['cases']:
                for s in d["arduino"]["sensors"]:
                    active_arduino.append(s["name"])
            return json.dumps(active_arduino)
        elif uri[0] == "breadCategories":
            return json.dumps(self.catalog["breadCategories"])
        elif uri[0] == "broker_ip":
            return json.dumps(self.catalog["broker_ip"])
        elif uri[0] == "broker_ip_outside":
            return json.dumps(self.catalog["broker_ip_outside"])
        elif uri[0] == "broker_port":
            return json.dumps(self.catalog["broker_port"])
        elif uri[0] == "cases":
            return json.dumps(self.catalog["cases"])
        elif uri[0] == "catalog_port":
            return json.dumps(self.catalog["catalog_port"])
        elif uri[0] == "category": 
            res = []
            for d in self.catalog['cases']:
                if d['caseID'] == params['caseID']:
                    res = d["bread_type"]
            return json.dumps(res)
        elif uri[0] == "db":
            return json.dumps(self.catalog["db"])
        elif uri[0] == "freeboard":
            return json.dumps(self.catalog["freeboard"])
        elif uri[0] == "InfluxDB":
            return json.dumps(self.catalog["InfluxDB"])
        elif uri[0] == "telegramBot":
            return json.dumps(self.catalog["telegramBot"])
        elif uri[0] == "thingspeak":
            return json.dumps(self.catalog["thingspeak"])
        elif uri[0] == "thresholds":
            return json.dumps(self.catalog["thresholds"])
        elif uri[0] == "topics":
            return json.dumps(self.catalog["topics"])
        elif uri[0] == "stats":
            return json.dumps(self.catalog["stats"])

        elif uri[0] == "getBest":
            res = []
            for d in self.catalog['thresholds']:
                if d['type'] == params['category']:
                    res = d[params['sensor']]
            return json.dumps(res)
        elif uri[0] == "getLink":
            return json.dumps(self.catalog["links"][params['category']])


    def POST(self, *uri, **params):
        res = {}
        if len(uri) == 1 and uri[0] == 'addSensor':
            # add new sensor to the self.catalog
            new_device_info = json.loads(cherrypy.request.body.read())
            print("cherrypy.request.body.read()", new_device_info)
             
            try:
                sensorID = new_device_info['sensorID']
                caseID = new_device_info['caseID']
                ip = new_device_info['ip']
                port = new_device_info['port']
                last_seen = new_device_info['last_seen']
                dev_name = new_device_info['dev_name']
            except KeyError:
                raise cherrypy.HTTPError(400, 'Bad request')

            new_dev = {'ip': ip, 'port': port, 'name': sensorID,
                        'last_seen': last_seen}

            found = False
            # check if in the catalog there is already a sensor in the same caseID with the same name: 
            # in this case the old one is removed and the new one is stored, updating the field called "last updated"
            for c in self.catalog['cases']:
                if c['caseID'] == caseID:
                    found = True
                    if c[dev_name]['sensors'] == []:
                        c[dev_name]['sensors'].append(new_dev)
                    else:
                        for d in c[dev_name]['sensors']:
                            print("d", d)
                            if d['name'] == sensorID:
                                c[dev_name]['sensors'].pop(c[dev_name]['sensors'].index(d))
                            c[dev_name]['sensors'].append(new_dev)

            if found == False:
                new_case = {
                            "arduino": {
                                "sensors": []
                            },
                            "bread_type": "White",
                            "caseID": caseID,
                            "rpi": {
                                "sensors": []
                            }
                            }
                new_case[dev_name]["sensors"].append(new_dev)
                self.catalog['cases'].append(new_case)

            self.catalog['last_updated'] = time.time()
            self.catalog.seek(0)
            self.catalog.write(json.dumps(self.catalog, indent=4, sort_keys=True))
            self.catalog.truncate()
            print(f'${new_dev["name"]} - added to the self.catalog')

            try: 
                print("catalog['topics'][name]", self.catalog['topics'][sensorID])
                res["topic"] = self.catalog['topics'][sensorID]
                res["broker_ip"] = self.catalog["broker_ip"]
                res["broker_ip_outside"] = self.catalog["broker_ip_outside"]
                res["breadCategories"] = self.catalog["breadCategories"]
                print("res[topic]", res['topic'])
                return json.dumps(res)
            except:
                print('No topic found for this sensor')
                raise cherrypy.HTTPError(404, 'No topic found for this sensor')

            #except KeyError:
            #    raise cherrypy.HTTPError(404, 'The self.catalog file was not found')

        if len(uri) == 1 and uri[0] == 'addBot':
                # add TelegramBot to the self.catalog
                new_bot_info = json.loads(cherrypy.request.body.read())
                print("cherrypy.request.body.read()", new_bot_info)
                try:
                    chatID = new_bot_info['chat_ID']
                    ip = new_bot_info['ip']
                    last_seen = new_bot_info['last_seen']
                    #dev_name = 'rpi'
                except KeyError:
                    raise cherrypy.HTTPError(400, 'Bad request')

                new_bot = {'chat_ID': chatID, 'ip': ip, 'last_seen': last_seen}

                for d in self.catalog['bots']:
                    if d['chat_ID'] == chatID:
                        self.catalog['bots'].pop(self.catalog['bots'].index(d))

                self.catalog['bots'].append(new_bot)
                self.catalog['last_updated'] = time.time()
                self.catalog.seek(0)
                self.catalog.write(json.dumps(self.catalog, indent=4, sort_keys=True))
                self.catalog.truncate()
                print(f'${new_bot["chat_ID"]} - added to the self.catalog')

                #except KeyError:
                #   raise cherrypy.HTTPError(404, 'The self.catalog file was not found')
        

        if len(uri) == 1 and uri[0] == 'setThresholds':
            # to modify the thresholds of the different bread typology 
            # try:
            #     with open('catalog2.json', 'r+') as f:
            #         self.catalog = json.load(f)
            new_threshold_info = json.loads(cherrypy.request.body.read())

            try:
                type = new_threshold_info['type']
                min_T_th = new_threshold_info['min_temperature_th']
                min_hum_th = new_threshold_info['min_humidity_th']
                min_co2_th = new_threshold_info['min_co2_th']
                max_T_th = new_threshold_info['max_temperature_th']
                max_co2_th = new_threshold_info['max_co2_th']
                max_hum_th = new_threshold_info['max_humidity_th']
            except KeyError:
                
                raise cherrypy.HTTPError(400, 'Bad request')

            new_th = {
                "type": type,
                "min_temperature_th": min_T_th,
                "min_humidity_th": min_hum_th,
                "min_co2_th": min_co2_th,
                "max_temperature_th": max_T_th,
                "max_humidity_th": max_hum_th,
                "max_co2_th": max_co2_th
            }

            print("new_tresh", new_th)
            for d in self.catalog['thresholds']:
                print(d)
                if d['type'] == type:
                    print("comparison", d['type'], type)
                    self.catalog['thresholds'].pop(self.catalog['thresholds'].index(d))

            self.catalog['thresholds'].append(new_th)
            self.catalog.seek(0)
            self.catalog.write(json.dumps(self.catalog, indent=4, sort_keys=True))
            self.catalog.truncate()
            print(f'${new_th["type"]} - modify in the self.catalog')
            return 'self.catalog file successfully written'
            # except KeyError:
            #     raise cherrypy.HTTPError(404, 'The self.catalog file was not found')

        if len(uri) == 1 and uri[0] == 'setBreadtype':
            # to set the bread typology
            # try:
            #     with open('catalog2.json', 'r+') as f:
            #         self.catalog = json.load(f)
            new_breadtype = json.loads(cherrypy.request.body.read())

            try:
                breadtype = new_breadtype['breadtype']
                caseID = new_breadtype['caseID']
                
            except KeyError:
                # f.close()
                raise cherrypy.HTTPError(400, 'Bad request')

            print("new_breadtype", new_breadtype)
            for d in self.catalog['cases']:
                if d['caseID'] == caseID:
                    d["bread_type"] = breadtype
            print([i['bread_type'] for i in self.catalog['cases']])
            self.catalog.seek(0)
            self.catalog.write(json.dumps(self.catalog, indent=4, sort_keys=True))
            self.catalog.truncate()
            print(f'${new_breadtype["breadtype"]} - modify in the self.catalog')
            return 'self.catalog file successfully written'
            # except KeyError:
            #     raise cherrypy.HTTPError(404, 'The self.catalog file was not found')
    
        if len(uri) == 1 and uri[0] == 'removeSensor':
            # remove the sensor from the self.catalog
            new_device_info = json.loads(cherrypy.request.body.read())
            print("cherrypy.request.body.read()", new_device_info)
           
            try:
                caseID = new_device_info['caseID']
                name = new_device_info['name']
                dev_name = new_device_info['dev_name']
            except KeyError:
                raise cherrypy.HTTPError(400, 'Bad request')

            found = False
            for c in self.catalog['cases']:
                if c['caseID'] == caseID:
                    for d in c[dev_name]['sensors']:
                        if d['name'] == name:
                            c[dev_name]['sensors'].pop(c[dev_name]['sensors'].index(d))
                            print("Sensor deleted successfully")
                            found = True

            if found is False:
                f.close()
                raise cherrypy.HTTPError(404, "Device not found")

            self.catalog['last_updated'] = time.time()
            self.catalog.seek(0)
            self.catalog.write(json.dumps(self.catalog, indent=4, sort_keys=True))
            self.catalog.truncate()
            return 'catalog file successfully written'

        if len(uri) == 1 and uri[0] == 'removeBot':
            # remove the Telegram Bot from the self.catalog
            new_bot_info = json.loads(cherrypy.request.body.read())
            print("new_bot_info", new_bot_info)
           
            try:
                chat_ID = new_bot_info['chat_ID']
                print("chat_ID", chat_ID)
            except KeyError:
                f.close()
                raise cherrypy.HTTPError(400, 'Bad request')

            found = False
            for d in self.catalog['bots']:
                if d['chat_ID'] == chat_ID:
                    print(d['chat_ID'], chat_ID)
                    self.catalog['bots'].pop(self.catalog['bots'].index(d))
                    found = True

            if found is False:
                raise cherrypy.HTTPError(404, "Device not found")

            self.catalog['last_updated'] = time.time()
            self.catalog.seek(0)
            self.catalog.write(json.dumps(self.catalog, indent=4, sort_keys=True))
            self.catalog.truncate()
            #f.close()
            return 'catalog file successfully written'
 

    def PUT(self, *uri, **params):
        if len(uri) == 1 and uri[0] == 'setThresholds':

            new_threshold_info = json.loads(cherrypy.request.body.read())

            try:
                type = new_threshold_info['type']
                min_T_th = new_threshold_info['min_temperature_th']
                min_hum_th = new_threshold_info['min_humidity_th']
                min_co2_th = new_threshold_info['min_co2_th']
                max_T_th = new_threshold_info['max_temperature_th']
                max_co2_th = new_threshold_info['max_co2_th']
                max_hum_th = new_threshold_info['max_humidity_th']
            except KeyError:
                raise cherrypy.HTTPError(400, 'Bad request')

            new_th = {
                "type": type,
                "min_temperature_th": min_T_th,
                "min_humidity_th": min_hum_th,
                "min_co2_th": min_co2_th,
                "max_temperature_th": max_T_th,
                "max_humidity_th": max_hum_th,
                "max_co2_th": max_co2_th
            }

            print("new_tresh", new_th)
            for d in self.catalog['thresholds']:
                print(d)
                if d['type'] == type:
                    print("comparison", d['type'], type)
                    self.catalog['thresholds'].pop(self.catalog['thresholds'].index(d))

            self.catalog['thresholds'].append(new_th)
            self.catalog.seek(0)
            self.catalog.write(json.dumps(self.catalog, indent=4, sort_keys=True))
            self.catalog.truncate()
            
            print(f'${new_th["type"]} - modify in the self.catalog')
            return 'catalog file successfully written'

if __name__ == '__main__':

    with open("catalog2.json", 'r') as f:
        config = json.load(f)
    catalog_ip = config['catalog_ip']
    catalog_port = config['catalog_port']

    catalog = Catalog(config_data=config)

    

    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.tree.mount(catalog, '/', conf)
    cherrypy.server.socket_host = catalog_ip
    cherrypy.server.socket_port = catalog_port
    cherrypy.engine.start()
