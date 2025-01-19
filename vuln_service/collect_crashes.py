from vuln_service.entities import RoutineEntry


def collect_crashes(routine: RoutineEntry) -> str | None:
    """
    returns path of target zip file
    """
    crash_dir = routine.get_crash_dir()
    crash_zip_path = routine.get_crash_zip_path()
    script = f"""

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
find "$CRASH_DIR" -mindepth 1 -maxdepth 1 -type f | zip -j "$OUTPUT_ZIP" -@

# Check if the zip file was created successfully
if [ $? -eq 0 ]; then
    echo "$OUTPUT_ZIP"
else
    echo "Error: Failed to create the zip file."
    exit 1
fi

find "$CRASH_DIR" -mindepth 1 -maxdepth 1 -type f -name 'crash-*' -exec rm '{{}}' \\+
"""
    proc = routine.run_ctn_script(script, False)
    if proc.returncode != 0:
        return None
    return routine.get_crash_zip_path()
