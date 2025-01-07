import re

REC_PAT = re.compile(
    r"#\d+\s+([a-zA-Z]+)\s+(cov:\s+\d+\s+)?(ft:\s+\d+\s+)?(corp:\s+\d+\/\d+b\s+)?(lim:\s+\d+\s+)?exec\/s:\s+\d+\s+rss:\s+\d+Mb"
)
REC_PRE_PAT = re.compile(r"#\d+\s+")
COV_PAT = re.compile(r"cov: (\d+)")
TPS_PAT = re.compile(r"exec/s: (\d+)")
TOT_PAT = re.compile(r"^#(\d+)")
INI_PAT = re.compile(r"([A-Z]+): ")


REC_INIT_PAT = re.compile(
    r"#\d+\s+INITED\s+(cov:\s+\d+\s+)?(ft:\s+\d+\s+)?(corp:\s+\d+\/\d+b\s+)?(lim:\s+\d+\s+)?exec\/s:\s+\d+\s+rss:\s+\d+Mb"
)


def is_complete_rec(rec: str) -> bool:
    mat = REC_PAT.match(rec)
    return mat is not None


def has_record_prefix(rec: str) -> bool:
    mat = REC_PRE_PAT.match(rec)
    return mat is not None


def has_init_prefix(rec: str) -> bool:
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
    return has_record_prefix(rec) and not is_complete_rec(rec)


def is_init_record(line: str) -> bool:
    mat = REC_INIT_PAT.match(line)
    return mat is not None
