#!/bin/bash
set -euxo pipefail
# Used by Zuul CI to perform extra bootstrapping

# sudo used only because currently zuul default tox_executable=tox instead of
# "python3 -m tox"
# https://zuul-ci.org/docs/zuul-jobs/python-roles.html#rolevar-ensure-tox.tox_executable

# Install pip if not already install on the system
python3 -m pip --version || {
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    sudo python3 get-pip.py
}

# Workaround until ensure-tox will allow upgrades
# https://review.opendev.org/#/c/690057/
sudo python3 -m pip install -U tox
