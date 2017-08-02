import threading
from .. import globals
from .. import state
import time

class Watcher (threading.Thread):
    def run (self):
        while True:
            for namespace in globals.namespaces:
                for node in globals.namespaces[namespace]["nodes"]:
                    containers = len(node["containers"])
                    healthy_containers = 0
                    status = state.critical
                    for container in node["containers"]:
                        if node["containers"][container] == "healthy":
                            healthy_containers += 1

                    if containers > 0 and containers == healthy_containers:
                        status = state.healthy
                    elif containers > 0 and healthy_containers > 0:
                        status = state.warning
                    elif containers == 0:
                        status = state.pending

                    globals.statuses[node["id"]] = status

            globals.event.set(globals.statuses)
            time.sleep(3)