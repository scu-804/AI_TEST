import re
from enum import Enum


class RoutineStatus(Enum):
    EXI = 1
    RUN = 2
    INI = 3


class ExitStatus(Enum):
    CLN = 1
    PAR = 2
    RUN = 3

    def __str__(self) -> str:
        return self.name


class ExitReason(Enum):
    """
    SAN for error exit, INTER for explicit exit
    OOM to be implemented
    """

    SAN = 1
    OOM = 2
    INTER = 3


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
