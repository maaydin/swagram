import docker
import gevent
from gevent import monkey
from gevent.event import AsyncResult
from gevent.wsgi import WSGIServer

namespaces = {}
services_by_address = {}
event = AsyncResult()
client = docker.from_env()
llclient = docker.APIClient(**docker.utils.kwargs_from_env())
cmd = "sh -c \"(netstat -nputw || ss) | grep 'tcp\|udp'\""