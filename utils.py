import os
import io
import zipfile

from flask import Flask, request, jsonify
from functools import wraps
import yaml

import docker
import subprocess


def return_0_1(code: int =200 , message: str = "done", data: dict = {"v":"k"}):
    #  this code for returning response of POST(GET) with json format
    response = {
        "code": code,
        "message": message,
        "data": data
    }

    return jsonify(response)


def share_weight(contain_id, shared_path):
    #  this function for sharing weights of one model generated by different adversarial methods.
    return 0


def update_dict_1_level(original, new):
    # just update dict key
    for key, value in new.items():
        if key not in original:
            original[key] = value


def update_dict_2_level(original, new):
    # if new dict's model is same with origin, update the 2 level key 'weight_number', 'weight_name',
    # 'test_method', and 'download_addr'
    for key, value in new.items():
        if key not in original:
            original[key] = value
        else:
            if isinstance(original[key]['weight_number'], int):
                original[key]['weight_number'] = original[key]['weight_number'] + new[key]['weight_number']
            else:
                original[key]['weight_number'] = int(original[key]['weight_number']) + int(new[key]['weight_number'])

            for kkey in ['weight_name', 'test_method', 'download_addr']:
                if isinstance(original[key][kkey], str) and isinstance(new[key][kkey], str):
                    original[key][kkey] = [original[key][kkey], new[key][kkey]]
                elif isinstance(original[key][kkey], list) and isinstance(new[key][kkey], str):
                    original[key][kkey].append(new[key][kkey])
                elif isinstance(original[key][kkey], str) and isinstance(new[key][kkey], list):
                    original[key][kkey] = new[key][kkey].append(original[key][kkey])
                elif isinstance(original[key][kkey], list) and isinstance(new[key][kkey], list):
                    original[key][kkey].extend(new[key][kkey])


def init_read_yaml_for_model():
    yaml_file_path = './config/adver_white_box.yaml'

    with open(yaml_file_path, 'r') as yaml_file:
        data_dict = yaml.safe_load(yaml_file)

    # print(data_dict)

    new_data_dict = os.listdir("./config")
    for item in new_data_dict:
        if item != 'adver_white_box.yaml':
            # print(item)
            with open(os.path.join("./config", item)) as yaml_file:
                new_data = yaml.safe_load(yaml_file)
                update_dict_1_level(data_dict, new_data)

    # print(data_dict)
    return data_dict


def init_read_yaml_for_model_duplicate():
    yaml_file_path = './config/adver_white_box.yaml'

    with open(yaml_file_path, 'r') as yaml_file:
        data_dict = yaml.safe_load(yaml_file)

    # print(data_dict)

    new_data_dict = os.listdir("./config")
    for item in new_data_dict:
        if item != 'adver_white_box.yaml':
            with open(os.path.join("./config", item)) as yaml_file:
                new_data = yaml.safe_load(yaml_file)
                update_dict_2_level(data_dict, new_data)

    # print(data_dict)
    return data_dict


def update_yaml():
    ## do we need this funcion?  To be added
    return 0


def translate_test_method(method):
    translations = {
        "FGSM": "快速梯度符号法",
        "PGD": "投影梯度下降",
        "CW": "CW攻击",
        "CW2": "CW2攻击",
        "DeepFool": "深度愚弄法",
        "fuzzing": "模糊测试"
    }
    return translations.get(method, method)


def exec_docker_container_shell(shell_path:str) -> str:
    client = docker.from_env()

    parts = shell_path.split(":")
    container_id = parts[0]
    #  你可以给docker容器里的shell脚本提供参数，约定好就行
    #  script_path = parts[1] + ' status'    ##  option: {start|stop|status|restart}

    script_path = parts[1]
    cmd = f"bash -c '{script_path} &"

    # print("容器 ID:", container_id)
    # print("脚本路径:", script_path)
    # print("docker start %s" % (container_id))
    os.system("docker start %s" % (container_id))

    container = client.containers.get(container_id)
    exec_result = container.exec_run(cmd=cmd, detach=True)

    if exec_result.exit_code == 0:
        # 将输出从bytes解码为字符串
        try:
            # 尝试解码输出为 UTF-8 字符串，忽略解码错误，若仍出现解码错误请直接返回原始字节数据
            output = exec_result.output.decode('utf-8', errors='ignore')
            print("Script output:", output)
            return output
        except UnicodeDecodeError:
            # 如果解码失败，返回原始字节数据
            print("Received non-UTF-8 output")
            return exec_result.output
    else:
        print("Script execution failed with exit code:", exec_result.exit_code)
        print("Error output:", exec_result.output.decode('utf-8'))
        error_message = f"Script execution failed with exit code: {exec_result.exit_code}\nError output: {exec_result.output.decode('utf-8')}"
        return error_message


def download_zip_from_docker(download_addr:str) -> io.BytesIO:
    container_id, zip_path = download_addr.split(":")

    client = docker.from_env()
    container = client.containers.get(container_id)
    bits,stat = container.get_archive(zip_path)

    file_stream = io.BytesIO()
    for chunk in bits:
        file_stream.write(chunk)
    file_stream.seek(0)

    return file_stream


def multi_file_download_from_docker(file_paths:list) -> io.BytesIO:
    client = docker.from_env()
    container_id = file_paths[0].split(":")[0]
    container = client.containers.get(container_id)

    file_sream = io.BytesIO()

    with zipfile.ZipFile(file_sream, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            file_path = file_path.split(":")[1]
            bits, stat = container.get_archive(file_path)
            file_name_with_ext = file_path.split("/")[-1]
            file_name, _ = os.path.splitext(file_name_with_ext)
            zipf.writestr(f"{file_name}.tar", b''.join(bits))
    
    file_sream.seek(0)

    return file_sream


def upload_files_to_docker(file_paths, container_id, target_path="/root/file"):

    try:
        subprocess.run(["docker", "exec", container_id, "mkdir", "-p", target_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create directory in container: {e}")
        return

    # 拷贝文件到容器
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"File {file_path} does not exist or is not a file. Skipping...")
            continue

        try:
            # 使用 docker cp 进行拷贝
            subprocess.run(
                ["docker", "cp", file_path, f"{container_id}:{target_path}"],
                check=True
            )
            print(f"Uploaded {file_path} to container {container_id}:{target_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to copy {file_path} to container: {e}")


if __name__ == "__main__":
    data_dict = init_read_yaml_for_model()

    print(data_dict["Vgg16"]["docker_container"])
    exec_docker_container_shell(data_dict["Vgg16"]["docker_container"])