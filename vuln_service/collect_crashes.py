from vuln_service.entities import RoutineEntry
from .utils import (
    container_run_script,
    get_crash_dir,
    get_crash_zip_path,
)


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


def get_zip_script(routine: RoutineEntry) -> str:
    crash_dir = get_crash_dir(routine.get_name())
    return zip_script_template.format(
        crash_dir=crash_dir, crash_zip_path=get_crash_zip_path(routine.get_name())
    )


def collect_crashes(routine: RoutineEntry) -> str  :
    """
    returns path of target zip file
    """
    script = get_zip_script(routine)
    proc = container_run_script(routine.container, script, True)
    if proc.returncode != 0:
        return None
    return get_crash_zip_path(routine.get_name())
