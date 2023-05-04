#!/usr/bin/env bash
set -eu
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [[ -d "${SCRIPT_DIR}/../.cache/eco/.git" ]]; then
  git -C "${SCRIPT_DIR}/../.cache/eco" pull
else
  mkdir -p "${SCRIPT_DIR}/../.cache"
  git clone --recursive https://github.com/ansible-community/ansible-lint-eco "${SCRIPT_DIR}/../.cache/eco"
fi
pushd "${SCRIPT_DIR}/../.cache/eco/projects" > /dev/null


for i in $(ls -d */); do
  DIR=${i%%/}
  RC=0
  pushd $DIR > /dev/null
  # Calling ansible lint without any positional arguments inside repository root
  SECONDS=0
  ANSIBLE_LINT_IGNORE_FILE=../$DIR.ignore.txt ansible-lint -qq --generate-ignore -f codeclimate | python3 -m json.tool > ../$DIR.json ||
  RC=$?
  echo "Got $RC RC on $DIR in $SECONDS seconds"
  popd > /dev/null
done
popd > /dev/null
# Fail if git reports dirty at the end
git diff --exit-code
