from vuln_service.entities import RoutineEntry
from .utils import FUZZ_DIR, container_run_script, get_pid_name, logger
from .utils import routines_seen

stop_script_template = """
fuzz_dir='{fuzz_dir}'
if [[ ! -d "$fuzz_dir" ]]; then
  mkdir "$fuzz_dir"
fi

pid=$(cat "$fuzz_dir"/{pid_name})

kill -TERM "$pid"
"""


def get_stop_script(routine: RoutineEntry) -> str:
    pid_name = get_pid_name(routine.get_name())
    return stop_script_template.format(fuzz_dir=FUZZ_DIR, pid_name=pid_name)


def stop(routine: RoutineEntry) -> None:
    script = get_stop_script(routine)
    proc = container_run_script(routine.container, script, False)
    assert proc.returncode == 0, f"stopping failed at routine {routine.get_name()}"
    routines_seen.discard(routine)
    logger.info(f"routine {routine.get_name()} stopped.")
