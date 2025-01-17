import ipdb
import subprocess
from vuln_service.entities import ExitReason, ExitStatus, RoutineEntry, RoutineStatus
from .utils import (
    check_exit_status,
    logger,
)
from .info_read.utils import check_exit_reason

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


# def get_stop_script(routine: RoutineEntry) -> str:
#     pid_name = get_pid_name(routine.get_name())
#     return stop_script_template.format(fuzz_dir=FUZZ_DIR, pid_name=pid_name)


def exec_stop(routine: RoutineEntry) -> subprocess.CompletedProcess[bytes]:
    pid_path = routine.get_pid_path()
    script = f"""
pid=$(cat {pid_path})
kill -TERM "$pid"
    """
    return routine.run_script(script, False)


# def get_backup_log_script(routine: RoutineEntry) -> str:
#     old_name = get_routine_fuzz_log_path(routine)
#     new_name = old_name + "_" + get_time_suffix()
#     return backup_log_script_template.format(old_fname=old_name, new_fname=new_name)


# def backup_routine_log_file(routine: RoutineEntry) -> None:
#     script = get_backup_log_script(routine)
#     container_run_script(routine.container, script, False)


# def backup_routine_crash_dir(routine: RoutineEntry) -> None:
#     old_dir = get_routine_crash_dir(routine.get_name())
#     new_dir = old_dir + "_" + get_time_suffix()
#     script = f"""
#     if [[ ! -d {old_dir} ]]; then
#         exit 1
#     fi
#
#     mv {old_dir} {new_dir}
#     """
#     proc = container_run_script(routine.container, script, False)
#     assert proc.returncode == 0


# def get_clean_pid_script(routine: RoutineEntry) -> str:
#     return clean_pid_file_script_template.format(pid_path=get_pid_path(routine))


def clean_pid(routine: RoutineEntry) -> None:
    pid_path = routine.get_pid_path()
    script = f"""
rm {pid_path}
    """
    routine.run_script(script, False)


def clean_after_stop(routine: RoutineEntry) -> None:
    logger.debug(f"Cleaning {routine.get_name()} routine info...")
    # backup log files
    # backup_routine_log_file(routine)
    # backup_routine_crash_dir(routine)
    clean_pid(routine)


def show_exit_reason(routine: RoutineEntry) -> None:
    reason = check_exit_reason(routine)
    if reason == ExitReason.SAN:
        logger.debug(f"routine {routine.get_name()} exited for crash")
    elif reason == ExitReason.INTER:
        logger.debug(f"routine {routine.get_name()} exited for interruption")
    else:
        assert False, f"routine {routine.get_name()} exited for unsupported reason"


def stop(routine: RoutineEntry) -> None:
    logger.info(f"Trying to stop routine {routine.get_name()}")
    status = check_exit_status(routine)

    logger.info(f"The pre-stop state for routine {routine.get_name()} is {status}")
    if status == ExitStatus.CLN:
        logger.warning(f"Routine {routine.get_name()} already exited")
        # check exit reason
        show_exit_reason(routine)
    elif status == ExitStatus.RUN:
        proc = exec_stop(routine)
        clean_after_stop(routine)
        assert proc.returncode == 0, f"stopping failed at routine {routine.get_name()}"
    else:
        assert (
            False
        ), f"It seems that previous read did not clean the exited routine {routine.get_name()}"
    logger.info(f"routine {routine.get_name()} stopped.")
