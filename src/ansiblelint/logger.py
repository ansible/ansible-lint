"""Utils related to logging."""
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

_logger = logging.getLogger(__name__)


@contextmanager
def timed_info(msg: Any, *args: Any) -> Iterator[None]:
    """Context manager for logging slow operations, mentions duration."""
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        _logger.info(msg + " (%.2fs)", *(*args, elapsed))


def warn_or_fail(message: str) -> None:
    """Warn or fail depending on the strictness level."""
    # pylint: disable=import-outside-toplevel
    from ansiblelint.config import options
    from ansiblelint.errors import StrictModeError

    if options.strict:
        raise StrictModeError(message)

    _logger.warning(message)
