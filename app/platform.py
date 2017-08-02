import os

platform_name = os.getenv('PLATFORM', 'swarm')

__import__("app."+platform_name, fromlist=[])