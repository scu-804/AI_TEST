from dataclasses import dataclass
from enum import Enum


@dataclass()
class RoutineEntry:
    container: str
    lib_name: str
    lib_version: str

    def get_name(self) -> str:
        return f"{self.lib_name}_{self.lib_version}"

    def __hash__(self):
        # Compute hash based on the unique attributes
        return hash((self.container, self.lib_name, self.lib_version))


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
