# coding=utf-8
import os
import docker
import gevent
import time
import threading
import json
from gevent import monkey
from gevent.event import AsyncResult
from gevent.wsgi import WSGIServer
from flask import Flask, Response

monkey.patch_all()

namespaces = {}
services_by_address = {}
client = docker.from_env()
llclient = docker.APIClient(**docker.utils.kwargs_from_env())
event = AsyncResult()

cmd = "sh -c \"(netstat -nputw || ss) | grep 'tcp\|udp'\""

class ServiceResolver (threading.Thread):
    def run (self):
        while True:
            for service in client.services.list():
                namespace_name = 'Global'
                if 'com.docker.stack.namespace' in service.attrs['Spec']['Labels']:
                    namespace_name = service.attrs['Spec']['Labels']['com.docker.stack.namespace']
                if not namespace_name in namespaces:
                    namespaces[namespace_name] = {}
                    namespaces[namespace_name]["nodes"] = {}
                    namespaces[namespace_name]["edges"] = {}

                namespace = namespaces[namespace_name]
                service_name = service.name
                if namespace_name != 'Global':
                    service_name = service.name[len(namespace_name)+1:]
                #replicas = int(service.attrs['Spec']['Mode']['Replicated']['Replicas'])
                namespace["nodes"][service_name] = {}
                namespace["nodes"][service_name]["id"] = service.id
                namespace["nodes"][service_name]["label"] = service_name
                #namespace[service_name]["replicas"] = replicas

                if 'VirtualIPs' in service.attrs['Endpoint']:
                    for vip in service.attrs['Endpoint']['VirtualIPs']:
                        services_by_address[vip['Addr'][:-3]] = service.id

                namespace["nodes"][service_name]["color"] = "#666"
                namespace["nodes"][service_name]["containers"] = {}
                for task in service.tasks():
                    if task['DesiredState'] != 'shutdown':
                        if task['Status']['State'] == 'running':
                            containerId = task['Status']['ContainerStatus']['ContainerID']
                            namespace["nodes"][service_name]["containers"][containerId] = task['Status']['State']
                            container = client.containers.get(containerId)
                            if "Health" in container.attrs["State"]:
                                namespace["nodes"][service_name]["containers"][containerId] = container.attrs["State"]["Health"]["Status"]
                            exec_id = llclient.exec_create(container=containerId, cmd=cmd)['Id']
                            stdout = llclient.exec_start(exec_id=exec_id, detach=False, tty=False, stream=True, socket=False)
                            if service.id not in namespace["edges"]:
                                namespace["edges"][service.id] = []
                            for lines in stdout:
                                lines = lines.split("\n")
                                for line in lines:
                                    edge = line.strip().split()
                                    print "############# EDGE 1 ###############"
                                    print edge
                                    if len(edge) > 5:
                                        edge = edge[5].strip(':f').split(':')[0]
                                        print "############# EDGE 2 ###############"
                                        print edge
                                        if edge in services_by_address and edge not in namespace["edges"][service.id]:
                                            namespace["edges"][service.id].append(services_by_address[edge])

                event.set(namespaces)
                time.sleep(1)

service_resolver = ServiceResolver()
service_resolver.daemon = True
service_resolver.start()

class ServerSentEvent(object):
    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k) 
                 for k, v in self.desc_map.iteritems() if k]
        
        return "%s\n\n" % "\n".join(lines)

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
    for key, value in namespaces.iteritems():
        namespacelist.append(key)
    return json.dumps(namespacelist)

@app.route("/namespace/<path:namespace>/nodes")
def serve_nodes(namespace):
    nodelist = []
    for key, value in namespaces[namespace]["nodes"].iteritems():
        nodelist.append(value)
    return json.dumps(nodelist)

@app.route("/namespace/<path:namespace>/edges")
def serve_edges(namespace):
    edgelist = []
    for from_service, to_services in namespaces[namespace]["edges"].iteritems():
        for to_service in to_services:
            edgelist.append({"from": from_service, "to": to_service})
    return json.dumps(edgelist)

@app.route("/namespace/<path:namespace>/subscribe")
def subscribe(namespace):
    def gen():
        while True:
            result = event.get()
            response = {}
            response["nodes"]=[]
            response["edges"]=[]
            for key, value in result[namespace]["nodes"].iteritems():
                response["nodes"].append(value)
            for from_service, to_services in result[namespace]["edges"].iteritems():
                for to_service in to_services:
                    response["edges"].append({"from": from_service, "to": to_service})
            ev = ServerSentEvent(json.dumps(response))
            yield ev.encode()
            time.sleep(1)

    return Response(gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.debug = True
    server = WSGIServer(("", 5000), app)
    server.serve_forever()