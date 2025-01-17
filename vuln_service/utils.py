import subprocess
from datetime import datetime
import re

import os
import sys
import logging
import colorlog

from vuln_service.config import LOGGING_LEVEL
from .config import CRASH_FILE_TIMEOUT
from vuln_service.entities import RoutineEntry, RoutineStatus

from .entities import ExitReason, ExitStatus

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


def create_ctn_dir_if_nonexist(dir_path: str, container: str) -> None:
    # ensure dir path passed in is absolute path
    assert dir_path.startswith(
        "/"
    ), f"dir_path {dir_path} passed in is not absolute path"
    script = f"""
if [[ ! -d {dir_path} ]]; then 
mkdir -p {dir_path}
fi
    """
    container_run_script(container, script, False)


def container_run_script(
    container: str, script: str, output: bool
) -> subprocess.CompletedProcess[bytes]:
    docker_cmd = f"docker exec -i {container} bash -s"
    return subprocess.run(
        docker_cmd.split(), input=script.encode(), capture_output=output
    )


def get_crash_zip_path(routine_name: str) -> str:
    return os.path.join(FUZZ_DIR, f"{routine_name}.zip")


def check_exit_status(routine: RoutineEntry) -> ExitStatus:
    """
    1 finished, 2 running
    """
    pid_path = routine.get_pid_path()
    script = f"""
pid_path={pid_path}
if [[ ! -f "$pid_path" ]]; then 
    exit 2
fi

pid=$(cat "$pid_path")

ps -p "$pid"
    """

    proc = container_run_script(routine.container, script, False)
    # pid file is cleaned
    if proc.returncode == 2:
        return ExitStatus.CLN
    # query success
    if proc.returncode == 0:
        return ExitStatus.RUN

    # pid file exists and query fails
    return ExitStatus.PAR


def get_time_suffix() -> str:
    now = datetime.now()
    date_time_string = now.strftime("%Y-%m-%d:%H:%M:%S")
    return date_time_string
