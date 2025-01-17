from vuln_service.entities import ExitReason, ExitStatus, RoutineEntry

import re
from vuln_service.utils import (
    FUZZ_DIR,
    check_exit_status,
    container_run_script,
)


def read_log(routine: RoutineEntry) -> str | None:
    log_path = routine.get_fuzz_log_path()
    # log_path = get_routine_fuzz_log_path(routine)
    script = get_info_script(log_path)
    proc = container_run_script(routine.container, script, True)
    if proc.returncode != 0:
        if proc.returncode == 2:
            return None
        else:
            assert False, f"failed to read log file for routine {routine.get_name()}"

    log_content = proc.stdout.decode()
    return log_content


def is_partial_exit(routine: RoutineEntry) -> bool:
    status = check_exit_status(routine)
    return status == ExitStatus.PAR


def is_cleaned_exit(routine: RoutineEntry) -> bool:
    status = check_exit_status(routine)
    return status == ExitStatus.CLN


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


EXIT_LINE_PAT = re.compile(r"==(\d+)==")


def is_exit_code_line(line: str) -> bool:
    mat = EXIT_LINE_PAT.match(line)
    return mat is not None


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
    log_content = read_log(routine)
    assert log_content, f"Failed to read backup log of routine {routine.get_name()}"
    lines = log_content.splitlines()
    for line in reversed(lines):
        line = line.rstrip()
        if not is_exit_code_line(line):
            continue

        reason = exit_status_judge(line)
        return reason
    assert False, f"Routine {routine.get_name()} is still running"
