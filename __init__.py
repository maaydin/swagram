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

from app import var
from app import service
from app import server
from app import event

monkey.patch_all()

service_resolver = service.Resolver()
service_resolver.daemon = True
service_resolver.start()

if __name__ == "__main__":
    server.app.debug = True
    swagram = WSGIServer(("", 5000), server.app)
    swagram.serve_forever()