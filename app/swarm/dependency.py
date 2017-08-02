import threading
import traceback
from .. import globals
import time
import docker

client = docker.APIClient(**docker.utils.kwargs_from_env())

class Watcher (threading.Thread):
    def run (self):
        while True:
            try:
                for namespace in globals.namespaces:
                    for node in globals.namespaces[namespace]["nodes"]:
                        for container in globals.namespaces[namespace]["nodes"][node]["containers"]:
                            if globals.namespaces[namespace]["nodes"][node]["containers"][container] == "healthy":
                                exec_id = client.exec_create(container=container, cmd=globals.cmd)['Id']
                                stdout = client.exec_start(exec_id=exec_id, detach=False, tty=False, stream=True, socket=False)
                                for lines in stdout:
                                    lines = lines.split("\n")
                                    for line in lines:
                                        edge = line.strip().split()
                                        if len(edge) > 4:
                                            edge = edge[4].strip(':f').split(':')[0]
                                            if globals.namespaces[namespace]["nodes"][node]["id"] not in globals.namespaces[namespace]["edges"]:
                                                globals.namespaces[namespace]["edges"][globals.namespaces[namespace]["nodes"][node]["id"]] = []
                                            print "######## BEGIN ########"
                                            print edge
                                            print globals.endpoints
                                            print globals.namespaces[namespace]["edges"]
                                            print "######## END ########"
                                            if edge in globals.endpoints and globals.endpoints[edge] not in globals.namespaces[namespace]["edges"][globals.namespaces[namespace]["nodes"][node]["id"]]:
                                                globals.namespaces[namespace]["edges"][globals.namespaces[namespace]["nodes"][node]["id"]].append(globals.endpoints[edge])
                            globals.event.set(globals.namespaces)
                            time.sleep(0.5)
            except Exception as e:
                print e
                traceback.print_exc()