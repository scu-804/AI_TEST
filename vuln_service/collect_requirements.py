import os
from .utils import FUZZ_DIR, REQ_NAME, container_run_script, get_data_dir

collect_requirements_script_template = """

fuzz_dir='{fuzz_dir}'
req_name='{req_name}'
if [[ ! -d "$fuzz_dir" ]]; then
  mkdir "$fuzz_dir"
fi

req_path="$fuzz_dir"/"$req_name"

source /root/.bashrc
pip freeze > "$req_path"
"""


def get_collect_requirements_script() -> str:
    return collect_requirements_script_template.format(
        fuzz_dir=FUZZ_DIR, req_name=REQ_NAME
    )


def get_container_req_path() -> str:
    return f"{FUZZ_DIR}/{REQ_NAME}"


def collect_requirements(container_name: str) -> None:
    os.system(f"docker start {container_name}")
    script = get_collect_requirements_script()
    container_run_script(container_name, script, False)
    fname = f"req_{container_name}.txt"
    src_path = get_container_req_path()
    dst_path = os.path.join(get_data_dir(), fname)
    os.system(f"docker cp {container_name}:{src_path} {dst_path}")
