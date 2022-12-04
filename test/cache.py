"""Cache test fixture such collections and roles."""
import json
import logging
import os
import sys
import time
import urllib.request
from pathlib import Path
from urllib.request import Request
import pytest

_logger = logging.getLogger(__package__)


# Maps kinds to JSON schemas
# See https://www.schemastore.org/json/
store_file = Path(f"{__file__}/../cache.json").resolve()
with open(store_file, encoding="utf-8") as json_file:
    FILE_CACHE = json.load(json_file)


# pylint: disable=too-many-branches
def refresh_cache(min_age_seconds: int = 3600 * 24) -> int:
    """Refresh cache by downloading latest versions.

    Returns number of changed schemas.
    """
    cache = Path(
        os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        + "/ansible-lint/web/"
    )
    cache.mkdir(exist_ok=True)

    age = int(time.time() - store_file.stat().st_mtime)

    # never check for updated schemas more than once a day
    # if min_age_seconds > age:
    #     breakpoint()
    #     return 0
    _logger.debug("Checking for updated files...")

    changed = 0
    # breakpoint()
    for filename, data in FILE_CACHE.items():
        url = data["url"]
        if "#" in url:
            raise RuntimeError(f"File URLs cannot contain #: {url}")
        path = cache / filename
        _logger.debug("Refreshing %s file ...", filename)
        request = Request(url)
        etag = ""
        if path.is_file():
            etag = data.get("etag", "")
        if etag:
            request.add_header("If-None-Match", f'"{data.get("etag")}"')
        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    content = response.read()
                    etag = response.headers["etag"].strip('"')
                    if etag != data.get("etag", ""):
                        FILE_CACHE[filename]["etag"] = etag
                        changed += 1
                    with open(f"{path}", "wb") as f_out:
                        _logger.info("File %s was updated", filename)
                        f_out.write(content)
                        f_out.truncate()
                        os.fsync(f_out.fileno())
                        changed = 1
                        # breakpoint()
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                _logger.debug("File %s is not modified", url)
                continue
            if not path.is_file():
                _logger.fatal("Failed to download test fixture into cache: %s", exc)
                pytest.exit("x", 101)
            changed = 0
    if changed:
        with open(store_file, "w", encoding="utf-8") as f_out:
            json.dump(FILE_CACHE, f_out, indent=4, sort_keys=True)
    else:
        store_file.touch()
        changed = 1

    return changed


if __name__ == "__main__":

    if refresh_cache():
        print("File cache was updated.")
        sys.exit(1)
    else:
        print("File cache update skipped.", 0)
