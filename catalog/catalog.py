import sys
import cherrypy
import json
import time
import datetime
import socket

sys.path.insert(0, "../")
HOST = "0.0.0.0"
PORT = 9090

class Catalog(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        with open("catalog.json", 'r') as f:
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
        elif uri[0] == "devices":
            return json.dumps(catalog["devices"])
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
                with open('catalog.json', 'r+') as f:
                    catalog = json.load(f)
                    try:
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

                    # print("lista di sensori",type(catalog['devices'][dev_name]))
                    for d in catalog['devices'][dev_name]['sensors']:
                        if d['ip'] == ip:
                            catalog['devices'][dev_name]['sensors'].pop(catalog['devices'][dev_name]['sensors'].index(d))

                    catalog['devices'][dev_name]['sensors'].append(new_dev)
                    catalog['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    print(f'${new_dev["name"]} - added to the catalog')

                    res["topic"] = catalog['topics'][name]
                    res["broker_ip"] = catalog["broker_ip"]

                    return json.dumps(res)

            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'addBot':
                new_bot_info = json.loads(cherrypy.request.body.read())
                print("cherrypy.request.body.read()", new_bot_info)
                try:
                    with open('catalog.json', 'r+') as f:
                        catalog = json.load(f)
                        try:
                            ip = new_bot_info['ip']
                            name = new_bot_info['name']
                            last_seen = new_bot_info['last_seen']
                            dev_name = 'rpi'
                        except KeyError:
                            f.close()
                            raise cherrypy.HTTPError(400, 'Bad request')

                        new_bot = {'ip': ip, 'name': name,
                                   'last_seen': last_seen}

                        # print("lista di bots",type(catalog['devices'][dev_name]))
                        for d in catalog['devices'][dev_name]['bots']:
                            if d['ip'] == ip:
                                catalog['devices'][dev_name]['bots'].pop(catalog['devices'][dev_name]['bots'].index(d))

                        catalog['devices'][dev_name]['bots'].append(new_bot)
                        catalog['last_updated'] = time.time()
                        f.seek(0)
                        f.write(json.dumps(catalog, indent=4, sort_keys=True))
                        f.truncate()
                        f.close()
                        print(f'${new_bot["name"]} - added to the catalog')

                except KeyError:
                    raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'removeDevice':
            new_device_info = json.loads(cherrypy.request.body.read())
            print("cherrypy.request.body.read()", new_device_info)
            try:
                with open('catalog.json', 'r+') as f:
                    catalog = json.load(f)
                    try:
                        ip = new_device_info['ip']
                        dev_name = new_device_info['dev_name']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for d in catalog['devices'][dev_name]['sensors']:
                        if d['ip'] == ip:
                            catalog['devices'][dev_name]['sensors'].pop(catalog['devices'][dev_name]['sensors'].index(d))
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
            try:
                with open('catalog.json', 'r+') as f:
                    catalog = json.load(f)
                    try:
                        ip = new_bot_info['ip']
                        dev_name = 'rpi'
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for d in catalog['devices'][dev_name]['bots']:
                        if d['ip'] == ip:
                            catalog['devices'][dev_name]['bots'].pop(catalog['devices'][dev_name]['bots'].index(d))
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

        if len(uri) == 1 and uri[0] == 'setThreshold':
            try:
                with open('catalog.json', 'r+') as f:
                    catalog = json.load(f)
                    new_threshold_info = json.loads(cherrypy.request.body.read())
                    try:
                        name = new_threshold_info['name']
                        min_T_th = new_threshold_info['min_temperature_th']
                        min_rh_th = new_threshold_info['min_humidity_th']
                        max_T_th = new_threshold_info['max_temperature_th']
                        max_co2_th = new_threshold_info['max_co2_th']
                        max_rh_th = new_threshold_info['max_humidity_th']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    new_th = {
                        "name": name,
                        "min_temperature_th": min_T_th,
                        "min_humidity_th": min_rh_th,
                        "max_temperature_th": max_T_th,
                        "max_humidity_th": max_rh_th,
                        "max_co2_th": max_co2_th
                    }

                    for d in catalog['thresholds']:
                        if d['name'] == name:
                            catalog['thresholds'].pop(catalog['thresholds'].index(d))

                    catalog['thresholds'].append(new_th)
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    print(f'${new_th["name"]} - added to the catalog')
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