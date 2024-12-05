import os
import io
import zipfile
import csv

from flask import Flask, request, jsonify
from functools import wraps
import yaml

import docker
import subprocess
import threading
import time


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
    yaml_file_path = './model_config/adver_white_box.yaml'

    with open(yaml_file_path, 'r') as yaml_file:
        data_dict = yaml.safe_load(yaml_file)

    # print(data_dict)

    new_data_dict = os.listdir("./model_config")
    for item in new_data_dict:
        if item != 'adver_white_box.yaml':
            # print(item)
            with open(os.path.join("./model_config", item)) as yaml_file:
                new_data = yaml.safe_load(yaml_file)
                update_dict_1_level(data_dict, new_data)

    #print(data_dict)
    data_dict = replace_param(data_dict)
    return data_dict


def init_read_yaml_for_model_duplicate():
    yaml_file_path = './model_config/adver_white_box.yaml'

    with open(yaml_file_path, 'r') as yaml_file:
        data_dict = yaml.safe_load(yaml_file)

    # print(data_dict)

    new_data_dict = os.listdir("./model_config")
    for item in new_data_dict:
        if item != 'adver_white_box.yaml':
            with open(os.path.join("./model_config", item)) as yaml_file:
                new_data = yaml.safe_load(yaml_file)
                update_dict_2_level(data_dict, new_data)

    # print(data_dict)
    data_dict = replace_param(data_dict)
    return data_dict


def init_yaml_read_for_vulndig():
    yaml_file_path = './vuln_config/vul_dig.yaml'

    with open(yaml_file_path, 'r') as yaml_file:
        data_dict = yaml.safe_load(yaml_file)

    parsed_data = {}
    for key, value in data_dict.items():
        if isinstance(value, dict):
            parsed_data[key] = {
                'version': value.get('version'),
                'dependents': value.get('dependents', {}),  # 原始嵌套结构
                'docker_container': value.get('docker_container'),
                'shell_command': value.get('shell_command'),
                'test_method': value.get('test_method'),
                'download_addr': value.get('download_addr')
            }

    return parsed_data


def model_classify(data):
    categories = {
        "Image_class": ["Alexnet_black_box", "Alexnet_GAN", "Vgg16", "Vgg16_fuzz", "Vgg19", "Resnet"],
        "Face_detect": ["Facenet", "Deepface", "InceptionResne"],
        "Obj_detect": ["Yolo3"],
        "Audio": ["Librispeech", "Wav2vec2"],
        "Reinforce": ["DQN"]
    }

    classified_data = []

    for model in data:
        for key, keywords in categories.items():
            if any(keyword.lower() in model.lower() for keyword in keywords):
                catrgory = key
                classified_data.append({"name": model, "type": catrgory})
                break
    return classified_data


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


def get_container_id(container_name, client=None):
    if client is None:
        client = docker.from_env()
    name_id = {}
    # 列出所有运行中的容器
    containers = client.containers.list(all=True)
    for container in containers:
        # print(container.id, container.image, container.status, container.name)
        name_id[container.name] = container.id
    # print(name_id)
    if container_name in name_id:
        return name_id[container_name]
    raise BaseException(f"Not found container whit name {container_name}")


def exec_docker_container_shell_detach(shell_path: str) -> str:
    client = docker.from_env()

    parts = shell_path.split(":")
    container_name = parts[0]

    container_id = get_container_id(container_name, client)

    print(f"container_name: {container_name}, container_id: {container_id}")

    script_path = parts[1]
    cmd = f"bash -c '{script_path} &'"

    os.system("docker start %s" % (container_id))

    container = client.containers.get(container_id)

    print(f"script_path: {cmd}")

    exec_result = container.exec_run(cmd=cmd, detach=True)

    if exec_result.exit_code == 0:
        # 将输出从bytes解码为字符串
        try:
            # 尝试解码输出为 UTF-8 字符串，忽略解码错误，若仍出现解码错误请直接返回原始字节数据
            if isinstance(exec_result.output, str):
                print(exec_result.output)
                return exec_result.output
            output = exec_result.output.decode('utf-8', errors='ignore')
            print("Script output:", output)
            return output
        except UnicodeDecodeError:
            # 如果解码失败，返回原始字节数据
            print("Received non-UTF-8 output")
            return exec_result.output
    else:
        print("Script execution failed with exit code:", exec_result.exit_code)
        print("Error output:", exec_result.output)
        error_message = f"Script execution failed with exit code: {exec_result.exit_code}\nError output: {exec_result.output}"
        return error_message


def container_run_cmd(res: list, cmd, ctn):
    exec_result = ctn.exec_run(cmd=cmd)
    if exec_result.exit_code == 0:
        # 将输出从bytes解码为字符串
        try:
            if isinstance(exec_result.output, str):
                print(exec_result.output)
                return exec_result.output
            # 尝试解码输出为 UTF-8 字符串，忽略解码错误
            output = exec_result.output.decode('utf-8', errors='ignore')
            print("Script output:", output)
            res.append(output)
            return output
        except UnicodeDecodeError:
            # 如果解码失败，返回原始字节数据
            print("Received non-UTF-8 output")
            res.append(exec_result.output)
            return exec_result.output
    else:
        print("Script execution failed with exit code:", exec_result.exit_code)
        print("Error output:", exec_result.output.decode('utf-8'))
        error_message = f"Script execution failed with exit code: {exec_result.exit_code}\nError output: {exec_result.output.decode('utf-8')}"
        res.append(error_message)
        return error_message


def exec_docker_container_shell_detach_v2(shell_path: str) -> str:
    client = docker.from_env()

    parts = shell_path.split(":")

    container_name = parts[0]

    container_id = get_container_id(container_name, client)

    script_path = parts[1]

    # 启动docker
    os.system(f"docker start {container_id}")

    print(f"docker:{container_id} run cmd: {script_path}")

    container = client.containers.get(container_id)

    wait_time = 2  # 等待2秒
    result = []
    threading.Thread(target=container_run_cmd, args=(result, script_path, container)).start()

    time0 = time.time()

    while time.time() - time0 < wait_time:
        if len(result) > 0:
            return result[0]
        time.sleep(0.2)
    return "process is  running"


def exec_docker_container_shell(shell_path: str) -> str:
    client = docker.from_env()

    parts = shell_path.split(":")

    container_name = parts[0]

    container_id = get_container_id(container_name, client)

    script_path = parts[1]

    os.system("docker start %s" % (container_id))

    container = client.containers.get(container_id)

    #print(f"script_path: {script_path}")

    exec_result = container.exec_run(cmd=script_path)

    if exec_result.exit_code == 0:
        # 将输出从bytes解码为字符串
        try:
            if isinstance(exec_result.output, str):
                print(exec_result.output)
                return exec_result.output
            # 尝试解码输出为 UTF-8 字符串，忽略解码错误
            output = exec_result.output.decode('utf-8', errors='ignore')
            #print("Script output:", output)
            return output
        except UnicodeDecodeError:
            # 如果解码失败，返回原始字节数据
            #print("Received non-UTF-8 output")
            return exec_result.output
    else:
        print("Script execution failed with exit code:", exec_result.exit_code)
        print("Error output:", exec_result.output.decode('utf-8'))
        error_message = f"Script execution failed with exit code: {exec_result.exit_code}\nError output: {exec_result.output.decode('utf-8')}"
        return error_message


def download_zip_from_docker(download_addr: str) -> io.BytesIO:
    client = docker.from_env()

    container_name, zip_path = download_addr.split(":")
    container_id = get_container_id(container_name, client)

    container = client.containers.get(container_id)
    bits,stat = container.get_archive(zip_path)

    file_stream = io.BytesIO()
    for chunk in bits:
        file_stream.write(chunk)
    file_stream.seek(0)

    return file_stream


def multi_file_download_from_docker(file_paths: list) -> io.BytesIO:
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


def upload_files_to_docker(file_paths, container_id, mission_id,target_path="/root/seed"):

    try:
        subprocess.run(["docker", "exec", container_id, "mkdir", "-p", target_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create directory in container: {e}")
        return

    # 拷贝文件到容器
    target_file_name = f"{mission_id}.zip"
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"File {file_path} does not exist or is not a file. Skipping...")
            continue

        try:
            # 使用 docker cp 进行拷贝
            subprocess.run(
                ["docker", "cp", file_path, f"{container_id}:{target_path}/{target_file_name}"],
                check=True
            )
            print(f"Uploaded {file_path} to container {container_id}:{target_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to copy {file_path} to container: {e}")


def replace_str(v: str, search_pool):
    while 0 <= v.find("${") < v.find("}"):
        start = v.find("${")
        end = v.find("}")
        rk = v[start + 2:end]
        rv = search_pool
        for it in rk.split("."):
            rv = rv.get(it)
        rk = "${" + rk + "}"
        try:
            nv = v.replace(rk, rv)
        except BaseException as e:
            nv = v.replace(rk, rv)
        v = nv
    return v



def replace_list(v: list, search_pool):
    for index in range(len(v)):
        iv = v[index]
        if isinstance(iv, str):
            v[index] = replace_str(iv, search_pool)
        if isinstance(iv, list):
            v[index] = replace_list(iv, search_pool)
        if isinstance(iv, dict):
            v[index] = replace_param(iv, search_pool)
    return v


def replace_param(data_dict: dict, search_pool=None):
    """
    替换${}占位符参数
    :param data_dict:
    :return:
    """
    if search_pool is None:
        search_pool = data_dict
    ks = data_dict.keys()
    for k in ks:
        v = data_dict.get(k)
        if isinstance(v, str):
            data_dict[k] = replace_str(v, search_pool)
            # while 0 <= v.find("${") < v.find("}"):
            #     start = v.find("${")
            #     end = v.find("}")
            #     rk = v[start+2:end]
            #     rv = search_pool
            #     for it in rk.split("."):
            #         rv = rv.get(it)
            #     rk = "${" + rk + "}"
            #     nv = v.replace(rk, rv)
            #     data_dict[k] = nv
            #     v = data_dict.get(k)
        elif isinstance(v, list):
            data_dict[k] = replace_list(v, search_pool)

        elif isinstance(v, dict):
            replace_param(v, search_pool)
    return data_dict




def adver_verify_parall(test_model:str, test_method:str) -> bool:
    """
    这个函数用来校验新发送的任务是否能够执行。因为同一种任务类型同一种方法不支持多个进程同时运行。
    因此在收到任务请求后，提取请求中的test_method,test_model，和csv中记录任务状态进行对比。
    若有同类型任务在执行，则返回False，意味当前任务不能执行。若返回True，则说明当前任务能执行
    """

    # 获取各种模型各种方法的字典
    yaml_file_path = './model_config/type_status.yaml'

    with open(yaml_file_path, 'r') as yaml_file:
        all_type_dict = yaml.safe_load(yaml_file)

    for item in all_type_dict['model']:
        all_type_dict['model'][item] = [s.lower() for s in all_type_dict['model'][item]]
    for item in all_type_dict['method']:
        all_type_dict['method'][item] = [s.lower() for s in all_type_dict['method'][item]]

    print(all_type_dict)

    # 获取现有任务的信息,并进行校验.具体的逻辑是，有3个button,同时满足则不能开始此任务,此函数return false.
    # 三个button，分别为model,method,执行状态的判断,任务状态中1代表over
    csv_file = 'Adver_gen_missions_DBSM.csv'
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            button_1 = 0
            button_2 = 0

            exist_test_model = row['test_model'].lower()
            exist_test_method = row['test_method'].lower()

            print(row['mission_id'], row['test_model'], row['test_method'], row['mission_status'])
            # 校验当前行是否状态为1，为1则已经结束，跳转下一行
            button_3 = int(row['mission_status'])
            if button_3 == 1: continue

            ## 校验新任务是否和现有任务面向同一种模型
            for item in all_type_dict['model']:
                if (test_model.lower() in all_type_dict['model'][item]) and (exist_test_model in all_type_dict['model'][item]):
                    button_1 = 1

            ## 校验新任务是否和现有任务使用同一类方法
            for item in all_type_dict['method']:
                if (test_method.lower() in all_type_dict['method'][item]) and (exist_test_method in all_type_dict['method'][item]):
                    button_2 = 1
            # print(row['mission_id'], row['test_model'], row['test_method'], row['mission_status'], button_1, button_2, button_3)
            if bool(button_1 and button_2 and button_3):
                return False
    csv_file = 'Eval_missions_DBSM.csv'
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            eval_test_model = row['test_model'].lower()
            eval_test_method = row['test_method'].lower()
            eval_test_status = int(row['mission_status'])

            if eval_test_model == test_model.lower() and eval_test_method == test_method.lower() and eval_test_status == 2:
                return False
    
    csv_file = 'Enhance_missions_DBSM.csv'
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            eval_test_model = row['test_model'].lower()
            eval_test_method = row['test_method'].lower()
            eval_test_status = int(row['mission_status'])

            if eval_test_model == test_model.lower() and eval_test_method == test_method.lower() and eval_test_status == 2:
                return False

        return True

def eval_verify_parall(test_model:str, test_method:str) -> bool:
    csv_file = 'Adver_gen_missions_DBSM.csv'
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            eval_test_model = row['test_model'].lower()
            eval_test_method = row['test_method'].lower()
            eval_test_status = int(row['mission_status'])

            if eval_test_model == test_model.lower() and eval_test_method == test_method.lower() and eval_test_status == 2:
                return False
    
    csv_file = 'Enhance_missions_DBSM.csv'
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            eval_test_model = row['test_model'].lower()
            eval_test_method = row['test_method'].lower()
            eval_test_status = int(row['mission_status'])

            if eval_test_model == test_model.lower() and eval_test_method == test_method.lower() and eval_test_status == 2:
                return False

        return True
    
def enhance_verify_parall(test_model:str, test_method:str) -> bool:
    csv_file = 'Adver_gen_missions_DBSM.csv'
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            eval_test_model = row['test_model'].lower()
            eval_test_method = row['test_method'].lower()
            eval_test_status = int(row['mission_status'])

            if eval_test_model == test_model.lower() and eval_test_method == test_method.lower() and eval_test_status == 2:
                return False
    
    csv_file = 'Eval_missions_DBSM.csv'
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            eval_test_model = row['test_model'].lower()
            eval_test_method = row['test_method'].lower()
            eval_test_status = int(row['mission_status'])

            if eval_test_model == test_model.lower() and eval_test_method == test_method.lower() and eval_test_status == 2:
                return False

        return True

if __name__ == "__main__":
    print(eval_verify_parall("vgg16","FGSM"))
    # dict = init_yaml_read_for_vulndig()
    # print(dict)
    # print(dict["Pytorch"].get('docker_container'))
    # print(dict["Pytorch"]['docker_container'])

    # print(data_dict["Vgg16"]["docker_container"])
    # exec_docker_container_shell(data_dict["Vgg16"]["docker_container"])
