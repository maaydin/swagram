from gevent.event import AsyncResult

namespaces = {}
endpoints = {}
statuses = {}
event = AsyncResult()

cmd = "sh -c \"(netstat -nputw || ss) | grep 'tcp\|udp'\""