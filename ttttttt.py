import threading
import docker


if __name__ == '__main__':

	# def c():
	# 	def a(i):
	# 		import time
	# 		for ii in range(i):
	# 			print(ii)
	# 			time.sleep(0.3)
	#
	# 	t = threading.Thread(target=a, args=(50, ))
	# 	t.start()
	# 	del t
	# 	print(1111111111111111111111)
	#
	#
	# c()
	# print(233333333333)

	# 远程Docker主机地址
	remote_docker_host = "tcp://10.1.2.189:2375"

	client = docker.DockerClient(base_url=remote_docker_host)

	print(client)

	images = client.images.list(all=True)
	for image in images:
		print(image.labels, image.tags, image.id)

	print("111111111111111111111111111111111111111111")
	name_id = {}
	# 列出所有运行中的容器
	containers = client.containers.list(all=True)
	for container in containers:
		print(container.id, container.image, container.status, container.name)
		name_id[container.name] = container.id
	print(name_id)



