from functools import wraps
from flask import request,jsonify
from vuln_service.start import start
import logging

logger = logging.getLogger(__name__)

def vulndig_start_decorator(yaml_reader):
    """
    :param yaml_reader: 用于读取 YAML 配置文件的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lib_name = request.form.get('lib_name')
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

            # 调用 start 函数启动 Docker 容器
            logger.info(f"Starting Docker container '{docker_container}' with command '{shell_command}'")
            start(docker_container, shell_command)

            # 执行被装饰的接口逻辑
            return func(*args, **kwargs)
        return wrapper
    return decorator