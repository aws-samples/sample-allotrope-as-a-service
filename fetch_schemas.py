"""
Fetch official Allotrope ASM JSON schemas for DVaaS validation.
Run before deploying the DVaaS Lambda to bundle schemas.

Usage:
    python fetch_schemas.py
"""

import subprocess
import shutil
import os

REPO_URL = "https://gitlab.com/allotrope-public/asm.git"
TEMP_DIR = "temp-asm-schemas"
TARGET_DIR = os.path.join("services", "dvaas", "schemas")


def fetch():
    print("Cloning Allotrope ASM schema repository...")
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, TEMP_DIR],
        check=True,
    )

    # Copy json-schemas and manifests
    for subdir in ["json-schemas", "manifests"]:
        src = os.path.join(TEMP_DIR, subdir)
        dst = os.path.join(TARGET_DIR, subdir)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"Copied {subdir} -> {dst}")

    # Clean up
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    # Count
    schema_count = sum(
        1 for _ in _walk_json(os.path.join(TARGET_DIR, "json-schemas"))
    )
    manifest_count = sum(
        1 for _ in _walk_json(os.path.join(TARGET_DIR, "manifests"))
    )
    print(f"Done: {schema_count} schemas, {manifest_count} manifests")


def _walk_json(path):
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".json"):
                yield os.path.join(root, f)


if __name__ == "__main__":
    fetch()
