import cherrypy
import json
import requests
import os
#import cherrypy_cors


#cherrypy_cors.install()


class ClientREST(object):
	"""docstring for Reverser"""
	exposed=True
	def __init__(self):
			pass
	def GET(self,*uri,**params):
		if len(uri) == 0:
			return open('index.html')


			#r sarà il testo su chrome
			#prendo elementi da lista feeds
		#alla fine devo ritornare dizionario json.dumps() non lista!



	def POST(self, *uri, **params):
		#TO SAVE CHANGES DONE DIRECTLY ON DASHBOARD
		if uri[0] == "saveDashboard":

			config=params['json_string']
			with open("examples/prova.json", "w") as f:
				f.write(config)
			#f.close()
if __name__ == '__main__':
	conf = {
	'/':{
		'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
		'tools.staticdir.root': os.path.abspath(os.getcwd()),	#command taken from slides
		'cors.expose.on': True,
		},
	'/css':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':'./css'
		},
	'/examples':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':'./examples'
		},
	'/img':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':'./img'
		},
	'/js':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':'./js'
		},
	'/plugins':{
		'tools.staticdir.on': True,
		'tools.staticdir.dir':'./plugins'
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