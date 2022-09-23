"""Utilities for mocking ansible modules and roles."""
from __future__ import annotations

import logging
import os
import re
import sys

from ansiblelint.config import options
from ansiblelint.constants import ANSIBLE_MOCKED_MODULE, INVALID_CONFIG_RC

_logger = logging.getLogger(__name__)


def _make_module_stub(module_name: str) -> None:
    # a.b.c is treated a collection
    if re.match(r"^(\w+|\w+\.\w+\.[\.\w]+)$", module_name):
        parts = module_name.split(".")
        if len(parts) < 3:
            path = f"{options.cache_dir}/modules"
            module_file = f"{options.cache_dir}/modules/{module_name}.py"
            namespace = None
            collection = None
        else:
            namespace = parts[0]
            collection = parts[1]
            path = f"{ options.cache_dir }/collections/ansible_collections/{ namespace }/{ collection }/plugins/modules/{ '/'.join(parts[2:-1]) }"
            module_file = f"{path}/{parts[-1]}.py"
        os.makedirs(path, exist_ok=True)
        _write_module_stub(
            filename=module_file,
            name=module_file,
            namespace=namespace,
            collection=collection,
        )
    else:
        _logger.error("Config error: %s is not a valid module name.", module_name)
        sys.exit(INVALID_CONFIG_RC)


def _write_module_stub(
    filename: str,
    name: str,
    namespace: str | None = None,
    collection: str | None = None,
) -> None:
    """Write module stub to disk."""
    body = ANSIBLE_MOCKED_MODULE.format(
        name=name, collection=collection, namespace=namespace
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(body)


# pylint: disable=too-many-branches
def _perform_mockings() -> None:  # noqa: C901
    """Mock modules and roles."""
    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+$", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = f"{options.cache_dir}/collections/ansible_collections/{ namespace }/{ collection }/roles/{ role_dir }/"
        else:
            path = f"{options.cache_dir}/roles/{role_name}"
        # Avoid error from makedirs if destination is a broken symlink
        if os.path.islink(path) and not os.path.exists(path):
            _logger.warning("Removed broken symlink from %s", path)
            os.unlink(path)
        os.makedirs(path, exist_ok=True)

    if options.mock_modules:
        for module_name in options.mock_modules:
            _make_module_stub(module_name)


def _perform_mockings_cleanup() -> None:  # noqa: C901
    """Clean up mocked modules and roles."""
    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+$", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = f"{options.cache_dir}/collections/ansible_collections/{ namespace }/{ collection }/roles/{ role_dir }/"
        else:
            path = f"{options.cache_dir}/roles/{role_name}"
        try:
            os.rmdir(path)
        except OSError:
            pass
