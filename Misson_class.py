import csv
from flask import request
import uuid


# 用一个类来保存任务。用一个csv文件充当数据库，来记录所有出现过的任务。
# !!!!!!!  这里有一个隐患：任务的更新和记录是通过读取csv, 覆盖重写csv实现的。 !!!!!!!!
# !!!!!!!  如果超过1个进程执行这个文件中的类管理函数，读写csv，可能会出现一些难以预料的错误。  !!!!!!!!


class Mission:

    def __init__(self, mission_id, test_model, test_weight, test_seed, test_method, timeout, mission_status):
        self.mission_id = mission_id
        self.test_model = test_model
        self.test_weight = test_weight
        self.test_seed = test_seed
        self.test_method = test_method
        self.timeout = timeout
        self.mission_status = mission_status

    def update_status(self, new_status):
        if int(self.mission_status) != 1:                ##  1 means mission is over, that could not be changed
            self.mission_status = new_status
        else:
            print('Mission is over!!  This status could not be changed !!')


class MissionManager:

    def __init__(self, csv_file):
        self.missions = {}
        self.csv_file = csv_file
        self.load_missions_from_csv()

    def load_missions_from_csv(self):
        try:
            with open(self.csv_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.missions[row['mission_id']] = Mission(
                        row['mission_id'],
                        row['test_model'],
                        row['test_weight'],
                        row['test_seed'],
                        row['test_method'],
                        int(row['timeout']),
                        int(row['mission_status'])
                    )
        except FileNotFoundError:
            pass  # CSV文件不存在则忽略
        except BaseException as e:
            pass  # 忽略错误

    def save_missions_to_csv(self):
        with open(self.csv_file, mode='w', newline='') as file:
            fieldnames = ['mission_id', 'test_model', 'test_weight', 'test_seed', 'test_method', 'timeout', 'mission_status']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for mission in self.missions.values():
                row = {
                    'mission_id': mission.mission_id,
                    'test_model': mission.test_model,
                    'test_weight': mission.test_weight,
                    'test_seed': mission.test_seed,
                    'test_method': mission.test_method,
                    'timeout': str(mission.timeout),
                    'mission_status': str(mission.mission_status)
                }
                writer.writerow(row)

    def add_or_update_mission(self, mission):
        self.missions[mission.mission_id] = mission
        self.save_missions_to_csv()

class Eval_Mission(Mission):
    def __init__(self, mission_id, test_model, test_method, mission_status):
        super().__init__(mission_id, test_model, None, None, test_method, None, mission_status)
        # 这里只保存 mission_id, test_model, test_method 和 mission_status
        # test_weight, test_seed, timeout 在评估任务中不需要

    def update_status(self, new_status):
        self.mission_status = new_status

class Eval_MissionManager(MissionManager):
    def __init__(self, csv_file):
        # 使用对抗样本生成任务 CSV 文件初始化
        super().__init__('Adver_gen_missions_DBSM.csv')  
        self.eval_missions = {}  # 用于存储评估任务
        self.load_eval_missions_from_csv(csv_file)

    def load_eval_missions_from_csv(self,csv_file):
        try:
            with open(csv_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # 读取必要的字段来创建 Eval_Mission 对象
                    eval_mission = Eval_Mission(
                        row['mission_id'],
                        row['test_model'],
                        row['test_method'],
                        row['mission_status']  # 直接从原始任务的状态来创建
                    )
                    # 将评估任务添加到字典中
                    self.eval_missions[eval_mission.mission_id] = eval_mission
                    print(f"Loaded Eval_Mission: {eval_mission.mission_id}")
        except FileNotFoundError:
            pass  # 如果文件不存在则忽略
        except Exception as e:
            print(f"Error loading missions from CSV: {e}")

    def update_eval_mission(self, mission_id, test_model, test_method, mission_status):
        if mission_id not in self.eval_missions:
            eval_mission = Eval_Mission(
                mission_id,
                test_model,
                test_method,
                mission_status
            )
            self.eval_missions[mission_id] = eval_mission

    def save_eval_missions_to_csv(self):
        try:
            with open('Eval_missions_DBSM.csv', mode='w', newline='') as file:
                fieldnames = ['mission_id', 'test_model', 'test_method', 'mission_status']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for mission in self.eval_missions.values():
                    row = {
                        'mission_id': mission.mission_id,
                        'test_model': mission.test_model,
                        'test_method': mission.test_method,
                        'mission_status': str(mission.mission_status)
                    }
                    writer.writerow(row)
        except Exception as e:
            print(f"Error saving eval missions to CSV: {e}")


def print_missions(csv_file='Adver_gen_missions_DBSM.csv'):
    try:
        with open(csv_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            print("Mission ID | Test Model | Test Weight | Test Seed             | Test Method | Timeout | Mission Status")
            print("----------------------------------------------------------------------------------------------------------------")
            for row in reader:
                print(f"{row['mission_id']:10} | {row['test_model']:10} | {row['test_weight']:11} | {row['test_seed']}\
                 | {row['test_method']:11} | {row['timeout']:8} | {row['mission_status']:15}")
    except FileNotFoundError:
        print(f"The file {csv_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def print_enhance_missions(csv_file='Enhance_missions_DBSM.csv'):
    try:
        with open(csv_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            print("Mission ID | Test Model | Test Weight | Test Seed             | Test Method | Timeout | Mission Status| Enhance_id")
            print("----------------------------------------------------------------------------------------------------------------")
            for row in reader:
                print(f"{row['mission_id']:10} | {row['test_model']:10} | {row['test_weight']:11} | {row['test_seed']}\
                 | {row['test_method']:11} | {row['timeout']:8} | {row['mission_status']:15} | {row['enhance_id']:15}")
    except FileNotFoundError:
        print(f"The file {csv_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


class Enhance_Mission(Mission):

    def __init__(self, mission_id, test_model, test_weight, test_seed, test_method, timeout, mission_status, enhance_id=None):
        super().__init__(mission_id, test_model, test_weight, test_seed, test_method, timeout, mission_status)
        self.enhance_id = enhance_id if enhance_id else None

    def update_status(self, new_status):
        self.mission_status = new_status


class Enhance_MissionManager(MissionManager):
    def __init__(self, csv_file):
        super().__init__(csv_file)
        self.csv_file = 'Enhance_missions_DBSM.csv'
        self.enhance_mission_dict = {}
        self.load_missions_from_csv_enhance()

    def load_missions_from_csv_enhance(self):
        try:
            with open(self.csv_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    enhance_mission = Enhance_Mission(
                        row['mission_id'],
                        row['test_model'],
                        row['test_weight'],
                        row['test_seed'],
                        row['test_method'],
                        int(row['timeout']),
                        int(row['mission_status']),
                        enhance_id=row.get('enhance_id', None)
                    )
                    self.enhance_mission_dict[enhance_mission.enhance_id] = enhance_mission
        except FileNotFoundError:
            pass  # CSV文件不存在则忽略

    def update_enhance_mission_dict(self, mission_id, enhance_id, mission_status):
        mission_id = str(mission_id)
        enhance_id = str(enhance_id)
        if enhance_id not in self.enhance_mission_dict.keys() and mission_id in self.missions.keys():
            self.enhance_mission_dict[enhance_id] = Enhance_Mission(
                        self.missions[mission_id].mission_id,
                        self.missions[mission_id].test_model,
                        self.missions[mission_id].test_weight,
                        self.missions[mission_id].test_seed,
                        self.missions[mission_id].test_method,
                        int(self.missions[mission_id].timeout),
                        int(mission_status),
                        enhance_id)

    def save_missions_to_csv(self):
        with open(self.csv_file, mode='w', newline='') as file:
            fieldnames = ['mission_id', 'test_model', 'test_weight', 'test_seed', 'test_method', 'timeout', 'mission_status', 'enhance_id']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for mission in self.enhance_mission_dict.values():
                row = {
                    'mission_id': mission.mission_id,
                    'test_model': mission.test_model,
                    'test_weight': mission.test_weight,
                    'test_seed': mission.test_seed,
                    'test_method': mission.test_method,
                    'timeout': str(mission.timeout),
                    'mission_status': str(mission.mission_status),
                    'enhance_id': mission.enhance_id
                }
                writer.writerow(row)

class VulnDigMission:
    def __init__(self, mission_id, container_id, lib_name, lib_version,mission_status):
        self.mission_id = mission_id
        self.container_id = container_id
        self.status = mission_status
        self.lib_name = lib_name
        self.lib_version = lib_version

    def update_status(self, new_status):
        if int(self.status) != 1:  # 1 表示任务完成，状态无法更改
            self.status = new_status
        else:
            print('Mission is over!! This status cannot be changed!!')

class VulnDigMissionManager:
    def __init__(self, csv_file):
        self.missions = {}
        self.csv_file = csv_file
        self.load_missions_from_csv()

    def load_missions_from_csv(self):
        try:
            with open(self.csv_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.missions[row['mission_id']] = VulnDigMission(
                        row['mission_id'],
                        row['container_id'],
                        row['lib_name'],
                        row['lib_version'],
                        int(row['status'])
                    )
        except FileNotFoundError:
            pass  # 如果CSV文件不存在，忽略错误

    def save_missions_to_csv(self):
        with open(self.csv_file, mode='w', newline='') as file:
            fieldnames = ['mission_id', 'container_id', 'lib_name', 'lib_version','status']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for mission in self.missions.values():
                row = {
                    'mission_id': mission.mission_id,
                    'container_id': mission.container_id,
                    'lib_name': mission.lib_name,
                    'lib_version': mission.lib_version,
                    'status': str(mission.status)
                }
                writer.writerow(row)

    def add_or_update_mission(self, mission):
        self.missions[mission.mission_id] = mission
        self.save_missions_to_csv()


if __name__ == "__main__":
    mission_id = str(5432123)
    #eval_manager = Eval_MissionManager('Adver_gen_missions_DBSM.csv')
    eval_manager = Eval_MissionManager('Eval_missions_DBSM.csv')
    eval_mission = eval_manager.eval_missions[mission_id]
    print(eval_mission)
    eval_mission.update_status(2)
    eval_manager.save_eval_missions_to_csv()
    # enhance_manager = Enhance_MissionManager('Adver_gen_missions_DBSM.csv')
    # print(enhance_manager.missions)
    # enhance_manager.update_enhance_mission_dict(12, 777)
    # enhance_manager.save_missions_to_csv()
    # print_missions()
    # print("\n")
    # print_enhance_missions()

