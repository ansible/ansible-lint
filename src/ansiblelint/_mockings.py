"""Utilities for mocking ansible modules and roles."""

from __future__ import annotations

import contextlib
import logging
import re
import sys
from typing import TYPE_CHECKING

from ansiblelint.constants import ANSIBLE_MOCKED_MODULE, RC

if TYPE_CHECKING:
    from pathlib import Path

    from ansiblelint.config import Options

_logger = logging.getLogger(__name__)


def _make_module_stub(module_name: str, options: Options) -> None:
    if not options.cache_dir:
        msg = "Cache directory not set"
        raise RuntimeError(msg)
    # a.b.c is treated a collection
    if re.match(r"^(\w+|\w+\.\w+\.[\.\w]+)$", module_name):
        parts = module_name.split(".")
        if len(parts) < 3:
            path = options.cache_dir / "modules"
            module_file = f"{options.cache_dir}/modules/{module_name}.py"
            namespace = None
            collection = None
        else:
            namespace = parts[0]
            collection = parts[1]
            path = (
                options.cache_dir
                / "collections"
                / "ansible_collections"
                / namespace
                / collection
                / "plugins"
                / "modules"
                / ("/".join(parts[2:-1]))
            )
            module_file = f"{path}/{parts[-1]}.py"
        path.mkdir(exist_ok=True, parents=True)
        _write_module_stub(
            filename=module_file,
            name=module_name,
            namespace=namespace,
            collection=collection,
        )
    else:
        _logger.error("Config error: %s is not a valid module name.", module_name)
        sys.exit(RC.INVALID_CONFIG)


def _write_module_stub(
    filename: str,
    name: str,
    namespace: str | None = None,
    collection: str | None = None,
) -> None:
    """Write module stub to disk."""
    body = ANSIBLE_MOCKED_MODULE.format(
        name=name,
        collection=collection,
        namespace=namespace,
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(body)


def _perform_mockings(options: Options) -> None:
    """Mock modules and roles."""
    path: Path
    if not options.cache_dir:
        msg = "Cache directory not set"
        raise RuntimeError(msg)
    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+$", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = (
                options.cache_dir
                / "collections"
                / "ansible_collections"
                / namespace
                / collection
                / "roles"
                / role_dir
            )
        else:
            path = options.cache_dir / "roles" / role_name
        # Avoid error from makedirs if destination is a broken symlink
        if path.is_symlink() and not path.exists():  # pragma: no cover
            _logger.warning("Removed broken symlink from %s", path)
            path.unlink(missing_ok=True)
        path.mkdir(exist_ok=True, parents=True)

    if options.mock_modules:
        for module_name in options.mock_modules:
            _make_module_stub(module_name=module_name, options=options)


def _perform_mockings_cleanup(options: Options) -> None:
    """Clean up mocked modules and roles."""
    if not options.cache_dir:
        msg = "Cache directory not set"
        raise RuntimeError(msg)
    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+$", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = (
                options.cache_dir
                / "collections"
                / "ansible_collections"
                / namespace
                / collection
                / "roles"
                / role_dir
            )
        else:
            path = options.cache_dir / "roles" / role_name
        with contextlib.suppress(OSError):
            path.rmdir()
