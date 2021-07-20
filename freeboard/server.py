import cherrypy
import json
import requests
import os
import sys
import pathlib

#import cherrypy_cors
#cherrypy_cors.install()


class ClientREST(object):
	"""docstring for Reverser"""
	exposed=True
	def __init__(self):
			pass
	def GET(self,*uri,**params):
		if len(uri) == 0:
			return open(os.path.join(sys.path[0], "index.html"), "r").read()


			#r sarà il testo su chrome
			#prendo elementi da lista feeds
		#alla fine devo ritornare dizionario json.dumps() non lista!



	def POST(self, *uri, **params):

		if uri[0] == 'saveDashboard':

			new_dash = json.loads(params['json_string'])
			with open('./freeboard/examples/final_dashboard.json', 'w') as old_dash:
				old_dash.seek(0)  # rewind
				old_dash.write(json.dumps(new_dash, indent=4, sort_keys=True))
				old_dash.truncate()
				old_dash.close()


if __name__ == '__main__':
	conf = {
	'/':{
		'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
		'tools.staticdir.root': os.path.abspath(os.getcwd()),	#command taken from slides
		'cors.expose.on': True,
		},
	'/css':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':  './freeboard/css'
		},
	'/examples':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':   './freeboard/examples'
		},
	'/img':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':   './freeboard/img'
		},
	'/js':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':   './freeboard/js'
		},
	'/plugins':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':   './freeboard/plugins'
		}
	}
	cherrypy.config.update({
		"server.socket_port": 8080,
		})
	cherrypy.tree.mount(ClientREST(),'/',conf)
	#bisogna connetterlo al catalog
	# ClientREST() IP and port assignment
	cherrypy.server.socket_host = "127.0.0.1"
	cherrypy.server.socket_port = 8080
	cherrypy.engine.start()
	cherrypy.engine.block()