import os
from .utils import add_container_cwd, container_run_script, FUZZ_DIR, FUZZ_LOG
from .utils import logger

# params needed: fuzz_dir, fuzz_cmd, fuzz_log
start_script_template = """ 
fuzz_dir='{fuzz_dir}'
if [[ ! -d "$fuzz_dir" ]]; then
  mkdir "$fuzz_dir"
fi

source /root/.bashrc
{fuzz_cmd} 2>"$fuzz_dir"/{fuzz_log} &
pwd
"""


def get_start_script(fuzz_cmd: str) -> str:
    return start_script_template.format(
        fuzz_dir=FUZZ_DIR, fuzz_cmd=fuzz_cmd, fuzz_log=FUZZ_LOG
    )


def exec_service(container: str, fuzz_cmd: str) -> None:
    """
    return cwd of fuzzing process
    """
    script = get_start_script(fuzz_cmd)
    proc = container_run_script(container, script, True)
    cwd = proc.stdout.decode().strip()
    logger.debug(f"cwd: {cwd}")
    add_container_cwd(container, cwd)


def start(container: str, fuzz_cmd: str) -> None:
    """
    container: container name
    script: path of the script to execute inside docker container
    """
    logger.info("starting docker container...")
    # start docker container
    os.system(f"docker start {container}")

    # run service
    exec_service(container, fuzz_cmd)
