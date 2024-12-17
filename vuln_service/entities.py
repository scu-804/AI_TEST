from dataclasses import dataclass


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
routine_entry_list = [
    # no_conda
    RoutineEntry("vul_pytorch", "pytorch", "2.5.0"),
    # no_conda
    RoutineEntry("vul_tf", "tensorflow", "2.17.0"),
    RoutineEntry("vul_keras", "keras", "3.5.0"),
    RoutineEntry("vul_keras", "keras", "3.6.0"),
    RoutineEntry("vul_np", "numpy", "2.0.2"),
    RoutineEntry("vul_np", "numpy", "2.1.3"),
    # no_conda
    RoutineEntry("vul_opencv", "opencv", "4.10.0"),
    RoutineEntry("vul_pandas", "pandas", "2.2.3"),
    RoutineEntry("vul_pandas", "pandas", "2.2.0"),
    # no conda
    RoutineEntry("vul_pillow", "pillow", "7.1.2"),
    RoutineEntry("vul_scipy", "scipy", "1.14.1"),
    RoutineEntry("vul_scipy", "scipy", "1.13.1"),
]
