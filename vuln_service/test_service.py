# vulnerability mining service module
import ipdb
from .config import CRASH_FILE_TIMEOUT
from dataclasses import dataclass
import os
import time
from .info_read.patterns import REC_PAT

from vuln_service.entities import RoutineEntry
from vuln_service.start import start_routine

from .collect_crashes import collect_crashes
from .info_read import info_read_json
from .stop import stop
from .utils import logger, path_formalize

# from .entities import vuln_engine_entry_list, routine_entry_list

EXAMPLE_HARN_PATH = path_formalize("test_data", "example.py")

status = os.system("docker context use server2")
assert status == 0, "Failed to set docker context to server2"

routine_entry_list = [
    # no_conda
    RoutineEntry("vul_pytorch", "pytorch", "2.5.0", EXAMPLE_HARN_PATH),
    # no_conda
    RoutineEntry("vul_tf", "tensorflow", "2.17.0", EXAMPLE_HARN_PATH),
    RoutineEntry("vul_keras", "keras", "3.5.0", EXAMPLE_HARN_PATH),
    RoutineEntry("vul_keras", "keras", "3.6.0", EXAMPLE_HARN_PATH),
    RoutineEntry("vul_np", "numpy", "2.0.2", EXAMPLE_HARN_PATH),
    # RoutineEntry("vul_np", "numpy", "2.1.3"),
    # no_conda
    RoutineEntry("vul_opencv", "opencv", "4.10.0", EXAMPLE_HARN_PATH),
    RoutineEntry("vul_pandas", "pandas", "2.2.3", EXAMPLE_HARN_PATH),
    RoutineEntry("vul_pandas", "pandas", "2.2.0", EXAMPLE_HARN_PATH),
    # no conda
    RoutineEntry("vul_pillow", "pillow", "7.1.2", EXAMPLE_HARN_PATH),
    RoutineEntry("vul_scipy", "scipy", "1.14.1", EXAMPLE_HARN_PATH),
    RoutineEntry("vul_scipy", "scipy", "1.13.1", EXAMPLE_HARN_PATH),
]

routine_entry_list_wo_harn = [
    # no_conda
    RoutineEntry("vul_pytorch", "pytorch", "2.5.0"),
    # no_conda
    RoutineEntry("vul_tf", "tensorflow", "2.17.0"),
    RoutineEntry("vul_keras", "keras", "3.5.0"),
    RoutineEntry("vul_keras", "keras", "3.6.0"),
    RoutineEntry("vul_np", "numpy", "2.0.2"),
    # RoutineEntry("vul_np", "numpy", "2.1.3"),
    # no_conda
    RoutineEntry("vul_opencv", "opencv", "4.10.0"),
    RoutineEntry("vul_pandas", "pandas", "2.2.3"),
    RoutineEntry("vul_pandas", "pandas", "2.2.0"),
    # no conda
    RoutineEntry("vul_pillow", "pillow", "7.1.2"),
    RoutineEntry("vul_scipy", "scipy", "1.14.1"),
    RoutineEntry("vul_scipy", "scipy", "1.13.1"),
]
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


def read_one_time(entry: RoutineEntry, tts: int) -> None:
    time.sleep(tts)
    _ = info_read_json(entry)


def run_loop(entry: RoutineEntry, tts: int, read_loop: int) -> None:
    flag = start_routine(entry)
    if not flag:
        return
    if read_loop > 0:
        for _ in range(read_loop):
            read_one_time(entry, tts)
    else:
        while True:
            read_one_time(entry, tts)

    stop(entry)
    info_read_json(entry)
    collect_crashes(entry)
    print("\n")


# def setup_zip() -> None:
#     err_containers = []
#     for entry in vuln_engine_entry_list:
#         os.system(f"docker start {entry.container}")
#         ret = os.system(f"docker exec {entry.container} bash -c 'apt install -y zip'")
#         if ret != 0:
#             err_containers.append(entry.container)
#     logger.error(f"error containers : {','.join(err_containers)}")


def run_one_routine(entry: RoutineEntry, tts: int, read_loop: int) -> None:
    # logger.info(f"start testing {entry.container}")
    # collect_requirements(entry.container)
    # if entry.lib_name == "numpy":
    #     run_loop(entry, 10, 10)
    run_loop(entry, tts, read_loop)


def test_rec_regex() -> None:
    line = r"#262144 pulse  corp: 1/1b lim: 2611 exec/s: 131072 rss: 311Mb"
    mat = REC_PAT.match(line)
    assert mat
    print(f"1st group: {mat.group(1)}")
    print(f"2st group: {mat.group(2)}")
    print(f"3st group: {mat.group(3)}")
    print(f"4st group: {mat.group(4)}")


def test_dup_crash_download() -> None:
    for entry in routine_entry_list:
        if entry.container != "vul_pytorch":
            continue
        run_one_routine(entry, 10, 5)
        collect_crashes(entry)


def test_opencv() -> None:
    for entry in routine_entry_list_wo_harn:
        if entry.container != "vul_opencv":
            continue
        run_one_routine(entry, 5, -1)


def test_service() -> None:
    for entry in routine_entry_list:
        run_one_routine(entry, 5, 6)

    for entry in routine_entry_list_wo_harn:
        run_one_routine(entry, 5, 6)
    # output_container_cwd()
