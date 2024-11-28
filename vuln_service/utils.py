import subprocess
import os
import sys
import logging
import colorlog
import toml

FUZZ_DIR = "/fuzz"
FUZZ_LOG = "fuzz_log"
# note that tailing '/' is needed
# CRASH_DIR = "/fuzz/crashes/"

LOGGER_NAME = "vuln_service"
# BASE_DIR = sys.path[0]

container_cwd: dict[str, str] = {
    "yqy_atheris_pt": "/root/pytorch",
    "yqy_atheris_tf": "/root",
    "yqy_atheris_keras": "/root/fuzz",
    "yqy_atheris_np": "/root",
    "yqy_fuzz_opencv": "/out",
    "yqy_atheris_pandas": "/root",
    "yqy_atheris_pillow": "/root/Pillow",
    "yqy_atheris_scipy": "/root",
}


def output_container_cwd() -> None:
    logger.info("printing container_cwd...")
    for key, val in container_cwd.items():
        print(f'"{key}": "{val}",')


def get_container_cwd(container: str) -> str | None:
    return container_cwd.get(container)


# def add_container_cwd(container: str, cwd: str) -> bool:
#     if container in container_cwd:
#         return False
#
#     container_cwd[container] = cwd
#     return True


def path_formalize(*paths) -> str:
    for path in paths:
        assert isinstance(path, str)
    return os.path.join(sys.path[0], *paths)


handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s[%(levelname)s]%(reset)s %(asctime)s - %(message)s"
    )
)

logger = colorlog.getLogger(LOGGER_NAME)
logger.addHandler(handler)

# set logging level
config_path = path_formalize("config.toml")
config = toml.load(open(config_path))
log_level = config["logging"]["level"].upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))


def container_run_script(
    container: str, script: str, output: bool
) -> subprocess.CompletedProcess[bytes]:
    docker_cmd = f"docker exec -i {container} bash -s"
    return subprocess.run(
        docker_cmd.split(), input=script.encode(), capture_output=output
    )
