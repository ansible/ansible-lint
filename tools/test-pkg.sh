#!/usr/bin/env bash
set -euxo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

VERSION=$(python -m setuptools_scm)

TEST_DIR=${TOX_WORK_DIR:-.tox}/pkg/smoke
mkdir -p "$TEST_DIR"
rm -rf "${TEST_DIR:?}"/*

pushd "$TEST_DIR" > /dev/null

cat > pyproject.toml <<EOF
[project]
name = "2"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13.7"
dependencies = []

[[tool.uv.index]]
name = "local"
url = "../../../dist"
format = "flat"
EOF

uv add "ansible-lint==$VERSION"

popd > /dev/null
