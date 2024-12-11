# vulnerability mining service module
from dataclasses import dataclass
import os
import time

from vuln_service.collect_crashes import collect_crashes

from .collect_crashes import collect_crashes
from .collect_requirements import collect_requirements
from .info_read import info_read_json
from .start import start
from .stop import stop
from .utils import get_container_cwd, output_container_cwd
from .utils import logger


@dataclass
class VulnEngineEntry:
    container: str
    fuzz_cmd: str


vuln_engine_entry_list = [
    # 8 in total
    VulnEngineEntry("yqy_atheris_pt", "./run_fuzz.sh"),
    VulnEngineEntry("yqy_atheris_tf", "python fuzz_tensorflow.py"),
    VulnEngineEntry("yqy_atheris_keras", "python fuzz_keras.py"),
    VulnEngineEntry("yqy_atheris_np", "python3 fuzz_numpy.py"),
    VulnEngineEntry("yqy_fuzz_opencv", "./generateusergallerycollage_fuzzer"),
    VulnEngineEntry("yqy_atheris_pandas", "python3 fuzz_pandas.py"),
    VulnEngineEntry("yqy_atheris_pillow", "./run_fuzz.sh"),
    VulnEngineEntry("yqy_atheris_scipy", "python3 fuzz_scipy.py"),
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


def run_loop(entry: VulnEngineEntry, tts: int, read_loop: int) -> None:
    start(entry.container, entry.fuzz_cmd)
    for _ in range(read_loop):
        time.sleep(tts)
        json = info_read_json(entry.container)
    stop(entry.container)


def setup_zip() -> None:
    err_containers = []
    for entry in vuln_engine_entry_list:
        os.system(f"docker start {entry.container}")
        ret = os.system(f"docker exec {entry.container} bash -c 'apt install -y zip'")
        if ret != 0:
            err_containers.append(entry.container)
    logger.error(f"error containers : {','.join(err_containers)}")


def test_one(entry: VulnEngineEntry, tts: int, read_loop: int) -> None:
    # logger.info(f"start testing {entry.container}")
    # collect_requirements(entry.container)
    run_loop(entry, 3, 2)


def test_all() -> None:
    for entry in vuln_engine_entry_list:
        test_one(entry, 5, 3)

    # output_container_cwd()


if __name__ == "__main__":
    # test_one(vuln_engine_entry_list[4])
    test_one(vuln_engine_entry_list[6], 5, 1)
    # test_one(vuln_engine_entry_list[7])
