from dataclasses import dataclass
from enum import Enum


from .routine import RoutineEntry


@dataclass
class VulnEngineEntry:
    container: str
    fuzz_cmd: str


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


@dataclass
class FuzzInfo:
    coverage: float = 0.0
    throughput: int = 0
    speed: int = 0
    crashNum: int = 0
    paths: int = 0
    edges: int = 0
    # 1 for finished, 2 for running, 3 for initializing
    status: int = RoutineStatus.RUN.value


class ExitReason(Enum):
    """
    SAN for error exit, INTER for explicit exit
    OOM to be implemented
    """

    SAN = 1
    OOM = 2
    INTER = 3


vuln_engine_entry_list = [
    # 8 in total
    VulnEngineEntry("vul_pytorch", "./run_fuzz.sh"),
    VulnEngineEntry("vul_tf", "python fuzz_tensorflow.py"),
    VulnEngineEntry("vul_np", "python3 fuzz_numpy.py"),
    VulnEngineEntry("vul_keras", "python fuzz_keras.py"),
    VulnEngineEntry("vul_opencv", "./generateusergallerycollage_fuzzer"),
    VulnEngineEntry("vul_pandas", "python3 fuzz_pandas.py"),
    VulnEngineEntry("vul_pillow", "./run_fuzz.sh"),
    VulnEngineEntry("vul_scipy", "python3 fuzz_scipy.py"),
]
