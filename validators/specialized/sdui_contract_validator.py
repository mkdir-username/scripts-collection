
import json
import subprocess
import sys
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "metaschema" / "schema" / "strict_unversioned.json"
def validate_contract(file_path):
    """Validate a single JSON contract."""
    print(f"Validating {file_path}...")

    # 1. AJV validation
    try:
        subprocess.run(
            [
                "npx",
                "ajv",
                "validate",
                "-s",
                str(SCHEMA_PATH),
                "-d",
                str(file_path),
                "--errors=text",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"  - AJV validation passed.")
    except subprocess.CalledProcessError as e:
        print("ERROR: AJV validation failed.")
        print(e.stderr)
        return False

    # 2. Check for 'notReleased'
    with open(file_path, "r") as f:
        try:
            contract = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {file_path}: {e}")
            return False

    if find_not_released(contract):
        print(f"  - ERROR: Found elements with 'releaseVersion.web: notReleased'.")
        return False
    else:
        print(f"  - 'notReleased' check passed.")

    print(f"Validation successful for {file_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sdui_contract_validator.py <file1.json> <file2.json> ...")
        sys.exit(1)

    files_to_validate = [Path(p) for p in sys.argv[1:]]
    all_valid = True

    for file_path in files_to_validate:
        if not file_path.exists():
            print(f"WARNING: File not found: {file_path}")
            continue
        if not validate_contract(file_path):
            all_valid = False

    if not all_valid:
        print("\nValidation failed for one or more files.")
        sys.exit(1)

    print("\nAll files validated successfully.")
    sys.exit(0)
