import cherrypy
import json
import requests
import os
import sys
import pathlib



class ClientREST(object):
	"""docstring for Reverser"""
	exposed=True
	def __init__(self):
			pass
	def GET(self,*uri,**params):
		if len(uri) == 0:
			return open(os.path.join(sys.path[0], "index.html"), "r").read()




	def POST(self, *uri, **params):
	    #POST method to save modifications to dashboard
		if uri[0] == 'saveDashboard':

			new_dash = json.loads(params['json_string'])
			with open('./freeboard/examples/final_dashboard.json', 'w') as old_dash:
				old_dash.seek(0)  # to move the cursor back to the beginning of the file  
				old_dash.write(json.dumps(new_dash, indent=4, sort_keys=True)) #start writing
				old_dash.truncate() #to deal with the case where the new data is smaller than the previous
				old_dash.close()


if __name__ == '__main__':
	conf = {
	'/':{
		'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
		'tools.staticdir.root': os.path.abspath(os.getcwd()),	
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
	cherrypy.server.socket_host = "127.0.0.1"
	cherrypy.server.socket_port = 8080
	cherrypy.engine.start()
	cherrypy.engine.block()