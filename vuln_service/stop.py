import ipdb
import subprocess

from .entities import RoutineEntry, ExitStatus
from .utils import (
    logger,
)

stop_script_template = """
fuzz_dir='{fuzz_dir}'
if [[ ! -d "$fuzz_dir" ]]; then
  mkdir "$fuzz_dir"
fi

pid=$(cat "$fuzz_dir"/{pid_name})

kill -TERM "$pid"
"""

backup_log_script_template = """
old_log="{old_fname}"
new_log="{new_fname}"

mv "$old_log" "$new_log"

"""

clean_pid_file_script_template = """
pid_path="{pid_path}"
rm "$pid_path"
"""


def exec_stop(routine: RoutineEntry) -> subprocess.CompletedProcess[bytes]:
    pid_path = routine.get_pid_path()
    script = f"""
pid=$(cat {pid_path})
kill -TERM "$pid"
    """
    return routine.run_ctn_script(script, False)


def stop(routine: RoutineEntry) -> None:
    logger.info(f"Trying to stop routine {routine.get_name()}")
    status = routine.check_exit_status()

    logger.info(f"The pre-stop state for routine {routine.get_name()} is {status}")
    if status == ExitStatus.CLN:
        logger.warning(f"Routine {routine.get_name()} already exited")
        # check exit reason
        routine.show_exit_reason()
    elif status == ExitStatus.RUN:
        proc = exec_stop(routine)
        routine.clean_after_stop()
        assert proc.returncode == 0, f"stopping failed at routine {routine.get_name()}"
    else:
        assert (
            False
        ), f"It seems that previous read did not clean the exited routine {routine.get_name()}"
    logger.info(f"routine {routine.get_name()} stopped.")
