"""PyTest fixtures for testing the project."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

import pytest

# pylint: disable=wildcard-import,unused-wildcard-import
from ansiblelint.testing.fixtures import *  # noqa: F403

if TYPE_CHECKING:
    from typing import List  # pylint: disable=ungrouped-imports

    from _pytest import nodes
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser


@contextmanager
def cwd(path: str) -> Iterator[None]:
    """Context manager for chdir."""
    old_pwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_pwd)


def pytest_addoption(parser: Parser) -> None:
    """Add --regenerate-formatting-fixtures option to pytest."""
    parser.addoption(
        "--regenerate-formatting-fixtures",
        action="store_true",
        default=False,
        help="Regenerate formatting fixtures with prettier and internal formatter",
    )


def pytest_collection_modifyitems(items: list[nodes.Item], config: Config) -> None:
    """Skip tests based on --regenerate-formatting-fixtures option."""
    do_regenerate = config.getoption("--regenerate-formatting-fixtures")
    skip_other = pytest.mark.skip(
        reason="not a formatting_fixture test and "
        "--regenerate-formatting-fixtures was specified"
    )
    skip_formatting_fixture = pytest.mark.skip(
        reason="specify --regenerate-formatting-fixtures to "
        "only run formatting_fixtures test"
    )
    for item in items:
        if do_regenerate and "formatting_fixtures" not in item.keywords:
            item.add_marker(skip_other)
        elif not do_regenerate and "formatting_fixtures" in item.keywords:
            item.add_marker(skip_formatting_fixture)
