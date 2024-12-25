import re

import ipdb

from vuln_service.entities import RoutineEntry, RoutineStatus
from vuln_service.stop import clean_after_stop

from ..entities import FuzzInfo
from ..utils import (
    check_status,
    routines_seen,
    container_run_script,
    get_routine_crash_dir,
    get_routine_fuzz_log_path,
    logger,
)
from .utils import get_info_script, get_routine_backup_crash_dir, read_backup_log

MAP_SIZE = 65535


# REC_PAT = re.compile(
#     r"#\d+\s+[a-zA-Z]+\s+cov:\s+\d+\s+ft:\s+\d+\s+corp:\s+\d+\/\d+b\s+(lim:\s+\d+\s+)?exec\/s:\s+\d+\s+rss:\s+\d+Mb\s+L:\s+\d+(\/\d+)?\s+MS:\s"
# )
REC_PAT = re.compile(
    r"#\d+\s+[a-zA-Z]+\s+cov:\s+\d+\s+ft:\s+\d+\s+corp:\s+\d+\/\d+b\s+(lim:\s+\d+\s+)?exec\/s:\s+\d+\s+rss:\s+\d+Mb"
)
REC_PRE_PAT = re.compile(r"#\d+\s+")
COV_PAT = re.compile(r"cov: (\d+)")
TPS_PAT = re.compile(r"exec/s: (\d+)")
TOT_PAT = re.compile(r"^#(\d+)")
INI_PAT = re.compile(r"([A-Z]+): ")


def is_running_rec(rec: str) -> bool:
    mat = REC_PAT.match(rec)
    return mat is not None


def has_running_prefix(rec: str) -> bool:
    mat = REC_PRE_PAT.match(rec)
    return mat is not None


def is_init_rec(rec: str) -> bool:
    mat = INI_PAT.match(rec)
    if mat is None:
        return False
    level = mat.group(1)
    level_list = [
        "INFO",
        "WARNING",
        "DEBUG",
        "ERROR",
    ]
    return level in level_list


def is_not_complete(rec: str) -> bool:
    """Only for running record"""
    return has_running_prefix(rec) and not is_running_rec(rec)


def get_recent_record(log_content: str) -> str:
    pos = None

    lines = log_content.splitlines()
    for ind, line in enumerate(reversed(lines)):
        line = line.strip()
        if not is_init_rec(line) and not has_running_prefix(line):
            continue
        pos = len(lines) - 1 - ind
        break

    assert pos, "No valid line in current log"
    # get
    rec = lines[pos].strip()
    if is_not_complete(rec):
        rec = lines[pos - 1].strip()

    return rec


def is_running(log_content: str) -> bool:
    record = get_recent_record(log_content)
    return is_running_rec(record)


def get_crash_num(routine: RoutineEntry, exited: bool) -> int:
    if exited:
        crash_dir = get_routine_backup_crash_dir(routine)
    else:
        crash_dir = get_routine_crash_dir(routine.get_name())
    script = f"""
    find {crash_dir} -type f -name 'crash-*'
    """
    proc = container_run_script(routine.container, script, True)
    output = proc.stdout.decode()
    return len(output.splitlines())


# def check_status_or_resume(routine: RoutineEntry) -> RoutineStatus:
#     """
#     1 finished, 2 running
#     """
#     prev_status = check_status(routine)
#     if prev_status == RoutineStatus.RUN:
#         return RoutineStatus.RUN
#
#     # try to resume
#     logger.warning(f"Routine {routine.get_name()} stopped")
#     flag = try_resume(routine)
#     if flag:
#         return RoutineStatus.RUN
#
#     # remove routine_lock
#     clean_after_stop(routine)
#     return RoutineStatus.FIN


def parse_log_info(log_content: str) -> FuzzInfo:
    record = get_recent_record(log_content)

    mat = COV_PAT.search(record)
    assert mat
    edges = int(mat.group(1))

    mat = TPS_PAT.search(record)
    assert mat
    tps = int(mat.group(1))

    mat = TOT_PAT.search(record)
    assert mat
    tot = int(mat.group(1))

    paths = 0
    for line in log_content.splitlines():
        line = line.strip()
        if not is_running_rec(line):
            continue
        paths += 1

    return FuzzInfo(
        coverage=edges / MAP_SIZE,
        throughput=tot,
        speed=tps,
        # no sense
        crashNum=0,
        paths=paths,
        edges=edges,
        # no sense
        status=RoutineStatus.RUN.value,
    )


def collect_log_info(log_content: str, routine: RoutineEntry, exited: bool) -> FuzzInfo:
    crash_num = get_crash_num(routine, exited)
    if not is_running(log_content):
        logger.debug(f"routine {routine.get_name()} is initializing...")
        return FuzzInfo(crashNum=crash_num, status=RoutineStatus.INI.value)
    # logger.info("Already running...")

    info = parse_log_info(log_content)
    info.status = RoutineStatus.RUN.value
    info.crashNum = crash_num
    return info


def read_log(routine: RoutineEntry) -> str | None:
    log_path = get_routine_fuzz_log_path(routine)
    script = get_info_script(log_path)
    proc = container_run_script(routine.container, script, True)
    if proc.returncode != 0:
        if proc.returncode == 2:
            return None
        else:
            assert False, f"failed to read log file for routine {routine.get_name()}"

    log_content = proc.stdout.decode()
    return log_content


def exit_read(routine: RoutineEntry) -> FuzzInfo | None:
    log_content = read_backup_log(routine)
    if log_content is None:
        return None

    info = collect_log_info(log_content, routine, True)
    info.status = RoutineStatus.EXI.value
    return info


def is_partial_exit(routine: RoutineEntry) -> bool:
    status = check_status(routine)
    return status == RoutineStatus.EXI


def is_cleaned_exit(routine: RoutineEntry) -> bool:
    return routine not in routines_seen


def info_read(routine: RoutineEntry) -> FuzzInfo | None:
    # read and logger.info
    logger.info("start reading info...")

    if is_cleaned_exit(routine):
        logger.warning(f"routine {routine.get_name()} has been cleaned")
        info = exit_read(routine)
        return info

    if is_partial_exit(routine):
        logger.warning(f"routine {routine.get_name()} has exited")
        clean_after_stop(routine)
        info = exit_read(routine)
        return info

    log_content = read_log(routine)
    if log_content is None:
        return None

    if len(log_content) < 160:
        logger.debug("log_contnt not long enough")
    else:
        logger.debug(f"log_content suffix: {repr(log_content[-150:])}")

    lines = log_content.splitlines()
    if len(lines) == 0:
        logger.warning(f"no log content for routine {routine.get_name()}")
    else:
        logger.debug(f"log last line: {lines[-1]}")

    info = collect_log_info(log_content, routine, False)

    return info


def info_read_json(routine: RoutineEntry) -> dict:
    json = vars(info_read(routine))
    logger.debug(f"collected info: {json}")
    return json
