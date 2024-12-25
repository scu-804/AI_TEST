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


def container_run_script(
    container: str, script: str, output: bool
) -> subprocess.CompletedProcess[bytes]:
    docker_cmd = f"docker exec -i {container} bash -s"
    return subprocess.run(
        docker_cmd.split(), input=script.encode(), capture_output=output
    )


def get_log_name(routine_name: str) -> str:
    return f"{routine_name}_{FUZZ_LOG}"


def get_routine_fuzz_log_path(routine: RoutineEntry) -> str:
    log_name = get_log_name(routine.get_name())
    return os.path.join(FUZZ_DIR, log_name)


def get_routine_backup_fuzz_log_path(routine: RoutineEntry) -> str:
    log_name = get_log_name(routine.get_name())

    # get fuzz log paths
    script = f"""
    find {FUZZ_DIR} -mindepth 1 -maxdepth 1 -type f -name '{log_name}_*'
    """
    proc = container_run_script(routine.container, script, True)
    output = proc.stdout.decode()
    lines = [line.strip() for line in output.splitlines()]
    assert len(lines) > 0, f"No backup fuzz log for routine {routine.get_name()}"
    lines.sort()

    log_path = lines[-1]
    return log_path


def get_routine_crash_dir_name(routine_name: str) -> str:
    return f"{routine_name}_crashes"


def get_routine_crash_dir(routine_name: str) -> str:
    """
    base fuzz_dir with routine_name and tailing '/'
    """
    return os.path.join(FUZZ_DIR, get_routine_crash_dir_name(routine_name))


def get_routine_corpus_dir(routine_name: str) -> str:
    return os.path.join(FUZZ_DIR, f"{routine_name}_corpus")


def get_pid_name(routine_name: str) -> str:
    return f"{routine_name}_pid"


def get_pid_path(routine: RoutineEntry) -> str:
    pid_name = get_pid_name(routine.get_name())
    return f"{FUZZ_DIR}/{pid_name}"


def get_crash_zip_path(routine_name: str) -> str:
    return os.path.join(FUZZ_DIR, f"{routine_name}.zip")


def check_exit_status(routine: RoutineEntry) -> ExitStatus:
    """
    1 finished, 2 running
    """
    script = get_pid_check_script(routine)

    proc = container_run_script(routine.container, script, False)
    # pid file is cleaned
    if proc.returncode == 2:
        return ExitStatus.CLN
    # query success
    if proc.returncode == 0:
        return ExitStatus.RUN

    # pid file exists and query fails
    return ExitStatus.PAR


pid_check_script_template = """
fuzz_dir='{fuzz_dir}'
if [[ ! -d "$fuzz_dir" ]]; then
  mkdir "$fuzz_dir"
fi

pid_path="$fuzz_dir"/{pid_name}
if [[ ! -f "$pid_path" ]]; then 
    exit 2
fi

pid=$(cat "$pid_path")

ps -p "$pid"
"""


def get_pid_check_script(routine: RoutineEntry) -> str:
    pid_name = get_pid_name(routine.get_name())
    return pid_check_script_template.format(fuzz_dir=FUZZ_DIR, pid_name=pid_name)


def get_new_comming_crash_name(routine: RoutineEntry) -> str | None:
    """
    returns filename of the new comming crash file
    """
    crash_dir = get_routine_crash_dir(routine_name=routine.get_name())
    script = f"""
    crash_dir='{crash_dir}'
    time_thresh="$(date -d '{CRASH_FILE_TIMEOUT} seconds ago' '+%Y-%m-%d %H:%M:%S')"
    find "$crash_dir" -type f -newermt "$time_thresh"
    """
    proc = container_run_script(routine.container, script, True)
    output = proc.stdout.decode()
    lines = output.splitlines()
    cnt = 0

    fpath = None
    for line in lines:
        line = line.strip()
        if len(line) == 0:
            continue
        cnt += 1
        if cnt > 1:
            assert (
                False
            ), f"More than 1 new crash files occured for routine {routine.get_name()}, please adjust timeout threshold."
        fpath = line
    if fpath is None:
        return None
    else:
        return os.path.basename(fpath)


# def check_exit_reason(routine: RoutineEntry) -> ExitReason:
#     fname = get_new_comming_crash_name(routine)
#     if fname is None:
#         logger.info(f"Routine {routine.get_name()} stopped: Unexpected error occured")
#         return ExitReason.OTHER
#     if fname.startswith("crash-"):
#         logger.info(f"Routine {routine.get_name()} stopped: new crash occured")
#         return ExitReason.SAN
#     if fname.startswith("oom-"):
#         logger.info(f"Routine {routine.get_name()} stopped: oom error occured")
#         return ExitReason.OOM
#     assert False, f"Unexpected crash file name: {fname} at routine {routine.get_name()}"


def get_time_suffix() -> str:
    now = datetime.now()
    date_time_string = now.strftime("%Y-%m-%d:%H:%M:%S")
    return date_time_string
