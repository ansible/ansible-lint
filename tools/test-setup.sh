#!/bin/bash
# This tool is used to setup the environment for running the tests. Its name
# name and location is based on Zuul CI, which can automatically run it.
set -euo pipefail

# User specific environment
# shellcheck disable=SC2076
if ! [[ "$PATH" =~ "$HOME/.local/bin" ]]
then
    PATH="$HOME/.local/bin:$PATH"
fi

if [ -f "/usr/bin/apt-get" ]; then
    if [ ! -f "/var/cache/apt/pkgcache.bin" ]; then
        sudo apt-get update  # mandatory or other apt-get commands fail
    fi
    # avoid outdated ansible and pipx
    sudo apt-get remove -y ansible pipx || true
    # cspell:disable-next-line
    sudo apt-get install -y --no-install-recommends -o=Dpkg::Use-Pty=0 \
        git python3-venv python3-pip
fi

which pipx || python3 -m pip install --user pipx
which -a pipx
which pre-commit || pipx install pre-commit
which tox || pipx install tox

# Log some useful info in case of unexpected failures:
uname
python3 --version
tox --version
pre-commit --version
