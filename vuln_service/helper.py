import os
import json

import ipdb

from vuln_service.entities import RoutineEntry

from .entities import routine_entry_list

from .utils import logger

from vuln_service.utils import container_run_script, get_data_dir


def get_condarc_path() -> str:
    dir = get_data_dir()
    return os.path.join(dir, ".condarc")


def copy_condarc(container: str) -> None:
    fpath = get_condarc_path()
    os.system(f"docker cp {fpath} {container}:/root/.condarc")


def show_conda_env_name(container: str) -> None:
    script = "source /root/.bashrc && echo $CONDA_DEFAULT_ENV"
    logger.info(f"Name of conda env in {container}")
    proc = container_run_script(container, script, False)
    assert proc.returncode == 0, f"failed at {container}"


def set_pip_index(container: str) -> None:
    script = "pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
    proc = container_run_script(container, script, False)
    if proc.returncode != 0:
        logger.error(f"pip index configure failed in {container}")
    else:
        logger.info(f"pip index configure succeeded in {container}")


def check_container_cd(container: str) -> None:
    script = "cat /root/.bashrc"
    proc = container_run_script(container, script, True)
    content = proc.stdout.decode()
    flag = "cd" in content
    if not flag:
        logger.error(f"bashrc in {container} missing cd command")
    else:
        logger.info(f"cd command in {container} found")


def conda_init(container: str) -> None:
    script = "source /root/.bashrc && conda init"
    container_run_script(container, script, False)


def check_proxy(container: str) -> None:
    script = "source /root/.bashrc && env | grep -i proxy"
    proc = container_run_script(container, script, True)
    # assert proc.returncode == 0, f"proxy checking command failed in {container}"
    res = proc.stdout.decode()
    if "http_proxy" in res:
        logger.error(f"unnecessary http proxy setting in {container}")
    else:
        logger.info(f"no proxy setting in {container}")


def check_container_clean(container: str) -> None:
    script = "ps aux | grep python"
    proc = container_run_script(container, script, True)
    assert proc.returncode == 0, f"Failed to run ps script at {container}"
    res = proc.stdout.decode().strip()
    if len(res) > 0:
        logger.debug(f"res: {res}")
        logger.error(f"{container} is not clean")
    else:
        logger.info(f"{container} clean")


def dump_lib_version() -> None:
    res = []
    for entry in routine_entry_list:
        item = {
            "lib_name": entry.lib_name,
            "lib_version": entry.lib_version,
        }
        res.append(item)

    fname = "lib_version.json"
    with open(fname, "w") as f:
        json.dump(res, f, indent=4)
