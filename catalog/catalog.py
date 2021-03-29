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
            cc = catalog['Catalog']
        if uri[0] == "broker":
            return json.dumps(cc[0])
        elif uri[0] == "threshold":
            return json.dumps(cc[1])
        elif uri[0] == "devices":
            return json.dumps(cc[2])

    def POST(self, *uri, **params):
        if len(uri) == 1 and uri[0] == 'addDevice':
            try:
                with open('catalog.json', 'r+') as f:
                    catalog = json.load(f)
                    new_device_info = json.loads(cherrypy.request.body.read())
                    try:
                        ip = new_device_info['ip']
                        port = new_device_info['port']
                        name = new_device_info['name']
                        last_seen = new_device_info['last_seen']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    new_dev = {'ip': ip, 'port': port, 'name': name,
                               'last_seen': last_seen}

                    for d in catalog['Catalog'][2]['devices']:
                        if d['ip'] == ip:
                            catalog['Catalog'][2]['devices'].pop(catalog['Catalog'][2]['devices'].index(d))

                    catalog['Catalog'][2]['devices'].append(new_dev)
                    catalog['Catalog'][2]['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    print(f'${new_dev["name"]} - added to the catalog')
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')

        if len(uri) == 1 and uri[0] == 'removeDevice':
            try:
                with open('catalog.json', 'r+') as f:
                    catalog = json.load(f)
                    new_device_info = json.loads(cherrypy.request.body.read())
                    try:
                        ip = new_device_info['ip']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for d in catalog['Catalog'][2]['devices']:
                        if d['ip'] == ip:
                            catalog['Catalog'][2]['devices'].pop(catalog['Catalog'][2]['devices'].index(d))
                            found = True

                    if found is False:
                        f.close()
                        raise cherrypy.HTTPError(404, "Device not found")

                    catalog['Catalog'][2]['last_updated'] = time.time()
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

                    for d in catalog['Catalog'][1]['thresholds']:
                        if d['name'] == name:
                            catalog['Catalog'][1]['thresholds'].pop(catalog['Catalog'][1]['thresholds'].index(d))

                    catalog['Catalog'][1]['thresholds'].append(new_th)
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