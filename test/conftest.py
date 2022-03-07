import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

import pytest

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
