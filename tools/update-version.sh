#!/bin/bash
DIR=$(dirname "$0")
VERSION=$(./tools/get-version.sh)
mkdir -p "${DIR}/../dist"
sed -e "s/VERSION_PLACEHOLDER/${VERSION}/" \
    "${DIR}/../.config/ansible-lint.spec" \
    > "${DIR}/../dist/ansible-lint.spec"
# validate the produced spec file:
rpmlint -s .dist/ansible-lint.spec
