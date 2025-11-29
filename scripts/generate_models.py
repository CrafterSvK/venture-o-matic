import subprocess
from pathlib import Path

SCHEMA_DIR = Path("schemas")
OUTPUT_DIR = Path("generated")

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    cmd = [
        "datamodel-codegen",
        "--input", str(SCHEMA_DIR),
        "--input-file-type", "jsonschema",
        "--reuse-model",
        "--use-title-as-name",
        "--target-python-version", "3.13",
        "--output", str(OUTPUT_DIR),
    ]

    subprocess.run(cmd, check=True)
