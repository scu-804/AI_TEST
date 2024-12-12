import os
from .helper import (
    check_container_cd,
    check_container_clean,
    check_proxy,
    conda_init,
    copy_condarc,
    set_pip_index,
    show_conda_env_name,
)

from posixpath import basename

from .utils import container_run_script

from .utils import logger


container_list = [
    "yqy_atheris_pt",
    "yqy_atheris_tf",
    "yqy_atheris_keras",
    "yqy_atheris_np",
    "yqy_fuzz_opencv",
    "yqy_atheris_pandas",
    "yqy_atheris_pillow",
    "yqy_atheris_scipy",
]


test_conda_script = """
source /root/.bashrc
which conda
"""


def test_conda(container: str) -> None:
    os.system(f"docker start {container}")
    proc = container_run_script(container, test_conda_script, True)
    res = proc.stdout.decode().strip()
    flag = basename(res) == "conda"
    if not flag:
        logger.error(f"no conda installed in {container}")


def test_all_containers() -> None:
    for container in container_list:
        check_container_clean(container)
