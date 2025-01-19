import ipdb

from vuln_service.entities import RoutineEntry, RoutineStatus
from vuln_service.entities.routine.read import is_exit_code_line
from vuln_service.info_read.entities import FuzzerStatus, LogStatus

from ..entities import ExitStatus, FuzzInfo
from vuln_service.utils import (
    logger,
)
from .patterns import (
    is_complete_rec,
    has_record_prefix,
    has_init_prefix,
    COV_PAT,
    TPS_PAT,
    TOT_PAT,
    is_init_record,
)

MAP_SIZE = 65535


# REC_PAT = re.compile(
#     r"#\d+\s+[a-zA-Z]+\s+cov:\s+\d+\s+ft:\s+\d+\s+corp:\s+\d+\/\d+b\s+(lim:\s+\d+\s+)?exec\/s:\s+\d+\s+rss:\s+\d+Mb\s+L:\s+\d+(\/\d+)?\s+MS:\s"
# )


def skip_error_log(log_lines: list[str]) -> int:
    """
    return the index of last line of fuzzer running log
    """
    # skip to exit code line
    end = len(log_lines)
    flag = False
    for ind, line in enumerate(reversed(log_lines[:end])):
        cnt = ind + 1
        if not is_exit_code_line(line):
            continue
        flag = True
        end = end - cnt
        break
    assert flag, "No exit code line in the exit fuzzer log"

    # target line now is the first non-error line -> division: remaining
    for ind, line in enumerate(reversed(log_lines[:end])):
        if not has_init_prefix(line) and not has_record_prefix(line):
            continue
        flag = True
        end = end - ind
        break
    assert flag, "No fuzz running part in the exit fuzzer log"
    return end


def has_exit_code_line(lines: list[str]) -> bool:
    for line in reversed(lines):
        if is_exit_code_line(line):
            return True
    return False


def get_init_record_pos(lines: list[str]) -> int | None:
    for ind, line in enumerate(reversed(lines)):
        cnt = ind + 1
        if is_init_record(line):
            return len(lines) - cnt
    return None


def get_last_run_record(lines: list[str]) -> str | None:
    """
    returns the position of last record
    """
    beg = get_init_record_pos(lines)
    if beg is None:
        return None
    for line in reversed(lines[beg:]):
        if is_complete_rec(line):
            return line
    assert False, "Failed to get running record in running situation"


def get_recent_record(lines: list[str]) -> tuple[str, FuzzerStatus, LogStatus]:
    """
    get recent complete record or init log line
    analyze status based on log content
    """

    # exit skip part: returns an index
    # log_stat = None
    fuz_stat = None
    rec = None
    exited = has_exit_code_line(lines)
    if exited:
        fuz_stat = FuzzerStatus.EXI
        end = skip_error_log(lines)
    else:
        fuz_stat = FuzzerStatus.RUN
        end = len(lines)

    rec = get_last_run_record(lines[:end])
    if rec is None:
        return "", fuz_stat, LogStatus.INI
    else:
        return rec, fuz_stat, LogStatus.RUN


def get_routine_crash_num(routine: RoutineEntry) -> int:
    crash_dir = routine.get_crash_dir()
    # if exited:
    #     crash_dir = get_routine_backup_crash_dir(routine)
    # else:
    #     crash_dir = get_routine_crash_dir(routine.get_name())
    script = f"""
    find {crash_dir} -mindepth 1 -maxdepth 1 -type f
    """
    proc = routine.run_ctn_script(script, True)
    if proc.returncode != 0:
        err_msg = proc.stderr.decode()
        assert (
            False
        ), f"failed to collect crash files for routine {routine.get_name()}: {err_msg}"
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


def calc_routine_status(fuz_stat: FuzzerStatus, log_stat: LogStatus) -> RoutineStatus:
    if fuz_stat == FuzzerStatus.EXI:
        return RoutineStatus.EXI

    if log_stat == LogStatus.RUN:
        return RoutineStatus.RUN
    elif log_stat == LogStatus.INI:
        return RoutineStatus.INI


def parse_log_info(log_content: str) -> FuzzInfo:
    """
    get recent record and parse
    """
    lines = [line.rstrip() for line in log_content.splitlines()]
    rec, fuz_stat, log_stat = get_recent_record(lines)
    # exited status judge
    rout_stat = calc_routine_status(fuz_stat, log_stat)
    if log_stat == LogStatus.INI:
        return FuzzInfo(status=rout_stat.value)

    mat = COV_PAT.search(rec)
    if mat is None:
        edges = 0
    else:
        edges = int(mat.group(1))

    if fuz_stat == FuzzerStatus.EXI:
        tps = 0
    else:
        mat = TPS_PAT.search(rec)
        assert mat
        tps = int(mat.group(1))

    mat = TOT_PAT.search(rec)
    assert mat
    tot = int(mat.group(1))

    paths = 0
    for line in lines:
        if not is_complete_rec(line):
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
        status=rout_stat.value,
    )


def collect_routine_info(log_content: str, routine: RoutineEntry) -> FuzzInfo:
    crash_num = get_routine_crash_num(routine)

    # if not exited and not is_target_running(log_content):
    #     logger.debug(f"routine {routine.get_name()} is initializing...")
    #     return FuzzInfo(crashNum=crash_num, status=RoutineStatus.INI.value)
    # logger.info("Already running...")

    info = parse_log_info(log_content)
    info.crashNum = crash_num
    return info


def info_read(routine: RoutineEntry) -> FuzzInfo | None:
    # read and logger.info
    logger.info(f"start reading info for routine {routine.get_name()}")

    # exited = False
    if routine.is_cleaned_exit():
        logger.warning(f"routine {routine.get_name()} has been cleaned")
        # exited = True
    elif routine.is_partial_exit():
        logger.warning(f"routine {routine.get_name()} has exited")
        routine.clean_after_stop()
        # exited = True
    log_content = routine.read_log()
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

    info = collect_routine_info(log_content, routine)

    return info


def info_read_json(routine: RoutineEntry) -> dict:
    json = vars(info_read(routine))
    logger.debug(f"collected info: {json}")
    return json
