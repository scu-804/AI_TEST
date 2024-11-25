#coding=utf-8

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
import os
from utils import *
from Misson_class import *
from werkzeug.utils import secure_filename
from vuln_decorators import *
from vuln_service.info_read import info_read_json
from vuln_service.__init__ import stop


app = Flask(__name__)


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



# ## there are several functions about interface POST(GET) key. Every key has a unique function
## model19: 框架漏挖停止
@app.route('/vul_dig_stop', methods=['POST'])
def vuln_dig_stop():
     mission_id = request.form.get('mission_id')
     mission_manager = VulnDigMissionManager('Vuln_dig_missions_DBSM.csv')
     if mission_id not in mission_manager.missions.keys():
            return {
                "code": 400,
                "message": "任务不存在，id有误",
                "data": {
                    "status": 2
                }
            }
     mission = mission_manager.missions[mission_id]

     docker_container = mission_manager.missions[mission_id].container_id
     stop(docker_container)

     mission.update_status(1)
     mission_manager.save_missions_to_csv()

     return {
          "code": 200,
          "message": "任务已停止",
          "data": {"status": 1}
     }


## model18: 框架漏挖过程数据轮询
@app.route('/vul_dig', methods=['GET'])
#@info_read_decorator()
def vuln_dig_query():
     mission_id = request.args.get('mission_id')

     mission_manager = VulnDigMissionManager('Vuln_dig_missions_DBSM.csv')
     if mission_id not in mission_manager.missions.keys():
            return {
            "code": 400,
            "message": "任务不存在，id有误",
            "data": {"status": 2},
        }
     mission = mission_manager.missions[mission_id]

     docker_container = mission_manager.missions[mission_id].container_id
     container_info = info_read_json(docker_container)

     mission_status = container_info["status"]
     mission.update_status(mission_status)

     mission_manager.save_missions_to_csv()

     return {
          "code": 200,
          "message": "框架漏挖执行中",
          "data": container_info
     }


## model17: 框架漏挖启动
@app.route('/vul_dig', methods=['POST'])
@vulndig_start_decorator(init_yaml_read_for_vulndig)
def vuln_dig_start():
     mission_id = request.form.get('mission_id')
     lib_name = request.form.get('lib_name')
     lib_version = request.form.get('lib_version')

     vuln_dict = init_yaml_read_for_vulndig()
     docker_container = vuln_dict[lib_name].get('docker_container')
    #  shell_command = vuln_dict[lib_name].get('shell_command')

     mission_manager = VulnDigMissionManager('Vuln_dig_missions_DBSM.csv')
     mission_status = 2
     mission = VulnDigMission(mission_id, docker_container,lib_name, lib_version, mission_status)
     mission_manager.add_or_update_mission(mission)

     return {
            "code": 200,
            "message": "任务已开始执行",
            "data": {
                "status": 1
            }
        }


## mode16: 安全加固任务的模型权重文件zip包下载
@cross_origin()
@app.route('/sec_enhance_weight_download', methods=['GET'])
def sec_enhance_weight_download():

    print_info()
    param = request_params()

    enhance_id = param.get("enhance_id")
    enhance_manager = Enhance_MissionManager('Adver_gen_missions_DBSM.csv')

    '''
           根据docker引擎实际情况修改run.sh

        exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
        '''

    if enhance_id:
        mission = enhance_manager.enhance_mission_dict[enhance_id]

        model_dict = init_read_yaml_for_model_duplicate()
        zip_addr = model_dict[mission.test_model].get('enhance_download_addr')
        zip_addr = f"{zip_addr}/{enhance_id}_enhance.zip"

        zip_stream = download_zip_from_docker(zip_addr)

        return send_file(zip_stream, mimetype='application/zip', as_attachment=True, download_name=f"{enhance_id}_enhance.zip")
        # return jsonify({
        #     "code": 200,
        #     "message": "安全加固模型下载",
        #      "zipAddr": "xxxx",
        # })
    else :
        return {
            "code": 400,
            "message": "任务ID未识别"
        }

## mode15: 停止安全加固任务
@cross_origin()
@app.route('/sec_enhance_stop', methods=['POST'])
def sec_enhance_stop():

    print("Received POST request")

    print_info()
    param = request_params()
    enhance_id = param.get("enhance_id")

    enhance_manager = Enhance_MissionManager('Adver_gen_missions_DBSM.csv')   ###   这个csv用来记录对抗样本生成任务

    '''
           根据docker引擎实际情况修改run.sh

        exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
        '''

    if enhance_id not in enhance_manager.enhance_mission_dict.keys():
        return {
            "code": 400,
            "message": "任务不存在，id有误",
            "data": {
                "status": 2
            }
        }
    else:
        mission = enhance_manager.enhance_mission_dict[enhance_id]
        mission.update_status(1)
        enhance_manager.save_missions_to_csv()

        model_dict = init_read_yaml_for_model_duplicate()

        docker_shell_run = model_dict[mission.test_model].get('docker_container_enchance_stop_shell')
        container_id, script_path = docker_shell_run.split(":", 1)
        shell_command = f"{script_path} {enhance_id}"
        #shell_command = f"{script_path}"
        shell_path = f"{container_id}:{shell_command}"
        exec_docker_container_shell(shell_path)

        return {
            "code": 200,
            "message": "任务已停止",
            "data": {
                "status": 1
            }
        }


## mode14: 安全加固过程数据轮询
@cross_origin()
@app.route('/sec_enhance', methods=['GET'])
def sec_enhance_query():

    print_info()
    param = request_params()
    enhance_id = param.get("enhance_id")

    enhance_manager = Enhance_MissionManager('Adver_gen_missions_DBSM.csv')

    '''
       根据docker引擎实际情况修改run.sh

    exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
    '''

    if enhance_id not in enhance_manager.enhance_mission_dict.keys():
        return {
            "code": 400,
            "message": "任务不存在，id有误",
            "data": {"status": 2},
        }
    else:
        enhance_mission = enhance_manager.enhance_mission_dict[enhance_id]
        model_dict = init_read_yaml_for_model_duplicate()

        docker_shell_run = model_dict[enhance_mission.test_model].get('docker_container_enchance_query_shell')
        container_id, script_path = docker_shell_run.split(":", 1)
        shell_command = f"{script_path} {enhance_id}"
        shell_path = f"{container_id}:{shell_command}"
        exec_result = exec_docker_container_shell(shell_path)

        return jsonify({
            "code": 200,
            "message": "安全加固执行中",
            "data": exec_result,
        })
        # return {
        #     "code": 200,
        #     "message": "安全加固执行中",
        #     "data": {
        #         "epoch": 32,  ## 0-100的进度值，平台拼接%
        #         "acc" : 66.6,
        #         "loss": 3.4,
        #         "weightNum": 5,
        #         "status": 1},
        # }

## mode13: 启动安全加固任务
@cross_origin()
@app.route('/sec_enhance', methods=['POST'])
def sec_enhance():
    print("Received POST request")

    print_info()
    param = request_params()
    enhance_id = param.get("enhance_id")
    test_model = param.get("test_model")
    mission_id = param.get("mission_id")

    enhance_manager = Enhance_MissionManager('Adver_gen_missions_DBSM.csv')
    # enhance_manager.update_enhance_mission_dict(mission_id, enhance_id)
    # enhance_manager.save_missions_to_csv()


    print(mission_id, test_model, enhance_id)
    if enhance_id in enhance_manager.enhance_mission_dict.keys():   ###  if same mission id is executed twice, will report error
        return {
            "code": 400,
            "message": "该任务已存在",
            "data": {
                "status": 2
            }
        }

    if all([mission_id, test_model, enhance_id]):
        mission_status = 2
        enhance_manager.update_enhance_mission_dict(mission_id, enhance_id)
        enhance_manager.save_missions_to_csv()


        '''
                   根据docker引擎实际情况修改run.sh

                exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
                '''

        model_dict = init_read_yaml_for_model_duplicate()
        enhance_mission = enhance_manager.enhance_mission_dict[enhance_id]

        docker_shell_run = model_dict[enhance_mission.test_model].get('docker_container_enchance_shell')
        container_id, script_path = docker_shell_run.split(":", 1)
        shell_command = f"{script_path} {mission_id} {test_model} {enhance_id}"
        #shell_command = f"{script_path}"
        shell_path = f"{container_id}:{shell_command}"
        exec_docker_container_shell_detach_v2(shell_path)

        return {
            "code": 200,
            "message": "安全加固已开始执行",
            "data": {
                "status": 1
            }
        }
    else:
        return {
            "code": 400,
            "message": "POST参数有误",
            "data": {
                "status": 2
            }
        }

## mode12: 评估过程中数据轮询
@cross_origin()
@app.route('/adver_eval', methods=['GET'])
def adver_eval_query():
    print_info()
    param = request_params()
    mission_id = param.get("mission_id")

    mission_manager = MissionManager('Adver_gen_missions_DBSM.csv')

    '''
       根据docker引擎实际情况修改run.sh
       
    exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
    '''


    if mission_id not in mission_manager.missions.keys():
        return {
            "code": 400,
            "message": "任务不存在，id有误",
            "data": {
                "status": 2
            }
        }
    else:
        mission = mission_manager.missions[mission_id]
        model_dict = init_read_yaml_for_model_duplicate()

        adver_metrics = model_dict[mission.test_model].get('adver_metrics', [])
        metrics = []

        dcoker_shell_run = model_dict[mission.test_model].get('docker_container_evaluate_query_shell')
        container_id, script_path = dcoker_shell_run.split(":", 1)
        shell_command = f"{script_path} {mission_id}"
        shell_path = f"{container_id}:{shell_command}"
        exec_result = exec_docker_container_shell(shell_path)

        for line in exec_result.splitlines():
            for metric in adver_metrics:
                if line.startswith(metric):
                    metrics.append({"name": metric, "score": float(line.split(":")[1].strip())})
            if line.startswith("status"):
                    status = int(line.split(":")[1].strip())
        return {
            "code": 200,
            "message": "任务执行中",
            "data": {
                "process": 67.1,   ## 0-100的进度值，平台拼接%(实现方式有待商榷)
                "metricsScores": metrics,
                    # [\
                    #     {"name":"ACC", "score": 90},\
                    #     {"name":"ACTC", "score": 60},\
                    #     ],
                "status": status
            }
        }

## mode11: 启动测试任务评估
@cross_origin()
@app.route('/adver_eval', methods=['POST'])
def adver_eval():
    print_info()
    param = request_params()
    mission_id = param.get("mission_id")

    #eval_metrics = request.form.getlist('eval_metric')

    mission_manager = MissionManager('Adver_gen_missions_DBSM.csv')

    '''
           根据docker引擎实际情况修改run.sh

        exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
        '''

    if mission_id not in mission_manager.missions.keys():
        return {
            "code": 400,
            "message": "任务不存在，id有误",
            "data": {"status": 2},
        }
    else:
        mission = mission_manager.missions[mission_id]
        model_dict = init_read_yaml_for_model_duplicate()

        #metrics = ' '.join(eval_metrics)

        dcoker_shell_run = model_dict[mission.test_model].get('docker_container_evaluate_shell')
        container_id, script_path = dcoker_shell_run.split(":", 1)
        shell_command = f"{script_path} {mission_id}"
        shell_path = f"{container_id}:{shell_command}"
        exec_docker_container_shell_detach_v2(shell_path)

        return {
            "code": 200,
            "message": "评估已开始执行",
            "data": {
                "status": 1
            }
        }

## mode10: 获取不同被测对象下的评估配置指标
@cross_origin()
@app.route('/adver_metrics', methods=['GET'])
def adver_metrics():

    print_info()
    param = request_params()
    test_model = param.get("test_model")

    model_dict = init_read_yaml_for_model()

    if "adver_metrics" in model_dict[test_model].keys():
        return {
            "code": 200,
            "message": "模型的评估指标",
            "data": model_dict[test_model]["adver_metrics"],
        }
    else:
        return {
            "code": 400,
            "message": "模型不对",
            "data": {}
        }


## mode9: 生成的对抗样本zip包下载
@cross_origin()
@app.route('/adver_gen_download', methods=['GET'])
def adver_gen_download():

    print_info()
    param = request_params()
    mission_id = param.get("mission_id")

    mission_manager = MissionManager('Adver_gen_missions_DBSM.csv')

    '''
           根据docker引擎实际情况修改run.sh

        exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
        '''

    if mission_id:
        mission = mission_manager.missions[mission_id]
        model_dict = init_read_yaml_for_model_duplicate()
        model = mission.test_model
        zip_addr = model_dict[mission.test_model].get('result_download_addr')
        zip_addr = f"{zip_addr}/Attack_generation_{model}_{mission_id}.tar.gz"

        zip_stream = download_zip_from_docker(zip_addr)
        return send_file(zip_stream, mimetype='application/zip', as_attachment=True, download_name=f"{mission_id}_result.zip")
    else :
        return {
            "code": 400,
            "message": "任务ID未识别"
        }


## mode8: 停止对抗样本生成
@cross_origin()
@app.route('/adver_gen_stop', methods=['POST'])
def adver_gen_stop():
    print("Received POST request")

    print_info()
    param = request_params()
    mission_id = param.get("mission_id")

    mission_manager = MissionManager('Adver_gen_missions_DBSM.csv')   ###   这个csv用来记录对抗样本生成任务

    '''
           根据docker引擎实际情况修改run.sh

        exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
        '''

    if mission_id not in mission_manager.missions.keys():
        return {
            "code": 400,
            "message": "任务不存在，id有误",
            "data": {
                "status": 2
            }
        }
    else:
        mission = mission_manager.missions[mission_id]
        mission.update_status(1)
        mission_manager.add_or_update_mission(mission)

        model_dict = init_read_yaml_for_model_duplicate()
        docker_shell_run = model_dict[mission.test_model].get('docker_container_run_stop_shell')
        container_id, script_path = docker_shell_run.split(":", 1)
        shell_path = f"{container_id}:{script_path} {mission_id}"
        exec_docker_container_shell(shell_path)

        return {
            "code": 200,
            "message": "任务已停止",
            "data": {
                "status": 1
            }
        }

## mode7: 对抗样本生成过程中数据轮询
@cross_origin()
@app.route('/adver_gen', methods=['GET'])
def adver_gen_get():

    print_info()
    param = request_params()
    mission_id = param.get("mission_id")

    '''
           根据docker引擎实际情况修改run.sh

        exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
        '''
    mission_manager = MissionManager('Adver_gen_missions_DBSM.csv')
    if mission_id not in mission_manager.missions.keys():
        return {
            "code": 400,
            "message": "任务不存在，id有误",
            "data": {
                "dataNum": 0,
                "status": 2
            }
        }
    else:
        model_dict = init_read_yaml_for_model_duplicate()
        docker_shell_run = model_dict[mission_manager.missions[mission_id].test_model].get('docker_container_run_query_shell')
        container_id, script_path = docker_shell_run.split(":", 1)
        shell_path = f"{container_id}:{script_path} {mission_id}"
        data_num = exec_docker_container_shell(shell_path)

        print(f"shell result: {data_num}")

        # 尝试解析data_num
        r_data_num = 0
        r_status = mission_manager.missions[mission_id].mission_status
        flag = True
        if flag:
            try:
                r_data_num = int(data_num)
                flag = False
            except BaseException as e:
                pass
        if flag:
            try:
                if str(data_num).find("No running process found for mission_id") >= 0:
                    r_status = 1
                    r_data_num = None
                else:
                    r_data_num = int(str(data_num).split("\n")[0].replace("Datanum:", "").strip())
                    r_status = int(str(data_num).split("\n")[1].replace("status:", "").strip())
            except BaseException as e:
                pass

        return {
            "code": 200,
            "message": "任务执行中",
            "data": {
                "dataNum": r_data_num,
                "status": r_status
            }
        }


## mode6: 启动对抗样本生成
@cross_origin()
@app.route('/adver_gen', methods=['POST'])
def adver_gen():
    print("Received POST request")

    print_info()
    param = request_params()
    get_url()
    mission_id = param.get("mission_id")
    test_model = param.get("test_model")
    test_weight = param.get("test_weight")
    test_method = param.get("test_method")
    timeout = int(param.get("timeout"))  # unit is second

    file_paths = []

    if 'test_seed' not in request.files:
        return {
            "code": 400,
            "message": "POST参数有误",
            "data": {
                "status": 2
            }
        }
    files = request.files.getlist('test_seed')  # 获取多个文件
    for file in files:
        if file.filename == '' or not str(file.filename).endswith(".zip"):
            continue
        filename = secure_filename(file.filename)  # 防止非法文件名
        #filename = file.filename
        file_path = os.path.abspath(os.path.join("./upload", filename))
        file.save(file_path)  # 保存文件
        file_paths.append(file_path)

    seed_list = ",".join(file_paths)

    mission_manager = MissionManager('Adver_gen_missions_DBSM.csv')
    '''
           根据docker引擎实际情况修改run.sh

        exec_docker_container_shell("xxxxx:/some/path/your_run1.sh")
        '''
    '''
    if mission_id in mission_manager.missions.keys():   ###  if same mission id is executed twice, will report error
        return {
            "code": 400,
            "message": "该任务已存在",
            "data": {
                "status": 2
            }
        }
'''

    if mission_id in mission_manager.missions.keys() and mission_manager.missions[mission_id].mission_status == 2:
        return {
            "code": 400,
            "message": "该任务运行中",
            "data": {
                 "status": 2
            }
       }

    test_seed = "FGSM"  # TODO 还未约定好文件传输格式，暂且给个确定值，方便后面测试
    if all([mission_id, test_model, test_weight, test_seed, test_method, timeout]):
        mission_status = 2
        mission = Mission(mission_id, test_model, test_weight, test_seed, test_method, timeout, mission_status)
        mission_manager.add_or_update_mission(mission)

        model_dict = init_read_yaml_for_model_duplicate()

        docker_shell_run = model_dict[test_model].get('docker_container_run_shell')

        container_id, script_path = docker_shell_run.split(":", 1)

        # 构建完整的命令：run.sh test_model test_weight test_seed test_method
        shell_command = f"{script_path} {mission_id} {test_model} {test_weight} {test_seed} {test_method} {timeout}"

        # 拼接容器ID和命令
        shell_path = f"{container_id}:{shell_command}"

        #shell_path = f"{container_id}:{script_path}"

        upload_files_to_docker(file_paths, container_id)

        exec_docker_container_shell_detach_v2(shell_path)

        return {
            "code": 200,
            "message": "任务已开始执行",
            "data": {
                "status": 1
            }
        }
    else:
        return {
            "code": 400,
            "message": "POST参数有误",
            "data": {
                "status": 2
            }
        }

## mode5: 获取被测对象的模型权重文件列表、对抗方法列表的数据源
@cross_origin()
@app.route('/check_model', methods=['GET'])
def check_model():
    print_info()
    param = request_params()
    test_model = param.get("test_model")

    model_dict = init_read_yaml_for_model_duplicate()

    test_methods = model_dict[test_model].get('test_method', [])

    # 构造对抗方法的 `label` 和 `value`
    test_method_list = [
        {
            "label": translate_test_method(method),
            "value": method
        }
        for method in test_methods
    ]

    if model_dict[test_model]['weight_download_addr']:
        return {
            "code": 200,
            "message": "模型权重文件、对抗方法列表",
            "data": {
                "weightList": model_dict[test_model]['weight_name'],
                #"methodList": model_dict[test_model]['test_method']
                "methodList": test_method_list
            }
        }
    else :
        return {
            "code": 400,
            "message": "模型权重文件、对抗方法列表收集失败",
            "data": {
                "weightList": [],
                "methodList": []
            }
        }

## mode4: 被测对象的模型权重文件zip包下载
@cross_origin()
@app.route('/weight_download', methods=['GET'])
def weight_download():
    print_info()
    param = request_params()
    test_model = param.get("test_model")

    model_dict = init_read_yaml_for_model_duplicate()

    # return jsonify({
    #     "message":10
    # })

    if isinstance(model_dict[test_model]['weight_download_addr'], list):
        zip_steam = multi_file_download_from_docker(model_dict[test_model].get('weight_download_addr'))
        return send_file(zip_steam, mimetype='application/zip', as_attachment=True, download_name=f"{test_model}_weights.zip")
        # return jsonify({
        #     "code": 200,
        #     "message": "模型权重文件下载, 多个地址",
        #      "weightDown": model_dict[test_model]['download_addr']
        # })

    elif isinstance(model_dict[test_model]['weight_download_addr'], str):
        zip_stream = download_zip_from_docker(model_dict[test_model].get('weight_download_addr'))
        return send_file(zip_stream, mimetype='application/zip', as_attachment=True, download_name=f"{test_model}_weights.zip")
        # return jsonify({
        #     "code": 200,
        #     "message": "模型权重文件下载",
        #      "weightDown": model_dict[test_model]['download_addr']
        # })
    else :
        return {
            "code": 400,
            "message": "模型权重文件下载类型不对"
        }

## mode3: 被测对象的模型权重文件数量
@cross_origin()
@app.route('/weight_number', methods=['GET'])
def weight_number():

    print_info()
    param = request_params()
    test_model = param.get("test_model")

    model_dict = init_read_yaml_for_model_duplicate()

    if isinstance(model_dict[test_model]['weight_number'], int):
        return {
            "code": 200,
            "message": "模型权重文件数量",
            "data": {
                "weightNum": model_dict[test_model]['weight_number']
            }
        }

    return {
        "code": 400,
        "message": "请换个模型，这个没有权重",
        "data": {
            "weightNum": 0
        }
    }

## mode2: 获取内置依赖库及其版本的数据源
@cross_origin()
@app.route('/depn_lib', methods=['GET'])
def depn_lib():

    print_info()

    model_dict = init_yaml_read_for_vulndig()

    data = [{"targetName": key, "versionList": \
        [f"{kk}-{str(vv)}" for kk, vv in model_dict[key]["dependents"].items()]} for key in model_dict.keys()]

    return {
        "code": 200,
        "message": "内置依赖库及其版本信息",
        "data": data
    }

##  mode1:获取被测对象的数据源
@cross_origin()
@app.route('/test_model', methods=['GET'])
def test_model():

    print_info()

    model_dict = init_read_yaml_for_model()

    data = list(model_dict.keys())

    return {
        "code": 200,
        "message": "被测对象的详细信息",
        "data": data
    }


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)

