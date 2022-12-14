#!/bin/bash
set -euo pipefail
pushd examples/playbooks/collections
MISSING=()
for COLLECTION in ansible.posix community.general community.molecule;
do
    FILE=${COLLECTION//\./-}
    if test -n "$(find . -maxdepth 1 -name '$FILE*' -print -quit)"
    then
        echo "Already cached $FILE"
    else
        MISSING+=("${COLLECTION}")
    fi
    if [ ${#MISSING[@]} -ne 0 ]; then
        ansible-galaxy collection download -p . -v "${MISSING[@]}"
    fi
done

echo "Install requirements.yml ..."
cat requirements.yml
ansible-galaxy collection install -r requirements.yml -p .
popd
