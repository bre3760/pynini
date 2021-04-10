import sys
import cherrypy
import json
import time
import datetime
import socket

sys.path.insert(0, "../")
HOST = "0.0.0.0"
PORT = 9090
global CATEGORY
CATEGORY = 'White'

class Catalog(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        with open("catalog2.json", 'r') as f:
            catalog = json.load(f)
            #cc = catalog['Catalog']
        if uri[0] == "broker_port":
            return json.dumps(catalog["broker_port"])
        elif uri[0] == "catalog_port":
            return json.dumps(catalog["catalog_port"])
        elif uri[0] == "category":
            return json.dumps(catalog["category"])
        elif uri[0] == "thresholds":
            return json.dumps(catalog["thresholds"])
        # elif uri[0] == "devices":
            # return json.dumps(catalog["devices"])
        elif uri[0] == "cases":
            return json.dumps(catalog["cases"])
        elif uri[0] == "activeDev":
            return json.dumps(catalog["devices"]["rpi"]["sensors"])
        elif uri[0] == "telegramBot":
            return json.dumps(catalog["telegramBot"])
        elif uri[0] == "thingspeak":
            return json.dumps(catalog["thingspeak"])
        elif uri[0] == "db":
            return json.dumps(catalog["db"])
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
                        case_ID = new_device_info['case_ID']
                        ip = new_device_info['ip']
                        port = new_device_info['port']
                        name = new_device_info['name'] # temp, hum, co2
                        last_seen = new_device_info['last_seen']
                        dev_name = new_device_info['dev_name']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    new_dev = {'ip': ip, 'port': port, 'name': name,
                               'last_seen': last_seen}

                    found = False
                    print("catalog['cases']", catalog['cases'])
                    for c in catalog['cases']:
                        if c['case_ID'] == case_ID:
                            found = True
                            for d in c[dev_name]['sensors']:
                                if d['ip'] == ip and d['name'] == name:
                                    c[dev_name]['sensors'].pop(c[dev_name]['sensors'].index(d))
                                c[dev_name]['sensors'].append(new_dev)

                    if found == False:
                        new_case = {
                                        "arduino": {
                                            "sensors": []
                                        },
                                        "bread_type": "White",
                                        "case_ID": case_ID,
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
                    print(" ASOOOOOOO catalog['topics'][name]",catalog['topics'][name])
                    res["topic"] = catalog['topics'][name]
                    res["broker_ip"] = catalog["broker_ip"]

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
                            chat_ID = new_bot_info['chat_ID']
                            ip = new_bot_info['ip']
                            last_seen = new_bot_info['last_seen']
                            #dev_name = 'rpi'
                        except KeyError:
                            f.close()
                            raise cherrypy.HTTPError(400, 'Bad request')

                        new_bot = {'chat_ID': chat_ID, 'ip': ip, 'last_seen': last_seen}

                        for d in catalog['bots']:
                            if d['chat_ID'] == chat_ID:
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
                        case_ID = new_device_info['case_ID']
                        ip = new_device_info['ip']
                        name = new_device_info['name']
                        dev_name = new_device_info['dev_name']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for c in catalog['cases']:
                        if c['case_ID'] == case_ID:
                            for d in c[dev_name]['sensors']:
                                if d['ip'] == ip and d['name'] == name:
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
                        chat_ID = new_bot_info['chat_ID']
                        print("chat_ID", chat_ID)
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for d in catalog['bots']:
                        if d['chat_ID'] == chat_ID:
                            print(d['chat_ID'], chat_ID)
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
