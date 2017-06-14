import threading
import var
import time

class Resolver (threading.Thread):
    def run (self):
        while True:
            for service in var.client.services.list():
                namespace_name = 'Global'
                if 'com.docker.stack.namespace' in service.attrs['Spec']['Labels']:
                    namespace_name = service.attrs['Spec']['Labels']['com.docker.stack.namespace']
                if not namespace_name in var.namespaces:
                    var.namespaces[namespace_name] = {}
                    var.namespaces[namespace_name]["nodes"] = {}
                    var.namespaces[namespace_name]["edges"] = {}

                namespace = var.namespaces[namespace_name]
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
                        var.services_by_address[vip['Addr'][:-3]] = service.id

                namespace["nodes"][service_name]["color"] = "#666"
                namespace["nodes"][service_name]["containers"] = {}
                for task in service.tasks():
                    if task['DesiredState'] != 'shutdown':
                        if task['Status']['State'] == 'running':
                            containerId = task['Status']['ContainerStatus']['ContainerID']
                            namespace["nodes"][service_name]["containers"][containerId] = task['Status']['State']
                            container = var.client.containers.get(containerId)
                            if "Health" in container.attrs["State"]:
                                namespace["nodes"][service_name]["containers"][containerId] = container.attrs["State"]["Health"]["Status"]
                            exec_id = var.llclient.exec_create(container=containerId, cmd=var.cmd)['Id']
                            stdout = var.llclient.exec_start(exec_id=exec_id, detach=False, tty=False, stream=True, socket=False)
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
                                        if edge in var.services_by_address and edge not in namespace["edges"][service.id]:
                                            namespace["edges"][service.id].append(var.services_by_address[edge])

                var.event.set(var.namespaces)
                time.sleep(1)