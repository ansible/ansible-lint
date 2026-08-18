"""Utilities for mocking ansible modules and roles."""

from __future__ import annotations

import contextlib
import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ansiblelint.constants import ANSIBLE_MOCKED_MODULE, MOCK_MODULE_MARKER, RC

if TYPE_CHECKING:
    from ansiblelint.config import Options

_logger = logging.getLogger(__name__)


def is_lint_mock_module(path: str | Path | None) -> bool:
    """Return True if path is an ansible-lint generated module stub."""
    if not path:
        return False
    module_path = Path(path)
    if not module_path.is_file():
        return False
    try:
        with module_path.open(encoding="utf-8") as handle:
            first_line = handle.readline().rstrip("\n")
    except OSError:
        return False
    return first_line == MOCK_MODULE_MARKER


def _collection_module_relpath(module_name: str) -> Path | None:
    """Return ansible_collections-relative path for an FQCN module name."""
    parts = module_name.split(".")
    if len(parts) < 3:
        return None
    namespace, collection = parts[0], parts[1]
    subdirs = Path(*parts[2:-1]) if len(parts) > 3 else Path()
    return (
        Path("ansible_collections")
        / namespace
        / collection
        / "plugins"
        / "modules"
        / subdirs
        / f"{parts[-1]}.py"
    )


def _warn_if_mock_clobbered_real_collections(options: Options) -> None:
    """Warn when previously written stubs still sit under real collections."""
    if not options.cache_dir or not options.mock_modules:
        return
    real_collections = options.cache_dir / "collections"
    for module_name in options.mock_modules:
        relpath = _collection_module_relpath(module_name)
        if relpath is None:
            continue
        candidate = real_collections / relpath
        if is_lint_mock_module(candidate):
            _logger.warning(
                "Found ansible-lint mock stub at %s under the real collections "
                "path. Reinstall affected collections "
                "(ansible-galaxy collection install ... --force).",
                candidate,
            )
            return


def _make_module_stub(module_name: str, options: Options) -> None:
    mock_root = options.mock_root
    mock_collections_path = options.mock_collections_path
    mock_modules_path = options.mock_modules_path
    if not mock_root or not mock_collections_path or not mock_modules_path:
        msg = "Cache directory not set"
        raise RuntimeError(msg)
    # a.b.c is treated a collection
    if re.match(r"^(\w+|\w+\.\w+\.[\.\w]+)$", module_name):
        parts = module_name.split(".")
        if len(parts) < 3:
            path = mock_modules_path
            module_file = path / f"{module_name}.py"
            namespace = None
            collection = None
        else:
            namespace = parts[0]
            collection = parts[1]
            relpath = _collection_module_relpath(module_name)
            if relpath is None:  # pragma: no cover
                msg = f"Invalid module name: {module_name}"
                raise RuntimeError(msg)
            module_file = mock_collections_path / relpath
            path = module_file.parent
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
    filename: str | Path,
    name: str,
    namespace: str | None = None,
    collection: str | None = None,
) -> None:
    """Write module stub to disk without overwriting real modules."""
    module_path = Path(filename)
    if module_path.exists() and not is_lint_mock_module(module_path):
        _logger.debug(
            "Skipping mock stub for %s; existing non-mock module at %s",
            name,
            module_path,
        )
        return
    body = ANSIBLE_MOCKED_MODULE.format(
        name=name,
        collection=collection,
        namespace=namespace,
    )
    with module_path.open("w", encoding="utf-8") as handle:
        handle.write(body)


def _perform_mockings(options: Options) -> None:
    """Mock modules and roles."""
    mock_root = options.mock_root
    mock_collections_path = options.mock_collections_path
    if not mock_root or not mock_collections_path:  # pragma: no cover
        msg = "Cache directory not set"
        raise RuntimeError(msg)
    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+$", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = (
                mock_collections_path
                / "ansible_collections"
                / namespace
                / collection
                / "roles"
                / role_dir
            )
        else:
            path = mock_root / "roles" / role_name
        # Avoid error from makedirs if destination is a broken symlink
        if path.is_symlink() and not path.exists():  # pragma: no cover
            _logger.warning("Removed broken symlink from %s", path)
            path.unlink(missing_ok=True)
        path.mkdir(exist_ok=True, parents=True)

    if options.mock_modules:
        for module_name in options.mock_modules:
            _make_module_stub(module_name=module_name, options=options)

    _warn_if_mock_clobbered_real_collections(options)


def _perform_mockings_cleanup(options: Options) -> None:
    """Clean up mocked modules and roles."""
    mock_root = options.mock_root
    mock_collections_path = options.mock_collections_path
    mock_modules_path = options.mock_modules_path
    if not mock_root or not mock_collections_path or not mock_modules_path:
        msg = "Cache directory not set"
        raise RuntimeError(msg)

    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+$", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = (
                mock_collections_path
                / "ansible_collections"
                / namespace
                / collection
                / "roles"
                / role_dir
            )
        else:
            path = mock_root / "roles" / role_name
        with contextlib.suppress(OSError):
            path.rmdir()

    for module_name in options.mock_modules:
        parts = module_name.split(".")
        if len(parts) < 3:
            module_file = mock_modules_path / f"{module_name}.py"
        else:
            relpath = _collection_module_relpath(module_name)
            if relpath is None:  # pragma: no cover
                continue
            module_file = mock_collections_path / relpath
        if is_lint_mock_module(module_file):
            with contextlib.suppress(OSError):
                module_file.unlink()
