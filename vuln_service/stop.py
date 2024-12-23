import ipdb
from vuln_service.entities import RoutineEntry
from datetime import datetime
from .utils import (
    get_pid_path,
    FUZZ_DIR,
    container_run_script,
    get_pid_name,
    get_routine_fuzz_log_path,
    logger,
)
from .utils import routines_seen

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


def get_stop_script(routine: RoutineEntry) -> str:
    pid_name = get_pid_name(routine.get_name())
    return stop_script_template.format(fuzz_dir=FUZZ_DIR, pid_name=pid_name)


def get_time_suffix() -> str:
    now = datetime.now()
    date_time_string = now.strftime("%Y-%m-%d:%H:%M:%S")
    return date_time_string


def get_backup_log_script(routine: RoutineEntry) -> str:
    old_name = get_routine_fuzz_log_path(routine)
    new_name = old_name + "_" + get_time_suffix()
    return backup_log_script_template.format(old_fname=old_name, new_fname=new_name)


def backup_routine_log_file(routine: RoutineEntry) -> None:
    script = get_backup_log_script(routine)
    container_run_script(routine.container, script, False)


def get_clean_pid_script(routine: RoutineEntry) -> str:
    return clean_pid_file_script_template.format(pid_path=get_pid_path(routine))


def clean_pid(routine: RoutineEntry) -> None:
    script = get_clean_pid_script(routine)
    container_run_script(routine.container, script, False)


def clean_after_stop(routine: RoutineEntry) -> None:
    routines_seen.discard(routine)
    # backup log files
    backup_routine_log_file(routine)
    clean_pid(routine)


def stop(routine: RoutineEntry) -> None:
    script = get_stop_script(routine)
    proc = container_run_script(routine.container, script, False)
    assert proc.returncode == 0, f"stopping failed at routine {routine.get_name()}"
    ipdb.set_trace()
    clean_after_stop(routine)
    logger.info(f"routine {routine.get_name()} stopped.")
