import service
import container
import dependency
import status

service_watcher = service.Watcher()
service_watcher.daemon = True
service_watcher.start()

container_watcher = container.Watcher()
container_watcher.daemon = True
container_watcher.start()

dependency_watcher = dependency.Watcher()
dependency_watcher.daemon = True
dependency_watcher.start()