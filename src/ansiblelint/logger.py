"""Utils related to logging."""
import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

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
