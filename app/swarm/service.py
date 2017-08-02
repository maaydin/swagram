import threading
from .. import globals
import time
import docker
client = docker.from_env()

class Watcher (threading.Thread):
    def run (self):
        while True:
            for service in client.services.list():
                namespace_name = 'globals'
                if 'com.docker.stack.namespace' in service.attrs['Spec']['Labels']:
                    namespace_name = service.attrs['Spec']['Labels']['com.docker.stack.namespace']
                if not namespace_name in globals.namespaces:
                    globals.namespaces[namespace_name] = {}
                    globals.namespaces[namespace_name]["nodes"] = {}
                    globals.namespaces[namespace_name]["edges"] = {}

                service_label = service.name
                if namespace_name != 'globals':
                    service_label = service.name[len(namespace_name)+1:]
                globals.namespaces[namespace_name]["nodes"][service.id] = {}
                globals.namespaces[namespace_name]["nodes"][service.id]["id"] = service.id
                globals.namespaces[namespace_name]["nodes"][service.id]["name"] = service.name
                globals.namespaces[namespace_name]["nodes"][service.id]["label"] = service_label
                globals.namespaces[namespace_name]["nodes"][service.id]["shape"] = "image"
                globals.namespaces[namespace_name]["nodes"][service.id]["image"] = "createImage('"+service.id+"')"
                globals.namespaces[namespace_name]["nodes"][service.id]["containers"] = {}

                if 'VirtualIPs' in service.attrs['Endpoint']:
                    for vip in service.attrs['Endpoint']['VirtualIPs']:
                        globals.endpoints[vip['Addr'][:-3]] = service.id
            time.sleep(100)