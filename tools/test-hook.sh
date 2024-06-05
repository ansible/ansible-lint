#!/bin/bash
# This scripts checks if ansible-lint works as a hook as expected.
SOURCE=${BASH_SOURCE[0]}
while [ -L "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )

set -euo pipefail
rm -rf .tox/x
mkdir -p .tox/x
cd .tox/x
git init --initial-branch=main
# we add a file to the repo to avoid error due to no file to to lint
touch foo.yml
git add foo.yml
python3 -m pre_commit try-repo -v "${DIR}/.." ansible-lint
