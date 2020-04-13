#!/bin/bash
set -euxo pipefail
# Used by Zuul CI to perform extra bootstrapping

PYTHON=$(command -v python3 python | head -n1)

sudo $PYTHON -m pip install -U tox
