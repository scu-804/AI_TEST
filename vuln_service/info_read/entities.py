from enum import Enum


class LogStatus(Enum):
    INI = 1
    RUN = 2


class FuzzerStatus(Enum):
    EXI = 1
    RUN = 2
