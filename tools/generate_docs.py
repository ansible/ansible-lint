#!/bin/env python3
"""Script that tests rule markdown documentation."""
import subprocess

subprocess.run(
    "ansible-lint -L --format=md",  # noqa: S607
    shell=True,  # noqa: S602
    check=True,
    stdout=subprocess.DEVNULL,
)
