#!/usr/bin/env python

"""Pre-commit hook script to keep requirements.txt up-to-date"""

import hashlib
import subprocess
import sys
from pathlib import Path

pre_checksum = "x"
post_checksum = "x"

requirements = Path("requirements.txt")

if requirements.is_file():
    with requirements.open(mode="rb") as requirements_file:
        data = requirements_file.read()
        pre_checksum = hashlib.md5(data).hexdigest()
        print(f"pre_checksum={pre_checksum}")

subprocess.run(
    ["poetry", "export", "--format", "requirements.txt", "--output", "requirements.txt"]
)

with requirements.open(mode="rb") as requirements_file:
    data = requirements_file.read()
    post_checksum = hashlib.md5(data).hexdigest()
    print(f"post_checksum={post_checksum}")

if pre_checksum != post_checksum:
    sys.exit(1)
