import logging
import ipdb
import os


from .entities import RoutineEntry
from .utils import container_run_script, FUZZ_DIR, FUZZ_LOG
from .utils import logger


# params needed: fuzz_dir, fuzz_cmd, fuzz_log
start_script_template = """ 
fuzz_dir='{fuzz_dir}'

corpus_dir='{corpus_dir}'
crash_dir='{crash_dir}/'
pid_path='{pid_path}'

source /root/.bashrc

# conda env management

search_conda_env() {{
  if [[ -z $1 ]]; then
    echo "Usage: $0 <keyword>"
    exit 1
  fi

  keyword=$1

  # Get the list of Conda environments and filter for the keyword
  matching_env=$(conda env list | grep -v '^#' | grep -i "$keyword" | awk '{{print $1}}' | head -n 1)

  if [[ -n "$matching_env" ]]; then
    echo "$matching_env"
  fi
}}

pip_install() {{
while read -r pac; do
if ! pip install "$pac" ; then
echo "install $pac failed. Skipping"
fi
done < requirements.txt
}}

check_fail_exit(){{
    if [[ $? != 0 ]]; then 
        if [[ -n "$CONDA_DEFAULT_ENV" ]]; then 
            conda deactivate
        fi
        conda env remove -n "$target_env" -y
        exit 1
    fi
}}

conda_manage() {{
  lib_name='{lib_name}'
  lib_version='{lib_version}'

  flag_file='/.no_conda'

  target_env="$lib_name"_"$lib_version"

  if [[ -z "$(which conda)" ]]; then
    return
  fi
  if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
    return
  fi

    if [[ -f "$flag_file" ]]; then
        return 
    fi

  env=$(search_conda_env "$target_env")
  if [[ -n "$env" ]]; then
    conda activate "$env"
    echo "CONDA ENV: target env $target_env activated directly"
    return
  fi

  cand_env=$(search_conda_env "$lib_name"_)
  if [[ -n "$cand_env" ]]; then
    echo "CONDA ENV: candidate env $cand_env found"
    conda create --clone "$cand_env" --name "$target_env" -y
    check_fail_exit

    conda activate "$target_env"
    pip install "$lib_name"=="$lib_version"
    check_fail_exit

    echo "CONDA ENV: target env $target_env activated by cloning existing env $cand_env"
  else
    echo "CONDA ENV: creating $target_env from scratch"
    pip freeze >requirements.txt
    conda create -n "$target_env" python=3.10 -y
    check_fail_exit

    conda activate "$target_env"
    pip_install
    pip install "$lib_name"=="$lib_version"
    check_fail_exit

  fi
}}

conda_manage

{fuzz_cmd} "$corpus_dir" -artifact_prefix="$crash_dir" 2>{log_path} &
echo "$!" > "$pid_path"
"""


def get_start_script(routine: RoutineEntry, fuzz_cmd: str) -> str:
    crash_dir = routine.get_crash_dir()
    log_path = routine.get_fuzz_log_path()
    pid_path = routine.get_pid_path()
    corpus_dir = routine.get_corpus_dir()

    # crash_dir = get_routine_crash_dir(routine_name)
    # log_name = get_log_name(routine_name)
    # pid_name = get_pid_name(routine_name)
    # corpus_dir = get_routine_corpus_dir(routine_name)
    return start_script_template.format(
        fuzz_dir=FUZZ_DIR,
        fuzz_cmd=fuzz_cmd,
        log_path=log_path,
        crash_dir=crash_dir,
        pid_path=pid_path,
        lib_name=routine.lib_name,
        lib_version=routine.lib_version,
        corpus_dir=corpus_dir,
    )


def exec_routine(routine: RoutineEntry, fuzz_cmd: str) -> bool:
    """
    returns whether the script executes successfully
    """
    script = get_start_script(routine, fuzz_cmd)
    proc = container_run_script(routine.container, script, False)
    return proc.returncode == 0
    # add_container_cwd(container, cwd)


def start_routine(routine: RoutineEntry) -> bool:
    container = routine.container
    os.system(f"docker start {container}")
    fuzz_cmd = routine.get_fuzz_cmd()
    flag = exec_routine(routine, fuzz_cmd)
    if not flag:
        logger.error(f"{routine.get_name()} fails to start")
        return False

    logger.info(f"{routine.get_name()} started successfully")
    return True
