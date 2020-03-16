#!/bin/bash
set -Eeuxo pipefail
# Used by Zuul CI to perform extra bootstrapping

# Bumping system tox because version from CentOS 7 is too old
# We are not using pip --user due to few bugs in tox role which does not allow
# us to override how is called. Once these are addressed we will switch back
# non-sudo mode.
sudo yum remove -y python-tox || true

PYTHON=$(command -v python3 python | head -n1)

$PYTHON -m pip install --user "pip>=20.0.2"
$PYTHON -m pip install --user "virtualenv>=20.0.10"
$PYTHON -m pip install --user "tox>=3.8.0" "tox-venv" "zipp<0.6.0;python_version=='2.7'"

# testing
$PYTHON -m virtualenv --version
$PYTHON -m tox --version
tox --version
