#!/bin/bash
set -euo pipefail
echo "Ensure git submodules are initialized ..."
git submodule update --init
echo "Install requirements.yml ..."
ansible-galaxy collection install -r requirements.yml -p examples/playbooks/collections
