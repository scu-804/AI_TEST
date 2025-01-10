import yaml
import os


with open(os.path.join("./model_config", "type_status.yaml")) as yaml_file:
    new_data = yaml.safe_load(yaml_file)

print(new_data)