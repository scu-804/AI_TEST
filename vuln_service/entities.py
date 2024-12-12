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
    VulnEngineEntry("yqy_atheris_pt", "./run_fuzz.sh"),
    VulnEngineEntry("yqy_atheris_tf", "python fuzz_tensorflow.py"),
    VulnEngineEntry("yqy_atheris_keras", "python fuzz_keras.py"),
    VulnEngineEntry("yqy_atheris_np", "python3 fuzz_numpy.py"),
    VulnEngineEntry("yqy_fuzz_opencv", "./generateusergallerycollage_fuzzer"),
    VulnEngineEntry("yqy_atheris_pandas", "python3 fuzz_pandas.py"),
    VulnEngineEntry("yqy_atheris_pillow", "./run_fuzz.sh"),
    VulnEngineEntry("yqy_atheris_scipy", "python3 fuzz_scipy.py"),
]
routine_entry_list = [
    # no_conda
    RoutineEntry("yqy_atheris_pt", "pytorch", "2.5.0"),
    # no_conda
    RoutineEntry("yqy_atheris_tf", "tensorflow", "2.17.0"),
    RoutineEntry("yqy_atheris_keras", "keras", "3.5.0"),
    RoutineEntry("yqy_atheris_keras", "keras", "3.6.0"),
    RoutineEntry("yqy_atheris_np", "numpy", "2.0.2"),
    RoutineEntry("yqy_atheris_np", "numpy", "2.1.3"),
    # no_conda
    RoutineEntry("yqy_fuzz_opencv", "opencv", "4.10.0"),
    RoutineEntry("yqy_atheris_pandas", "pandas", "2.2.3"),
    RoutineEntry("yqy_atheris_pandas", "pandas", "2.2.0"),
    # no conda
    RoutineEntry("yqy_atheris_pillow", "pillow", "7.1.2"),
    RoutineEntry("yqy_atheris_scipy", "scipy", "1.14.1"),
    RoutineEntry("yqy_atheris_scipy", "scipy", "1.13.1"),
]
