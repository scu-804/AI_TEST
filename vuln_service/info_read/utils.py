from vuln_service.entities import ExitReason, RoutineEntry
import re
from vuln_service.utils import (
    FUZZ_DIR,
    get_routine_backup_fuzz_log_path,
    container_run_script,
    get_routine_crash_dir,
    get_routine_crash_dir_name,
)

# params needed: fuzz_dir fuzz_log
info_script_template = """
fpath="{log_path}"

if [[ ! -f "$fpath" ]]; then 
    echo "target log file $fpath does not exits"
    exit 2
fi

cat "$fpath"
"""


def get_info_script(log_path: str) -> str:
    return info_script_template.format(log_path=log_path)


def get_routine_backup_crash_dir(routine: RoutineEntry) -> str:
    crash_dir_name = get_routine_crash_dir_name(routine.get_name())

    script = f"""
    find  {FUZZ_DIR} -maxdepth 1 -mindepth 1 -type d -name '{crash_dir_name}_*'
    """
    proc = container_run_script(routine.container, script, True)
    output = proc.stdout.decode()
    lines = [line.strip() for line in output.splitlines()]
    assert len(lines) > 0
    lines.sort()
    return lines[-1]


def read_backup_log(routine: RoutineEntry) -> str | None:
    log_path = get_routine_backup_fuzz_log_path(routine)
    script = get_info_script(log_path)
    proc = container_run_script(routine.container, script, True)
    if proc.returncode != 0:
        if proc.returncode == 2:
            return None
        else:
            assert (
                False
            ), f"failed to read backup log file for routine {routine.get_name()}"

    log_content = proc.stdout.decode()
    return log_content


EXIT_LINE_PAT = re.compile(r"==(\d+)==")


def exit_status_judge(line: str) -> ExitReason:
    intrp = r"libFuzzer: run interrupted; exiting"
    if intrp in line:
        return ExitReason.INTER
    else:
        return ExitReason.SAN


def check_exit_reason(routine: RoutineEntry) -> ExitReason:
    """
    Invoked only in exited situation
    """
    log_content = read_backup_log(routine)
    assert log_content, f"Failed to read backup log of routine {routine.get_name()}"
    lines = log_content.splitlines()
    for line in reversed(lines):
        line = line.strip()
        mat = EXIT_LINE_PAT.match(line)
        if mat is None:
            continue

        reason = exit_status_judge(line)
        return reason
    assert False, f"Routine {routine.get_name()} is still running"
