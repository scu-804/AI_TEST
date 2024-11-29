from .utils import FUZZ_DIR, container_run_script, logger
import os

stop_script_template = """
fuzz_dir='{fuzz_dir}'
if [[ ! -d "$fuzz_dir" ]]; then
  mkdir "$fuzz_dir"
fi

pid=$(cat "$fuzz_dir"/pid)

pkill -TERM -P "$pid"
"""


def get_stop_script() -> str:
    return stop_script_template.format(fuzz_dir=FUZZ_DIR)


def stop(container: str) -> None:
    logger.info("stopping fuzzing process")
    script = get_stop_script()
    container_run_script(container, script, False)
