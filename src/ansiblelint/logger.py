"""Utils related to logging."""
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rich.logging import RichHandler
from rich.text import Text

_logger = logging.getLogger(__name__)


class RichHandlerEx(RichHandler):
    """Rich logging handler."""

    def get_level_text(self, record: logging.LogRecord) -> Text:
        """Get the level name from the record.

        Args:
            record (LogRecord): LogRecord instance.

        Returns:
            Text: A tuple of the style and level name.
        """
        level_name = record.levelname
        level_text = Text.styled(
            f"{level_name[0]}:", f"logging.level.{level_name.lower()}"
        )
        return level_text


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
