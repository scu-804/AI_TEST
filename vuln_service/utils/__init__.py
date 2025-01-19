import subprocess
from datetime import datetime
import re

import os
import sys
import logging
import colorlog

from vuln_service.config import LOGGING_LEVEL
from .container import create_ctn_dir_if_nonexist, container_run_script


# from vuln_service.entities import RoutineEntry, RoutineStatus


FUZZ_DIR = "/fuzz"
FUZZ_LOG = "fuzz_log"
# note that tailing '/' is needed
# CRASH_DIR = "/fuzz/crashes/"

REQ_NAME = "requirements.txt"

LOGGER_NAME = "vuln_service"
# BASE_DIR = sys.path[0]

# container_cwd: dict[str, str] = {
#     "yqy_atheris_pt": "/root/pytorch",
#     "yqy_atheris_tf": "/root",
#     "yqy_atheris_keras": "/root/fuzz",
#     "yqy_atheris_np": "/root",
#     "yqy_fuzz_opencv": "/out",
#     "yqy_atheris_pandas": "/root",
#     "yqy_atheris_pillow": "/root/Pillow",
#     "yqy_atheris_scipy": "/root",
# }


# def output_container_cwd() -> None:
#     logger.info("printing container_cwd...")
#     for key, val in container_cwd.items():
#         print(f'"{key}": "{val}",')
#
#
# def get_container_cwd(container: str) -> str | None:
#     return container_cwd.get(container)


# def add_container_cwd(container: str, cwd: str) -> bool:
#     if container in container_cwd:
#         return False
#
#     container_cwd[container] = cwd
#     return True

handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s[%(levelname)s]%(reset)s %(asctime)s - %(message)s"
    )
)

logger = colorlog.getLogger(LOGGER_NAME)
logger.addHandler(handler)

# set logging level
log_level = LOGGING_LEVEL
logger.setLevel(getattr(logging, log_level, logging.INFO))


def path_formalize(*paths) -> str:
    for path in paths:
        assert isinstance(path, str)
    return os.path.join(sys.path[0], *paths)


def dir_formalize(*paths) -> str:
    dir_path = path_formalize(*paths)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    return dir_path


def get_data_dir() -> str:
    return dir_formalize("data")


def get_time_suffix() -> str:
    now = datetime.now()
    date_time_string = now.strftime("%Y-%m-%d:%H:%M:%S")
    return date_time_string
