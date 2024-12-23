import logging
import ipdb
import os

from .utils import routines_seen

from .entities import RoutineEntry
from .utils import container_run_script, FUZZ_DIR, FUZZ_LOG
from .utils import logger, get_log_name, get_crash_dir, get_pid_name

container_fuzzcmd = {
    "vul_pytorch": 'LD_PRELOAD="$(python -c "import atheris; print(atheris.path())")/asan_with_fuzzer.so" python ./my_fuzzer.py',
    "vul_tf": "python fuzz_tensorflow.py",
    "vul_keras": "python fuzz_keras.py",
    "vul_np": "python3 fuzz_numpy.py",
    "vul_opencv": "./generateusergallerycollage_fuzzer",
    "vul_pandas": "python3 fuzz_pandas.py",
    "vul_pillow": 'LD_PRELOAD="$(python -c "import atheris; print(atheris.path())")/asan_with_fuzzer.so" python ./fuzz_pil.py',
    "vul_scipy": "python3 fuzz_scipy.py",
}

# params needed: fuzz_dir, fuzz_cmd, fuzz_log
start_script_template = """ 
# directory setup
fuzz_dir='{fuzz_dir}'
if [[ ! -d "$fuzz_dir" ]]; then
  mkdir "$fuzz_dir"
fi

crash_dir='{crash_dir}'
if [[ ! -d "$crash_dir" ]]; then
    mkdir -p "$crash_dir"
fi

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
  if [[ "$CONDA_DEFAULT_ENV" == 'atheris' ]]; then
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

{fuzz_cmd} -artifact_prefix="$crash_dir" 2>"$fuzz_dir"/{fuzz_log} &
echo "$!" > "$fuzz_dir"/{pid_name}
"""


def get_start_script(routine: RoutineEntry, fuzz_cmd: str) -> str:
    routine_name = routine.get_name()
    crash_dir = get_crash_dir(routine_name)
    log_name = get_log_name(routine_name)
    pid_name = get_pid_name(routine_name)
    return start_script_template.format(
        fuzz_dir=FUZZ_DIR,
        fuzz_cmd=fuzz_cmd,
        fuzz_log=log_name,
        crash_dir=crash_dir,
        pid_name=pid_name,
        lib_name=routine.lib_name,
        lib_version=routine.lib_version,
    )


def exec_routine(routine: RoutineEntry, fuzz_cmd: str) -> bool:
    """
    returns whether the script executes successfully
    """
    script = get_start_script(routine, fuzz_cmd)
    proc = container_run_script(routine.container, script, False)
    return proc.returncode == 0
    # add_container_cwd(container, cwd)


def get_fuzzcmd(container: str) -> str:
    fuzz_cmd = container_fuzzcmd.get(container)
    assert fuzz_cmd
    return fuzz_cmd


def start_routine(routine: RoutineEntry) -> bool:
    if routine in routines_seen:
        logger.warning(f"{routine.get_name()} is already running...")
        return False
    container = routine.container
    os.system(f"docker start {container}")
    fuzz_cmd = get_fuzzcmd(container)
    flag = exec_routine(routine, fuzz_cmd)
    if not flag:
        logger.error(f"{routine.get_name()} fails to start")
        return False

    routines_seen.add(routine)
    logger.info(f"{routine.get_name()} started successfully")
    return True


# def start(container: str) -> None:
#     """
#     container: container name
#     script: path of the script to execute inside docker container
#     """
#     logger.info("starting docker container...")
#     # start docker container
#     os.system(f"docker start {container}")
#
#     # run service
#     fuzz_cmd = container_fuzzcmd.get(container)
#     assert fuzz_cmd
#     exec_routine(container, fuzz_cmd)
