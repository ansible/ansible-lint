#!/bin/bash
set -euo pipefail
pushd examples/playbooks/collections >/dev/null
MISSING=()
export ANSIBLE_COLLECTIONS_PATH=.
for COLLECTION in ansible.posix community.general community.molecule;
do
    COL_NAME=${COLLECTION//\./-}
    FILENAME=$(find . -maxdepth 1 -name "$COL_NAME*" -print -quit)
    if test -n "$FILENAME"
    then
        echo "Already cached $COL_NAME as $FILENAME"
    else
        MISSING+=("${COLLECTION}")
    fi
    if [ ${#MISSING[@]} -ne 0 ]; then
        ansible-galaxy collection download -p . -v "${MISSING[@]}"
        # Downloader will break our requirements.yml on download
        git checkout -- requirements.yml
    fi
done

echo "Install requirements.yml ..."
cat requirements.yml
ansible-galaxy collection install -r requirements.yml -p .
popd >/dev/null
