import threading
import traceback
from .. import globals
import time
import docker
client = docker.from_env()

class Watcher (threading.Thread):
    def run (self):
        while True:
            try:
                for namespace in globals.namespaces:
                    for service in globals.namespaces[namespace]["nodes"]:
                        serviceObj = client.services.get(globals.namespaces[namespace]["nodes"][service]["id"])
                        containers = {}
                        for task in serviceObj.tasks():
                            if task['DesiredState'] != 'shutdown':
                                if task['Status']['State'] == 'running':
                                    containerId = task['Status']['ContainerStatus']['ContainerID']
                                    globals.namespaces[namespace]["nodes"][service]["containers"][containerId] = task['Status']['State']
                                    container = client.containers.get(containerId)
                                    if "Health" in container.attrs["State"]:
                                        globals.namespaces[namespace]["nodes"][service]["containers"][containerId] = container.attrs["State"]["Health"]["Status"]
                                    else:
                                        globals.namespaces[namespace]["nodes"][service]["containers"][containerId] = "healthy"
                        globals.event.set(globals.namespaces)
                        time.sleep(0.5)
            except docker.errors.NotFound as e:
                service = str(e).split("\"")[1].split(" ")[1]
                del globals.namespaces[namespace]["nodes"][service]
            except Exception as e:
                print e
                traceback.print_exc()