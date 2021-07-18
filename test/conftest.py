import os
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def cwd(path: str) -> Iterator[None]:
    """Context manager for chdir."""
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)
