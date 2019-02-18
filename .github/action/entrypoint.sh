#!/bin/sh
set -e

cd "${GITHUB_WORKSPACE}"

ACTION_PLAYBOOK_NAME="${ACTION_PLAYBOOK_NAME:-playbook.yml}"
ACTION_PLAYBOOK_PATH="${GITHUB_WORKSPACE}/${ACTION_PLAYBOOK_NAME}"

if [ -f "${ACTION_PLAYBOOK_PATH}" ]; then
  echo
  echo "==> Linting ${ACTION_PLAYBOOK_PATH}…"
  ansible-lint "${ACTION_PLAYBOOK_PATH}"
  echo
else
  exit 1
fi
