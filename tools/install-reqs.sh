#!/bin/bash
set -euo pipefail
echo "Install requirements.yml ..."

max_attempts=5
delay_seconds=15
attempt=1

while true; do
  if ansible-galaxy collection install -r requirements.yml -p examples/playbooks/collections; then
    break
  fi
  if (( attempt >= max_attempts )); then
    echo "ansible-galaxy collection install failed after ${max_attempts} attempts" >&2
    exit 1
  fi
  echo "ansible-galaxy collection install failed (attempt ${attempt}/${max_attempts}), retrying in ${delay_seconds}s..." >&2
  attempt=$((attempt + 1))
  sleep "${delay_seconds}"
done
