#!/bin/bash
set -euo pipefail
echo "Install requirements.yml ..."
ansible-galaxy collection install -r requirements.yml -p examples/playbooks/collections
