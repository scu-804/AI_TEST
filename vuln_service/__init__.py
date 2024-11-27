# vulnerability mining service module
from .utils import get_container_cwd
import time
import os


from dataclasses import dataclass

from .collect_crashes import collect_crashes
from vuln_service.collect_crashes import collect_crashes

from .info_read import info_read_json

from .start import start

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


def setup_zip() -> None:
    err_containers = []
    for entry in vuln_engine_entry_list:
        os.system(f"docker start {entry.container}")
        ret = os.system(f"docker exec {entry.container} bash -c 'apt install -y zip'")
        if ret != 0:
            err_containers.append(entry.container)
    logger.error(f"error containers : {','.join(err_containers)}")


def stop(container: str) -> None:
    logger.info("stoping docker container...")
    os.system(f"docker stop {container}")


def test_one(entry: VulnEngineEntry, tts: int, read_loop: int) -> None:
    start(entry.container, entry.fuzz_cmd)
    # for _ in range(read_loop):
    #     time.sleep(tts)
    #     fuzz_info = info_read_json(entry.container)
    #     logger.debug(f"Fuzz Info: {fuzz_info}")

    # create crash manually
    # cwd = get_container_cwd(entry.container)
    # os.system(f"docker exec {entry.container} bash -c 'touch {cwd}/crash-111'")

    zip_path = collect_crashes(entry.container)
    if zip_path is None:
        logger.error("Failed to collect crashes zip file")
    else:
        logger.info("zip success")
    stop(entry.container)
    # logger.info(
    #     "*" * 10 + f" conatiner {entry.container} passed the test " + "*" * 10 + "\n"
    # )


def test_all() -> None:
    for entry in vuln_engine_entry_list:
        test_one(entry, 5, 3)


if __name__ == "__main__":
    # test_one(vuln_engine_entry_list[4])
    test_one(vuln_engine_entry_list[6], 5, 1)
    # test_one(vuln_engine_entry_list[7])
