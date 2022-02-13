import os
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def cwd(path: str) -> Iterator[None]:
    """Context manager for chdir."""
    old_pwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_pwd)
