from .utils import container_run_script, get_container_cwd

CRASH_ZIP_PATH = "/crashes.zip"

zip_script_template = """

# Directory containing the crash files
CRASH_DIR="{crash_dir}"

# Output zip file
OUTPUT_ZIP="{crash_zip_path}"

# dependency setup
if [[ "$(which zip)" != '/usr/bin/zip' ]]; then
        apt install -y zip
fi

# Check if the crash directory exists
if [ ! -d "$CRASH_DIR" ]; then
    exit 1
fi

# Find files starting with 'crash-' and compress them into a zip file
echo "Collecting crash files from $CRASH_DIR..."
find "$CRASH_DIR" -mindepth 1 -maxdepth 1 -type f -name 'crash-*' | zip -j "$OUTPUT_ZIP" -@

# Check if the zip file was created successfully
if [ $? -eq 0 ]; then
    echo "$OUTPUT_ZIP"
else
    echo "Error: Failed to create the zip file."
    exit 1
fi

find "$CRASH_DIR" -mindepth 1 -maxdepth 1 -type f -name 'crash-*' -exec rm '{{}}' \\+
"""


def get_zip_script(cwd: str) -> str:
    return zip_script_template.format(crash_dir=cwd, crash_zip_path=CRASH_ZIP_PATH)


def collect_crashes(container: str) -> str:
    """
    returns path of target zip file
    """
    cwd = get_container_cwd(container)
    assert cwd
    script = get_zip_script(cwd)
    proc = container_run_script(container, script, True)
    if proc.returncode != 0:
        return None
    return CRASH_ZIP_PATH
