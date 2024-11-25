from dataclasses import dataclass
import re

from .utils import FUZZ_DIR, FUZZ_LOG, container_run_script, logger

MAP_SIZE = 65535

# params needed: fuzz_dir fuzz_log
info_script_template = """
cat {fuzz_dir}/{fuzz_log}
"""


@dataclass
class FuzzInfo:
    coverge: float = 0.0
    throughput: int = 0
    speed: int = 0
    crashNum: int = 0
    paths: int = 0
    edges: int = 0
    # 1 for finished, 2 for running, 3 for initializing
    status: int = 2


# REC_PAT = re.compile(
#     r"#\d+\s+[a-zA-Z]+\s+cov:\s+\d+\s+ft:\s+\d+\s+corp:\s+\d+\/\d+b\s+(lim:\s+\d+\s+)?exec\/s:\s+\d+\s+rss:\s+\d+Mb\s+L:\s+\d+(\/\d+)?\s+MS:\s"
# )
REC_PAT = re.compile(
    r"#\d+\s+[a-zA-Z]+\s+cov:\s+\d+\s+ft:\s+\d+\s+corp:\s+\d+\/\d+b\s+(lim:\s+\d+\s+)?exec\/s:\s+\d+\s+rss:\s+\d+Mb"
)
COV_PAT = re.compile(r"cov: (\d+)")
TPS_PAT = re.compile(r"exec/s: (\d+)")


def get_info_script() -> str:
    return info_script_template.format(fuzz_dir=FUZZ_DIR, fuzz_log=FUZZ_LOG)


def is_complete_rec(rec: str) -> bool:
    mat = REC_PAT.match(rec)
    return mat is not None


def get_recent_record(log_content: str) -> str:
    rec = log_content.splitlines()[-1].strip()
    # In case for incomplete logging during reading
    if not is_complete_rec(rec):
        rec = log_content.splitlines()[-2].strip()

    return rec


def is_running(log_content: str) -> bool:
    record = get_recent_record(log_content)
    return is_complete_rec(record)


def collect_running_info(log_content: str) -> FuzzInfo:
    record = get_recent_record(log_content)

    mat = COV_PAT.search(record)
    assert mat
    edges = int(mat.group(1))

    mat = TPS_PAT.search(record)
    assert mat
    tps = int(mat.group(1))

    paths = 0
    for line in log_content.splitlines():
        line = line.strip()
        if not is_complete_rec(line):
            continue
        paths += 1

    return FuzzInfo(
        coverge=edges / MAP_SIZE,
        throughput=tps,
        speed=tps,
        crashNum=0,
        paths=paths,
        edges=edges,
        status=2,
    )


def info_read(container: str) -> FuzzInfo:
    # read and logger.info
    logger.info("start reading info...")
    script = get_info_script()
    proc = container_run_script(container, script, True)
    log_content = proc.stdout.decode()

    logger.debug(f"log_content suffix: {repr(log_content[-150:])}")
    logger.debug(f"log last line: {log_content.splitlines()[-1]}")
    if not is_running(log_content):
        logger.warning("The Vulnerability Engine is initializing...")
        return FuzzInfo(status=3)

    # logger.info("Already running...")
    return collect_running_info(log_content)


def info_read_json(container: str) -> dict:
    return vars(info_read(container))
