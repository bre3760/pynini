import sys
import cherrypy
import json
import time
import datetime
import socket

sys.path.insert(0, "../")

class Catalog(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        with open("catalog2.json", 'r') as f:
            catalog = json.load(f)
        if uri[0] == "active_arduino":
            active_arduino = []
            for d in catalog['cases']:
                for s in d["arduino"]["sensors"]:
                    active_arduino.append(s["name"])
            return json.dumps(active_arduino)
        elif uri[0] == "breadCategories":
            return json.dumps(catalog["breadCategories"])
        elif uri[0] == "broker_ip":
            return json.dumps(catalog["broker_ip"])
        elif uri[0] == "broker_ip_outside":
            return json.dumps(catalog["broker_ip_outside"])
        elif uri[0] == "broker_port":
            return json.dumps(catalog["broker_port"])
        elif uri[0] == "cases":
            return json.dumps(catalog["cases"])
        elif uri[0] == "catalog_port":
            return json.dumps(catalog["catalog_port"])
        elif uri[0] == "category": # cat
            res = []
            for d in catalog['cases']:
                if d['caseID'] == params['caseID']:
                    res = d["bread_type"]
            return json.dumps(res)
        elif uri[0] == "db":
            return json.dumps(catalog["db"])
        elif uri[0] == "freeboard":
            return json.dumps(catalog["freeboard"])
        elif uri[0] == "InfluxDB":
            return json.dumps(catalog["InfluxDB"])
        elif uri[0] == "telegramBot":
            return json.dumps(catalog["telegramBot"])
        elif uri[0] == "thingspeak":
            return json.dumps(catalog["thingspeak"])
        elif uri[0] == "thresholds":
            return json.dumps(catalog["thresholds"])
        elif uri[0] == "topics":
            return json.dumps(catalog["topics"])


    def POST(self, *uri, **params):
        res = {}
        if len(uri) == 1 and uri[0] == 'addSensor':
            new_device_info = json.loads(cherrypy.request.body.read())
            print("cherrypy.request.body.read()", new_device_info)
            try:
                with open('catalog2.json', 'r+') as f:
                    catalog = json.load(f)
                    try:
                        sensorID = new_device_info['sensorID']
                        caseID = new_device_info['caseID']
                        ip = new_device_info['ip']
                        port = new_device_info['port']
                        last_seen = new_device_info['last_seen']
                        dev_name = new_device_info['dev_name']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    new_dev = {'ip': ip, 'port': port, 'name': sensorID,
                               'last_seen': last_seen}

                    found = False
                    for c in catalog['cases']:
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
                        catalog['cases'].append(new_case)

                    catalog['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    print(f'${new_dev["name"]} - added to the catalog')
                    print("catalog['topics'][name]",catalog['topics'][sensorID])
                    res["topic"] = catalog['topics'][sensorID]
                    res["broker_ip"] = catalog["broker_ip"]
                    res["breadCategories"] = catalog["breadCategories"]

                    print("res[topic]", res['topic'])

                    return json.dumps(res)

            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'addBot':
                new_bot_info = json.loads(cherrypy.request.body.read())
                print("cherrypy.request.body.read()", new_bot_info)
                try:
                    with open('catalog2.json', 'r+') as f:
                        catalog = json.load(f)
                        try:
                            chatID = new_bot_info['chat_ID']
                            ip = new_bot_info['ip']
                            last_seen = new_bot_info['last_seen']
                            #dev_name = 'rpi'
                        except KeyError:
                            f.close()
                            raise cherrypy.HTTPError(400, 'Bad request')

                        new_bot = {'chat_ID': chatID, 'ip': ip, 'last_seen': last_seen}

                        for d in catalog['bots']:
                            if d['chat_ID'] == chatID:
                                catalog['bots'].pop(catalog['bots'].index(d))

                        catalog['bots'].append(new_bot)
                        print("sono dentro ciclo for, ho aggiunto")
                        catalog['last_updated'] = time.time()
                        f.seek(0)
                        f.write(json.dumps(catalog, indent=4, sort_keys=True))
                        f.truncate()
                        f.close()
                        print(f'${new_bot["chat_ID"]} - added to the catalog')

                except KeyError:
                    raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'removeSensor':
            new_device_info = json.loads(cherrypy.request.body.read())
            print("cherrypy.request.body.read()", new_device_info)
            try:
                with open('catalog2.json', 'r+') as f:
                    catalog = json.load(f)
                    try:
                        caseID = new_device_info['caseID']
                        name = new_device_info['name']
                        dev_name = new_device_info['dev_name']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for c in catalog['cases']:
                        if c['caseID'] == caseID:
                            for d in c[dev_name]['sensors']:
                                if d['name'] == name:
                                    c[dev_name]['sensors'].pop(c[dev_name]['sensors'].index(d))
                                    print("ho trovato ed eliminato il sensore")
                                    found = True

                    if found is False:
                        f.close()
                        raise cherrypy.HTTPError(404, "Device not found")

                    catalog['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'removeBot':
            new_bot_info = json.loads(cherrypy.request.body.read())
            print("new_bot_info", new_bot_info)
            try:
                with open('catalog2.json', 'r+') as f:
                    catalog = json.load(f)
                    try:
                        chatID = new_bot_info['chatID']
                        print("chatID", chatID)
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for d in catalog['bots']:
                        if d['chatID'] == chat_ID:
                            print(d['chatID'], chat_ID)
                            catalog['bots'].pop(catalog['bots'].index(d))
                            found = True

                    if found is False:
                        f.close()
                        raise cherrypy.HTTPError(404, "Device not found")

                    catalog['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'setThresholds':
            try:
                with open('catalog2.json', 'r+') as f:
                    catalog = json.load(f)
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
                        f.close()
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
                    for d in catalog['thresholds']:
                        print(d)
                        if d['type'] == type:
                            print("comparison", d['type'], type)
                            catalog['thresholds'].pop(catalog['thresholds'].index(d))

                    catalog['thresholds'].append(new_th)
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    print(f'${new_th["type"]} - modify in the catalog')
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'setBreadtype':
            try:
                with open('catalog2.json', 'r+') as f:
                    catalog = json.load(f)
                    new_breadtype = json.loads(cherrypy.request.body.read())

                    try:
                        breadtype = new_breadtype['breadtype']
                        caseID = new_breadtype['caseID']
                        
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    print("new_breadtype", new_breadtype)
                    for d in catalog['cases']:
                        if d['caseID'] == caseID:
                           d["bread_type"] = breadtype
                           #print(breadtype+'AAAAAAAAAAAAAAAAAAAAAAAA')
                    print([i['bread_type'] for i in catalog['cases']])
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    print(f'${new_breadtype["breadtype"]} - modify in the catalog')
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')


    def PUT(self, *uri, **params):
        if len(uri) == 1 and uri[0] == 'setThresholds':
            try:
                with open('catalog2.json', 'r+') as f:
                    catalog = json.load(f)
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
                        f.close()
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
                    for d in catalog['thresholds']:
                        print(d)
                        if d['type'] == type:
                            print("comparison", d['type'], type)
                            catalog['thresholds'].pop(catalog['thresholds'].index(d))

                    catalog['thresholds'].append(new_th)
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    print(f'${new_th["type"]} - modify in the catalog')
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')


if __name__ == '__main__':
    catalog = Catalog()

    with open("catalog2.json", 'r') as f:
        config = json.load(f)
    HOST = config['HOST']
    PORT = config['PORT']
    

    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.tree.mount(catalog, '/', conf)
    cherrypy.server.socket_host = HOST
    cherrypy.server.socket_port = PORT
    cherrypy.engine.start()
