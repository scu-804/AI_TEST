# vulnerability mining service module
from dataclasses import dataclass
import os
import time

from vuln_service.collect_crashes import collect_crashes
from vuln_service.entities import RoutineEntry
from vuln_service.start import start_routine

from .collect_crashes import collect_crashes
from .collect_requirements import collect_requirements
from .info_read import info_read_json
from .stop import stop
from .utils import logger

from .entities import vuln_engine_entry_list, routine_entry_list


# container_list = [
#     "yqy_atheris_pt",
#     "yqy_atheris_tf",
#     "yqy_atheris_keras",
#     "yqy_atheris_np",
#     "yqy_fuzz_opencv",
#     "yqy_atheris_pandas",
#     "yqy_atheris_pillow",
#     "yqy_atheris_scipy",
# ]
#


def run_loop(entry: RoutineEntry, tts: int, read_loop: int) -> None:
    start_routine(entry)
    for _ in range(read_loop):
        time.sleep(tts)
        json = info_read_json(entry)

    stop(entry)
    info_read_json(entry)
    print("\n")


def setup_zip() -> None:
    err_containers = []
    for entry in vuln_engine_entry_list:
        os.system(f"docker start {entry.container}")
        ret = os.system(f"docker exec {entry.container} bash -c 'apt install -y zip'")
        if ret != 0:
            err_containers.append(entry.container)
    logger.error(f"error containers : {','.join(err_containers)}")


def test_one(entry: RoutineEntry, tts: int, read_loop: int) -> None:
    # logger.info(f"start testing {entry.container}")
    # collect_requirements(entry.container)
    if entry.container != "yqy_atheris_np":
        return
    run_loop(entry, 5, 2)


def test_all_routine() -> None:
    for entry in routine_entry_list:
        test_one(entry, 5, 3)

    # output_container_cwd()
