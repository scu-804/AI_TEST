import os
import subprocess


def start_container(container: str) -> None:
    status = os.system(f"docker start {container}")
    assert status == 0, f"Failed to start container {container}"


def container_run_script(
    container: str, script: str, output: bool
) -> subprocess.CompletedProcess[bytes]:
    docker_cmd = f"docker exec -i {container} bash -s"
    return subprocess.run(
        docker_cmd.split(), input=script.encode(), capture_output=output
    )


def create_ctn_dir_if_nonexist(dir_path: str, container: str) -> None:
    # ensure dir path passed in is absolute path
    assert dir_path.startswith(
        "/"
    ), f"dir_path {dir_path} passed in is not absolute path"
    script = f"""
if [[ ! -d {dir_path} ]]; then 
mkdir -p {dir_path}
fi
    """
    container_run_script(container, script, False)
