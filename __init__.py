from gevent import monkey
from gevent.wsgi import WSGIServer

from app import event
from app import server
from app import platform

monkey.patch_all()

if __name__ == "__main__":
    server.app.debug = True
    swagram = WSGIServer(("", 5042), server.app)
    swagram.serve_forever()