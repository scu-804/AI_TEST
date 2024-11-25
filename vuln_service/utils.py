import subprocess
import os
import sys
import logging
import colorlog
import toml

FUZZ_DIR = "/fuzz"
FUZZ_LOG = "fuzz_log"

LOGGER_NAME = "vuln_service"
# BASE_DIR = sys.path[0]


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
# __import__("ipdb").set_trace()
log_level = config["logging"]["level"].upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))


def container_run_script(
    container: str, script: str, output: bool
) -> subprocess.CompletedProcess[bytes]:
    docker_cmd = f"docker exec -i {container} bash -s"
    return subprocess.run(
        docker_cmd.split(), input=script.encode(), capture_output=output
    )
