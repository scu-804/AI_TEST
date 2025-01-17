from dataclasses import dataclass
from os.path import basename
import os
import subprocess

from vuln_service.utils import (
    FUZZ_DIR,
    container_run_script,
    create_ctn_dir_if_nonexist,
    get_time_suffix,
)


@dataclass()
class Harness:
    loc_path: str
    ctn_path: str

    def __init__(self, loc_path: str, ctn_path: str) -> None:
        self.loc_path = loc_path
        self.ctn_path = ctn_path


@dataclass()
class RoutineEntry:
    container: str
    lib_name: str
    lib_version: str
    harn: Harness
    fuzz_cmd: str

    inited: bool

    def __init__(
        self, container: str, lib_name: str, lib_version: str, harn_path: str
    ) -> None:
        self.container = container
        self.lib_name = lib_name
        self.lib_version = lib_version
        self.inited = False

        self.init_harness(harn_path)
        # fuzz_cmd initlization needed
        #
        self.inited = True

    def create_dir(self, dir_path: str) -> None:
        if not self.inited:
            create_ctn_dir_if_nonexist(dir_path, self.container)

    def init_harness(self, loc_path: str) -> None:
        ctn_path = self.get_ctn_harn_path(loc_path)
        self.harn = Harness(loc_path, ctn_path)

    def get_fuzz_dir(self) -> str:
        self.create_dir(FUZZ_DIR)
        return FUZZ_DIR

    def get_work_dir(self) -> str:
        fuzz_dir = self.get_fuzz_dir()
        work_dir = os.path.join(fuzz_dir, self.get_name())
        self.create_dir(work_dir)
        return work_dir

    def get_corpus_dir(self) -> str:
        fuzz_dir = self.get_fuzz_dir()
        corpus_dir = os.path.join(fuzz_dir, "corpus")
        self.create_dir(corpus_dir)
        return corpus_dir

    def get_crash_dir(self) -> str:
        work_dir = self.get_work_dir()
        crash_dir = os.path.join(work_dir, "crashes")
        self.create_dir(crash_dir)
        return crash_dir

    def run_script(
        self, script: str, output: bool
    ) -> subprocess.CompletedProcess[bytes]:
        return container_run_script(self.container, script, output)

    def get_pid_path(self) -> str:
        work_dir = self.get_work_dir()
        fpath = os.path.join(work_dir, "pid")
        return fpath

    def get_fuzz_log_path(self) -> str:
        work_dir = self.get_work_dir()
        fpath = os.path.join(work_dir, "fuzz_log")
        return fpath

    # for initialization
    def get_ctn_harn_path(self, loc_path: str) -> str:
        # copy logic
        work_dir = self.get_work_dir()
        ctn_path = os.path.join(work_dir, self.get_harn_name())
        os.system(f"docker cp {loc_path} {self.container}:{ctn_path}")
        return ctn_path

    # for reading
    def get_harn_path(self) -> str:
        return self.harn.ctn_path

    def get_name(self) -> str:
        time_suffix = get_time_suffix()
        return (
            f"{self.lib_name}_{self.lib_version}_{self.get_harn_name()}_{time_suffix}"
        )

    def get_harn_name(self) -> str:
        return basename(self.harn.loc_path)

    def __hash__(self):

        return hash(
            (self.container, self.lib_name, self.lib_version, self.get_harn_name())
        )
