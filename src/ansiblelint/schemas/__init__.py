"""Module containing cached JSON schemas."""
import logging
import os
import urllib.request

from ansiblelint.config import JSON_SCHEMAS

_logger = logging.getLogger(__package__)


def refresh_schemas() -> int:
    """Refresh JSON schemas by downloading latest versions.

    Returns number of changed schemas.
    """
    changed = 0
    for kind, url in sorted(JSON_SCHEMAS.items()):
        if url.startswith("https://raw.githubusercontent.com/ansible/ansible-lint"):
            _logger.warning(
                "Skipped updating schema that is part of the ansible-lint repository: %s",
                url,
            )
            continue
        path = f"{os.path.relpath(os.path.dirname(__file__))}/{kind}.json"
        print(f"Refreshing {path} ...")
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
            with open(f"{path}", "r+", encoding="utf-8") as f_out:
                if f_out.read() != content:
                    f_out.seek(0)
                    f_out.write(content)
                    f_out.truncate()
                    changed += 1
    return changed
