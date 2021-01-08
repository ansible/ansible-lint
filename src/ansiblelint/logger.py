"""Utils related to logging."""
import logging
import time
from contextlib import contextmanager
from typing import Any

_logger = logging.getLogger(__package__)


@contextmanager
def timed_info(msg: Any, *args: Any):
    """Context manager for logging slow operations, mentions duration."""
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        _logger.info(msg + " [repr.number]%.2fs[/repr.number]", *(*args, elapsed))
