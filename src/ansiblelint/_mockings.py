"""Utilities for mocking ansible modules and roles."""

from __future__ import annotations

import contextlib
import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

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
    """Remove legacy mock stubs still sitting under real collections."""
    if not options.cache_dir or not options.mock_modules:
        return
    real_collections = options.cache_dir / "collections"
    for module_name in options.mock_modules:
        relpath = _collection_module_relpath(module_name)
        if relpath is None:
            continue
        candidate = real_collections / relpath
        if is_lint_mock_module(candidate):
            with contextlib.suppress(OSError):
                candidate.unlink()
            _logger.warning(
                "Removed legacy ansible-lint mock stub at %s under the real "
                "collections path so installed modules can resolve correctly. "
                "If problems persist, reinstall affected collections "
                "(ansible-galaxy collection install ... --force).",
                candidate,
            )


def _safe_path_under_root(root: Path, *parts: str) -> Path | None:
    """Join path parts under root, or return None if they would escape root."""
    if any(part in ("", ".", "..") or "/" in part or "\\" in part for part in parts):
        return None
    candidate = root.joinpath(*parts)
    # Resolve only after join so we detect .. via Path semantics if present.
    if not candidate.resolve().is_relative_to(root.resolve()):
        return None
    return candidate


def _is_valid_module_name(module_name: str) -> bool:
    """Return True if module_name matches the allowed mock_modules patterns."""
    return bool(re.match(r"^(\w+|\w+\.\w+\.[\.\w]+)$", module_name))


def _is_valid_role_name(role_name: str) -> bool:
    """Return True if role_name matches the allowed mock_roles patterns."""
    if re.match(r"^\w+\.\w+\.\w+$", role_name):
        return True
    return bool(re.match(r"^[\w][\w.-]*$", role_name) and ".." not in role_name)


def _mock_role_path(role_name: str, mock_root: Path) -> Path | None:
    """Return the filesystem path for a mocked role, or None if invalid/unsafe."""
    if not _is_valid_role_name(role_name):
        return None
    if re.match(r"^\w+\.\w+\.\w+$", role_name):
        namespace, collection, role_dir = role_name.split(".")
        # Always anchor on mock_root so a symlinked collections/ cannot escape.
        return _safe_path_under_root(
            mock_root,
            "collections",
            "ansible_collections",
            namespace,
            collection,
            "roles",
            role_dir,
        )
    return _safe_path_under_root(mock_root, "roles", role_name)


def _mock_module_path(module_name: str, mock_root: Path) -> Path | None:
    """Return the filesystem path for a mocked module, or None if invalid/unsafe."""
    if not _is_valid_module_name(module_name):
        return None
    parts = module_name.split(".")
    if len(parts) < 3:
        return _safe_path_under_root(mock_root, "modules", f"{module_name}.py")
    relpath = _collection_module_relpath(module_name)
    if relpath is None:  # pragma: no cover
        return None
    # Always anchor on mock_root so a symlinked collections/ cannot escape.
    return _safe_path_under_root(mock_root, "collections", *relpath.parts)


def _exit_invalid_mock_name(kind: str, name: str, mock_root: Path) -> NoReturn:
    """Exit with a specific error for invalid names vs unsafe mock paths."""
    validator = _is_valid_module_name if kind == "module" else _is_valid_role_name
    if not validator(name):
        _logger.error("Config error: %s is not a valid %s name.", name, kind)
    else:
        _logger.error(
            "Config error: refused unsafe mock %s path for %s outside %s.",
            kind,
            name,
            mock_root,
        )
    sys.exit(RC.INVALID_CONFIG)


def _make_module_stub(module_name: str, options: Options) -> None:
    mock_root = options.mock_root
    if not mock_root:
        msg = "Cache directory not set"
        raise RuntimeError(msg)
    module_file = _mock_module_path(module_name, mock_root)
    if module_file is None:
        _exit_invalid_mock_name("module", module_name, mock_root)

    parts = module_name.split(".")
    if len(parts) < 3:
        namespace = None
        collection = None
    else:
        namespace = parts[0]
        collection = parts[1]

    module_file.parent.mkdir(exist_ok=True, parents=True)
    _write_module_stub(
        filename=module_file,
        name=module_name,
        namespace=namespace,
        collection=collection,
    )


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
    if not mock_root:  # pragma: no cover
        msg = "Cache directory not set"
        raise RuntimeError(msg)
    for role_name in options.mock_roles:
        path = _mock_role_path(role_name, mock_root)
        if path is None:
            _exit_invalid_mock_name("role", role_name, mock_root)
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
    if not mock_root:
        msg = "Cache directory not set"
        raise RuntimeError(msg)

    for role_name in options.mock_roles:
        path = _mock_role_path(role_name, mock_root)
        if path is None:
            continue
        with contextlib.suppress(OSError):
            path.rmdir()

    for module_name in options.mock_modules:
        module_file = _mock_module_path(module_name, mock_root)
        if module_file is not None and is_lint_mock_module(module_file):
            with contextlib.suppress(OSError):
                module_file.unlink()
