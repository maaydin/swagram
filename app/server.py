import var
import json
import event
import time
from flask import Flask, Response

app = Flask(__name__, static_url_path='')

@app.route("/")
def index():
    return app.send_static_file('index.html')

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return app.send_static_file("assets/"+filename)

@app.route("/namespaces")
def serve_namespaces():
    namespacelist = []
    for key, value in var.namespaces.iteritems():
        namespacelist.append(key)
    return json.dumps(namespacelist)

@app.route("/namespace/<path:namespace>/nodes")
def serve_nodes(namespace):
    nodelist = []
    for key, value in var.namespaces[namespace]["nodes"].iteritems():
        nodelist.append(value)
    return json.dumps(nodelist)

@app.route("/namespace/<path:namespace>/edges")
def serve_edges(namespace):
    edgelist = []
    for from_service, to_services in var.namespaces[namespace]["edges"].iteritems():
        for to_service in to_services:
            edgelist.append({"from": from_service, "to": to_service})
    return json.dumps(edgelist)

@app.route("/namespace/<path:namespace>/subscribe")
def subscribe(namespace):
    def gen():
        while True:
            result = var.event.get()
            response = {}
            response["nodes"]=[]
            response["edges"]=[]
            for key, value in result[namespace]["nodes"].iteritems():
                response["nodes"].append(value)
            for from_service, to_services in result[namespace]["edges"].iteritems():
                for to_service in to_services:
                    response["edges"].append({"from": from_service, "to": to_service})
            ev = event.ServerSentEvent(json.dumps(response))
            yield ev.encode()
            time.sleep(10)

    return Response(gen(), mimetype="text/event-stream")