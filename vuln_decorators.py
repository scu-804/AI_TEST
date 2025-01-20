from functools import wraps
from flask import request,jsonify
from vuln_service.start import start_routine
from utils import vuln_dig_verify, harness_upload
from vuln_service.entities import RoutineEntry
import logging

logger = logging.getLogger(__name__)

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

def vulndig_start_decorator(yaml_reader):
    """
    :param yaml_reader: 用于读取 YAML 配置文件的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            params = request_params()
            get_url()
            
            #params = request.get_json()
            lib_name = params.get('lib_name')
            lib_verison = params.get('lib_version')
            harness_file = request.files.getlist('harness_files')
            if vuln_dig_verify(lib_name) == False:
                return jsonify({
                    "code": 400,
                    "message": "该库已有挖掘任务正在进行",
                    "data": {"status": 2},
                })
            
            if not lib_name:
                return jsonify({
                    "code": 400,
                    "message": "未收到lib_name参数",
                    "data": {"status": 2},
                })
            vuln_dict = yaml_reader()
            lib_config = vuln_dict.get(lib_name)

            if not lib_config:    
                return jsonify({
                    "code": 400,
                    "message": "lib_name参数有误",
                    "data": {"status": 2},
                })

            docker_container = lib_config.get('docker_container')
            shell_command = lib_config.get('shell_command')

            if not docker_container or not shell_command:
                return jsonify({
                    "code": 400,
                    "message": "yaml文件参数读取失败",
                    "data": {"status": 2},
                })
            
            harn_path = harness_upload(harness_file)

            # 调用 start 函数启动 Docker 容器
            logger.info(f"Starting Docker container '{docker_container}' with command '{shell_command}'")

            entry = RoutineEntry(container=docker_container, lib_name=lib_name, lib_version=lib_verison, harn_path=harn_path)
            time_suffix = entry.time_suffix

            result = start_routine(entry)

            print(result)

            # 执行被装饰的接口逻辑
            return func(*args, result=result, harn_path=harn_path, time_suffix=time_suffix,**kwargs)
        return wrapper
    return decorator