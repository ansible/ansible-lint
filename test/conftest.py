"""PyTest fixtures for testing the project."""
import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator, Iterator

import pytest
from _pytest.fixtures import FixtureRequest
from filelock import FileLock

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


def pytest_addoption(parser: "Parser") -> None:
    """Add --regenerate-formatting-fixtures option to pytest."""
    parser.addoption(
        "--regenerate-formatting-fixtures",
        action="store_true",
        default=False,
        help="Regenerate formatting fixtures with prettier and internal formatter",
    )


def pytest_collection_modifyitems(items: "List[nodes.Item]", config: "Config") -> None:
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


@pytest.fixture(autouse=True)
def _block_on_serial_mark(request: FixtureRequest) -> Generator[None, None, None]:
    """Ensure that tests with serial marker do not run at the same time."""
    # https://github.com/pytest-dev/pytest-xdist/issues/84
    # https://github.com/pytest-dev/pytest-xdist/issues/385
    os.makedirs(".tox", exist_ok=True)
    if request.node.get_closest_marker("serial"):
        # pylint: disable=abstract-class-instantiated
        with FileLock(".tox/semaphore.lock"):
            yield
    else:
        yield
