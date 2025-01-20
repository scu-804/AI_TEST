from dataclasses import dataclass
from os.path import basename
import os
from posix import initgroups
import subprocess

from vuln_service.utils.container import start_container

from .read import (
    ExitReason,
    ExitStatus,
    RoutineStatus,
    exit_status_judge,
    is_exit_code_line,
)

from vuln_service.utils import logger

from vuln_service.utils import (
    FUZZ_DIR,
    container_run_script,
    create_ctn_dir_if_nonexist,
    get_time_suffix,
)

ctn_fuzz_cmd_template = {
    "vul_pytorch": 'LD_PRELOAD="$(python -c "import atheris; print(atheris.path())")/asan_with_fuzzer.so" python {harn_path}',
    "vul_tf": "python {harn_path}",
    "vul_keras": "python {harn_path}",
    "vul_np": 'LD_PRELOAD="$(python3 -c "import atheris; print(atheris.path())")/asan_with_fuzzer.so" python3 {harn_path}',
    "vul_opencv": "./generateusergallerycollage_fuzzer",
    "vul_pandas": "python3 {harn_path}",
    "vul_pillow": 'LD_PRELOAD="$(python -c "import atheris; print(atheris.path())")/asan_with_fuzzer.so" python {harn_path}',
    "vul_scipy": "python3 {harn_path}",
}


@dataclass()
class Harness:
    loc_path: str
    ctn_path: str

    def __init__(self, loc_path: str, ctn_path: str) -> None:
        self.loc_path = loc_path
        self.ctn_path = ctn_path

    def get_name(self) -> str:
        return basename(self.loc_path)


@dataclass()
class RoutineEntry:
    container: str
    lib_name: str
    lib_version: str
    harn: Harness

    name: str
    fuzz_cmd: str
    work_dir: str
    time_suffix: str

    inited: bool

    def __init__(
        self,
        container: str,
        lib_name: str,
        lib_version: str,
        harn_path: str,
        time_suffix: None | str = None,
    ) -> None:
        self.container = container
        self.lib_name = lib_name
        self.lib_version = lib_version
        self.inited = False
        if time_suffix is None:
            self.time_suffix = get_time_suffix()
        else:
            self.time_suffix = time_suffix

        self.start_container()
        self.init_harness(harn_path)
        # fuzz_cmd initlization needed
        #
        self.inited = True

    ### for initialization
    def start_container(self) -> None:
        start_container(self.container)

    def create_ctn_dir(self, dir_path: str) -> None:
        create_ctn_dir_if_nonexist(dir_path, self.container)

    def init_harness(self, loc_path: str) -> None:
        ctn_path = self.get_ctn_harn_path(loc_path)
        self.harn = Harness(loc_path, ctn_path)

    def get_ctn_work_dir_by_locpath(self, loc_path: str) -> str:
        fuzz_dir = self.get_fuzz_dir()
        work_dir = os.path.join(fuzz_dir, self.get_name_by_locpath(loc_path))
        self.create_ctn_dir(work_dir)
        self.work_dir = work_dir
        return work_dir

    def get_name_by_locpath(self, loc_path: str) -> str:
        name = f"{self.lib_name}_{self.lib_version}_{self.get_harn_name_by_locpath(loc_path)}_{self.get_time_suffix()}"
        self.name = name
        return name

    def get_harn_name_by_locpath(self, loc_path: str) -> str:
        return basename(loc_path)

    def judge_ctn_path_exists(self, path: str) -> bool:
        script = f"""
if [[ -e {path} ]]; then
exit 0
else 
exit 1
fi
        """
        proc = self.run_ctn_script(script, False)
        return proc.returncode == 0

    def copy_to_ctn_harn(self, loc_path: str, ctn_path: str) -> None:
        flag = self.judge_ctn_path_exists(ctn_path)
        # judge if it exists
        if not flag:
            os.system(f"docker cp {loc_path} {self.container}:{ctn_path}")

    def get_ctn_harn_path(self, loc_path: str) -> str:
        # copy logic
        work_dir = self.get_ctn_work_dir_by_locpath(loc_path)
        ctn_path = os.path.join(work_dir, self.get_harn_name_by_locpath(loc_path))
        self.copy_to_ctn_harn(loc_path, ctn_path)
        return ctn_path

    ### get attributes
    def get_time_suffix(self) -> str:
        assert self.time_suffix is not None
        return self.time_suffix

    def get_fuzz_cmd(self) -> str:
        fc_temp = ctn_fuzz_cmd_template.get(self.container)
        assert isinstance(
            fc_temp, str
        ), f"Failed to get fuzz cmd template for {self.container}"
        if "python" not in fc_temp:
            return fc_temp
        return fc_temp.format(harn_path=self.get_harn_path())

    ### directory part

    def get_fuzz_dir(self) -> str:
        self.create_ctn_dir(FUZZ_DIR)
        return FUZZ_DIR

    def get_work_dir(self) -> str:
        assert self.inited
        return self.work_dir

    def get_corpus_dir(self) -> str:
        fuzz_dir = self.get_fuzz_dir()
        corpus_dir = os.path.join(fuzz_dir, "corpus")
        self.create_ctn_dir(corpus_dir)
        return corpus_dir

    def get_crash_dir(self) -> str:
        work_dir = self.get_work_dir()
        crash_dir = os.path.join(work_dir, "crashes")
        self.create_ctn_dir(crash_dir)
        return crash_dir

    def get_crash_zip_path(self) -> str:
        work_dir = self.get_work_dir()
        zip_path = os.path.join(work_dir, "crashes.zip")
        return zip_path

    def run_ctn_script(
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

    # for reading
    def get_harn_path(self) -> str:
        assert self.inited
        return self.harn.ctn_path

    def get_name(self) -> str:
        assert self.inited
        return self.name

    def __hash__(self):

        return hash(
            (self.container, self.lib_name, self.lib_version, self.harn.get_name())
        )

    def check_exit_status(self) -> ExitStatus:
        """
        1 finished, 2 running
        """
        pid_path = self.get_pid_path()
        script = f"""
    pid_path={pid_path}
    if [[ ! -f "$pid_path" ]]; then 
        exit 2
    fi

    pid=$(cat "$pid_path")

    ps -p "$pid"
        """

        proc = container_run_script(self.container, script, False)
        # pid file is cleaned
        if proc.returncode == 2:
            return ExitStatus.CLN
        # query success
        if proc.returncode == 0:
            return ExitStatus.RUN

        # pid file exists and query fails
        return ExitStatus.PAR

    def is_partial_exit(self) -> bool:
        status = self.check_exit_status()
        return status == ExitStatus.PAR

    def is_cleaned_exit(self) -> bool:
        status = self.check_exit_status()
        return status == ExitStatus.CLN

    def read_log(self) -> str | None:
        log_path = self.get_fuzz_log_path()
        # log_path = get_self_fuzz_log_path(routine)
        script = f"""
fpath="{log_path}"

if [[ ! -f "$fpath" ]]; then 
    echo "target log file $fpath does not exits"
    exit 2
fi

cat "$fpath"
        """
        proc = container_run_script(self.container, script, True)
        if proc.returncode != 0:
            if proc.returncode == 2:
                return None
            else:
                assert False, f"failed to read log file for routine {self.get_name()}"

        log_content = proc.stdout.decode()
        return log_content

    def check_exit_reason(self) -> ExitReason:
        """
        Invoked only in exited situation
        """
        log_content = self.read_log()
        assert log_content, f"Failed to read backup log of routine {self.get_name()}"
        lines = log_content.splitlines()
        for line in reversed(lines):
            line = line.rstrip()
            if not is_exit_code_line(line):
                continue

            reason = exit_status_judge(line)
            return reason
        assert False, f"Routine {self.get_name()} is still running"

    def clean_pid(self) -> None:
        pid_path = self.get_pid_path()
        script = f"""
    rm {pid_path}
        """
        self.run_ctn_script(script, False)

    def clean_after_stop(self) -> None:
        logger.debug(f"Cleaning {self.get_name()} routine info...")
        self.clean_pid()

    def show_exit_reason(self) -> None:
        reason = self.check_exit_reason()
        if reason == ExitReason.SAN:
            logger.debug(f"routine {self.get_name()} exited for crash")
        elif reason == ExitReason.INTER:
            logger.debug(f"routine {self.get_name()} exited for interruption")
        else:
            assert False, f"routine {self.get_name()} exited for unsupported reason"
