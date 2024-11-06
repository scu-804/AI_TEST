# coding=utf-8
from flask import Flask, request, jsonify, send_file
import os
from flask_cors import CORS, cross_origin
import random
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import torchvision as tv
import torch


if __name__ == '__main__':
	pass
else:
	print("只能从主入口启动")
	exit(-1)

app = Flask(__name__)

# 全局共享
ctx = {"cache": {}}


def request_params():
	params = {}
	try:
		for k, v in request.args.items():
			params[k] = v
	except BaseException as e:
		pass
	try:
		for k, v in request.values.items():
			params[k] = v
	except BaseException as e:
		pass
	try:
		r_json = request.get_json()
		if r_json and isinstance(r_json, dict):
			for k, v in r_json.items():
				params[k] = v
	except BaseException as e:
		pass
	return params


def get_url():
	return request.method, str(request.url_rule)


def time_str(time=None, fmt="%Y-%m-%d %H:%M:%S") -> str:
	"""
		时间格式化
		:param time: 要格式化的是俺
		:param fmt: 格式化格式
		:return: str 类型的格式时间
	"""
	import time as t
	return t.strftime(fmt, t.localtime(time))


def print_info():
	ps = request_params()
	method, url = get_url()
	with open("./print_info", mode="a", encoding="utf-8") as f:
		print(f"[{time_str()}]:{method}:{url}   params:{ps}", flush=True, file=f)


#  1获取被测对象的数据源
@cross_origin()
@app.route('/test_model', methods=['GET'])
def test_model():
	print_info()
	# todo mock 数据
	return_data = {
		"code": 200,
		"message": "success",
		"data": [
			"vgg11",
			"resnet18",
			"resnet34",
			"resnet50",
			"resnet101",
			"resnet152",
			"alexnet",
			"googlenet"
		]
	}
	# mock end
	return return_data


#  2获取内置依赖库及其版本的数据源
@cross_origin()
@app.route('/depn_lib', methods=['GET'])
def dependent_on_lib():
	print_info()
	# todo mock 数据
	return_data = {
		"code": 200,
		"message": "success",
		"data": [{
			"targetName": "numpy",
			"versionList": ["1.26.4", "1.26.5", "1.26.8", "2.1.2"]
		}, {
			"targetName": "pil",
			"versionList": ["1.3.1", "1.5.3", "1.8.2"]
		}, {
			"targetName": "cv2",
			"versionList": ["1.7.1", "1.9.3", "2.8.2"]
		}]
	}
	# mock end
	return return_data


#  3被测对象的模型权重文件数量
@cross_origin()
@app.route('/weight_number', methods=['GET'])
def weight_number():
	print_info()
	param = request_params()
	test_model = param.get("test_model")
	# todo mock 数据
	return_data = {
		"code": 200,
		"message": "success",
		"data": {
				"weightNum": random.randint(0, len(str(test_model)))
		}
	}
	# mock end
	return return_data


#  4被测对象的模型权重文件zip包下载
@cross_origin()
@app.route('/weight_download', methods=['GET'])
def weight_download():
	print_info()
	param = request_params()
	test_model = param.get("test_model")
	zip_path = "tmp.zip"
	# todo mock 数据
	folder_path = "./tmp"
	for f in os.listdir(folder_path):
		os.remove(os.path.join(folder_path, f))
	# #  随机生成几个pt
	net = random.choice([tv.models.googlenet(), tv.models.resnet18(), tv.models.resnet50(), tv.models.alexnet()])
	for i in range(random.randint(1, len(str(test_model)))):
		torch.save(net.state_dict(), f"{folder_path}/20241001_{random.randint(100, 999) / 10000}.pt")
	# # 打包
	import zipfile
	output_path = zip_path
	"""压缩文件或文件夹"""
	with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
		for root, dirs, files in os.walk(folder_path):
			for file in files:
				file_path = os.path.join(root, file)
				file_in_zip_path = os.path.relpath(file_path, os.path.dirname(folder_path))
				zipf.write(file_path, file_in_zip_path)
	# mock end
	return send_file(zip_path, as_attachment=True)


#  5获取被测对象的模型权重文件列表、对抗方法列表的数据源
@cross_origin()
@app.route('/check_model', methods=['GET'])
def check_model():
	print_info()
	param = request_params()
	test_model = param.get("test_model")
	# todo mock 数据
	return_data = {
		"code": 200,
		"message": "success",
		"data": {
			"weightList": ["20241031_0.3586.pt", "20241031_0.3536.pt", "20241031_0.3136.pt"],
			"methodList": [{
				"label": "白盒测试",
				"value": "white_box_testing",
			}, {
				"label": "黑盒测试",
				"value": "black_box_testing",
			}, {
				"label": "模糊测试",
				"value": "fuzzing_testing",
			}]
		}
	}
	# mock end
	return return_data


#  6启动对抗样本生成
@cross_origin()
@app.route('/adver_gen', methods=['POST'])
def adver_gen_post():
	print_info()
	param = request_params()
	get_url()
	mission_id = param.get("mission_id")
	test_model = param.get("test_model")
	test_weight = param.get("test_weight")
	test_method = param.get("test_method")
	timeout = param.get("timeout")  # unit is second
	file_paths = []
	# 保存上传的文件
	if 'test_seed' not in request.files:
		return {
			"code": 200,
			"message": "no file",
			"data": {
				"status": 2
			}
		}
	files = request.files.getlist('test_seed')  # 获取多个文件
	for file in files:
		if file.filename == '' or not str(file.filename).endswith(".zip"):
			continue
		filename = secure_filename(file.filename)  # 防止非法文件名
		file_path = os.path.abspath(os.path.join("./upload", filename))
		file.save(file_path)  # 保存文件
	# todo mock 数据
	# ........ 启动任务 todo
	import time
	ctx[f"task_{mission_id}"] = (time.time(), timeout, 0, 2)  # (开始时间，超时时间，生成数量，任务状态[进行中])
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"status": 1
		}
	}


#  7对抗样本生成过程中数据轮询
@cross_origin()
@app.route('/adver_gen', methods=['GET'])
def adver_gen_get():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	# todo mock 数据
	task_id = f"task_{mission_id}"
	if task_id in ctx:
		import time
		start_time, timeout, num, status = ctx[task_id]
		data_num = num
		if status == 2:
			now = time.time()
			if now >= timeout + start_time:
				status = 1
			else:
				status = 2  # 1:完成，2：进行中
				ctx[task_id] = (start_time, timeout, num + random.randint(2, 50), status)
	else:
		data_num = 0
		status = 1
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"dataNum": data_num,
			"status": status
		}
	}


#  8停止对抗样本生成
@cross_origin()
@app.route('/adver_gen_stop', methods=['POST'])
def adver_gen_stop():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	# todo mock 数据
	task_id = f"task_{mission_id}"
	if task_id in ctx:
		start_time, timeout, num, status = ctx[task_id]
		if status == 2:  # 运行中
			ctx[task_id] = (start_time, timeout, num + random.randint(2, 50), 1)
	else:
		pass
	success = 1
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"status": success  # 1 // 1:成功，2:失败
		}
	}


#  9生成的对抗样本zip包下载
@cross_origin()
@app.route('/adver_gen_download', methods=['GET'])
def adver_gen_download():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	zip_path = "tmp.zip"
	# todo mock 数据
	folder_path = "./tmp"
	for f in os.listdir(folder_path):
		os.remove(os.path.join(folder_path, f))
	# #  随机生成几个image
	for i in range(random.randint(10, 20 + len(str(mission_id)))):
		w, h, c = random.randint(50, 200), random.randint(50, 200), 3
		data = [random.randint(0, 255) for i in range(w * h * c)]
		data = np.array(data, dtype=np.uint8).reshape(h, w, c)
		cv2.imwrite(f"./tmp/{i + 1}.jpg", data)
	# # 打包
	import zipfile
	output_path = zip_path
	"""压缩文件或文件夹"""
	with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
		for root, dirs, files in os.walk(folder_path):
			for file in files:
				file_path = os.path.join(root, file)
				file_in_zip_path = os.path.relpath(file_path, os.path.dirname(folder_path))
				zipf.write(file_path, file_in_zip_path)
	# mock end
	return send_file(zip_path, as_attachment=True)


#  10获取不同被测对象下的评估配置指标
@cross_origin()
@app.route('/adver_metrics', methods=['GET'])
def adver_metrics():
	print_info()
	param = request_params()
	test_model = param.get("test_model")
	# todo mock 数据
	### .....
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": [
			"ACC",
			"ACTC",
			"ASS",
		]
	}


#  11启动测试任务评估
@cross_origin()
@app.route('/adver_eval', methods=['POST'])
def adver_eval_post():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	# todo mock 数据
	eval_id = f"eval_{mission_id}"
	ctx[eval_id] = (0, 2)  # (进度，状态[1 // 1:完成，2：进行中])
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"status": 1
		}
	}


#  12评估过程中数据轮询
@cross_origin()
@app.route('/adver_eval', methods=['GET'])
def adver_eval_get():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	# todo mock 数据
	eval_id = f"eval_{mission_id}"
	if eval_id in ctx:
		import time
		process, status = ctx[eval_id]
		if status == 2:  # 进行中
			process = min(100, process + random.randint(2, 6))
			if process >= 100:
				status = 1
			ctx[eval_id] = (process, status)
	else:
		status = 1
		process = 100
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"process": process,
			"metricsScores": [
				{"name": "ACC", "score": 90},
				{"name": "ACTC", "score": 60},
			],
			"status": status  # // 1:完成，2：进行中
		}
	}


#  13启动安全加固任务
@cross_origin()
@app.route('/sec_enhance', methods=['POST'])
def sec_enhance_post():
	print_info()
	param = request_params()
	enhance_id = param.get("enhance_id")
	test_model = param.get("test_model")
	mission_id = param.get("mission_id")
	# todo mock 数据
	sec_id = f"sec_{enhance_id}"
	ctx[sec_id] = (0, random.randint(1, 10), 2)  # (轮次， 权重数，状态【1:完成，2：进行中】)
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"status": 1  # 1 // 1:成功，2:失败
		}
	}


#  14安全加固过程数据轮询
@cross_origin()
@app.route('/sec_enhance', methods=['GET'])
def sec_enhance_get():
	print_info()
	param = request_params()
	enhance_id = param.get("enhance_id")
	# todo mock 数据
	sec_id = f"sec_{enhance_id}"
	tota_eps = 2000
	if sec_id in ctx:
		epoch, num, status = ctx[sec_id]
		if status == 2:  # 进行中
			epoch = min(tota_eps, tota_eps + random.randint(2, 6))
			if epoch >= tota_eps:
				status = 1
			ctx[sec_id] = (epoch, num, status)
	else:
		status = 1
		epoch = tota_eps
		num = 1
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"epoch": epoch,
			"acc": random.randint(50, 100),
			"loss": random.randint(50, 1000) / 1000,
			"weightNum": num,
			"status": status  # 1: 完成，2：进行中
		}
	}


#  15停止安全加固任务
@cross_origin()
@app.route('/sec_enhance_stop', methods=['POST'])
def sec_enhance_stop():
	print_info()
	param = request_params()
	enhance_id = param.get("enhance_id")
	# todo mock 数据
	sec_id = f"sec_{enhance_id}"
	ctx[sec_id] = (0, random.randint(1, 10), 1)  # (轮次， 权重数，状态【1:完成，2：进行中】)
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"status": 1
		}
	}


#  16安全加固任务的模型权重文件zip包下载
@cross_origin()
@app.route('/sec_enhance_weight_download', methods=['GET'])
def sec_enhance_weight_download():
	print_info()
	param = request_params()
	enhance_id = param.get("enhance_id")
	zip_path = "tmp.zip"
	# todo mock 数据
	folder_path = "./tmp"
	for f in os.listdir(folder_path):
		os.remove(os.path.join(folder_path, f))
	# #  随机生成几个pt
	import torchvision as tv
	import torch
	net = random.choice([tv.models.googlenet(), tv.models.resnet18(), tv.models.resnet50(), tv.models.alexnet()])
	for i in range(random.randint(1, len(str(test_model)))):
		torch.save(net.state_dict(), f"{folder_path}/20241001_{random.randint(100, 999) / 10000}.pt")
	# # 打包
	import zipfile
	output_path = zip_path
	"""压缩文件或文件夹"""
	with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
		for root, dirs, files in os.walk(folder_path):
			for file in files:
				file_path = os.path.join(root, file)
				file_in_zip_path = os.path.relpath(file_path, os.path.dirname(folder_path))
				zipf.write(file_path, file_in_zip_path)
	# mock end
	return send_file(zip_path, as_attachment=True)


#  17启动框架漏挖任务
@cross_origin()
@app.route('/vul_dig', methods=['POST'])
def vul_dig_post():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	lib_name = param.get("lib_name")
	lib_version = param.get("lib_version")
	# todo mock 数据
	vul_id = f"vul_{mission_id}"
	# # 缓存状态
	edges = 0
	coverage = 0
	thoughout = 0
	crashNum = 0
	paths = 0
	status = 2
	ctx[vul_id] = (edges, coverage, thoughout, crashNum, paths, status)
	success = True
	# mock end
	return {
		"code": 200,
		"message": "success" if success else "fail",
		"data": {
			"status": 1 if success else 2  # // 1:成功，2:失败
		}
	}


#  18框架漏挖过程数据轮询
@cross_origin()
@app.route('/vul_dig', methods=['GET'])
def vul_dig_get():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	# todo mock 数据
	vul_id = f"vul_{mission_id}"
	# # 缓存状态
	if vul_id in ctx:
		edges, coverage, thoughout, crashNum, paths, status = ctx[vul_id]
		if status == 2:
			if random.choices([True, False], weights=[0.03, 0.97]):  # 结束
				edges += random.randint(0, 3)
				coverage += random.randint(0, 5) / 10
				thoughout += random.randint(0, 3)
				crashNum += random.randint(0, 3)
				paths += random.randint(0, 3)
				status = 1
				ctx[vul_id] = (edges, coverage, thoughout, crashNum, paths, status)
	else:
		status = 1
		edges = 0
		coverage = 0
		thoughout = 0
		crashNum = 0
		paths = 0
	# mock end
	return {
		"code": 200,
		"message": "框架漏挖执行中",
		"data": {
			"coverage": coverage,
			"thoughout": thoughout,
			"speed": random.randint(500, 900) / random.randint(50, 90),
			"crashNum": crashNum,
			"paths": paths,
			"edges": edges,
			"status": status  # // 1:完成，2：进行中
		}
	}


#  19停止框架漏挖任务
@cross_origin()
@app.route('/vul_dig_stop', methods=['POST'])
def vul_dig_stop():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	# todo mock 数据
	vul_id = f"vul_{mission_id}"
	if vul_id in ctx:
		edges, coverage, thoughout, crashNum, paths, status = ctx[vul_id]
		status = 1
		ctx[vul_id] = (edges, coverage, thoughout, crashNum, paths, status)
	# mock end
	return {
		"code": 200,
		"message": "success",
		"data": {
			"status": 1  # // 1:成功，2:失败
		}
	}


#  20框架漏挖任务的Crash文件zip包下载
@cross_origin()
@app.route('/vul_dig_crash_download', methods=['GET'])
def vul_dig_crash_download():
	print_info()
	param = request_params()
	mission_id = param.get("mission_id")
	zip_path = "tmp.zip"
	# todo mock 数据
	folder_path = "./tmp"
	for f in os.listdir(folder_path):
		os.remove(os.path.join(folder_path, f))
	# #  随机生成几个漏洞文件
	import torchvision as tv
	import torch
	net = random.choice([tv.models.googlenet(), tv.models.resnet18(), tv.models.resnet50(), tv.models.alexnet()])
	for i in range(random.randint(1, 5)):
		torch.save(net.state_dict(), f"{folder_path}/20241001_{random.randint(100, 999) / 10000}.bug")
	# # 打包
	import zipfile
	output_path = zip_path
	"""压缩文件或文件夹"""
	with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
		for root, dirs, files in os.walk(folder_path):
			for file in files:
				file_path = os.path.join(root, file)
				file_in_zip_path = os.path.relpath(file_path, os.path.dirname(folder_path))
				zipf.write(file_path, file_in_zip_path)
	# mock end
	return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
	app.run(debug=False, host="0.0.0.0", port=8080)
