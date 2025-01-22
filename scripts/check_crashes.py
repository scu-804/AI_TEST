import subprocess
import argparse


def container_run_script(
    container: str, script: str, output: bool
) -> subprocess.CompletedProcess[bytes]:
    docker_cmd = f"docker exec -i {container} bash -s"
    return subprocess.run(
        docker_cmd.split(), input=script.encode(), capture_output=output
    )


def run_check(container: str) -> None:
    script = """
find /fuzz -type d -name '*crashes*' | sort | while read -r dir; do 
num=$(find $dir -type f | wc -l)
echo "$dir: $num"
done 
    """
    container_run_script(container, script, False)


def check_crashes() -> None:
    parser = argparse.ArgumentParser(description="check crashes in a container")
    parser.add_argument("container", help="name of the container")

    args = parser.parse_args()
    container = args.container
    assert isinstance(container, str), "Failed to get container name parameter"
    run_check(container)


if __name__ == "__main__":
    check_crashes()
