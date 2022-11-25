"""Module containing cached JSON schemas."""
import json
import logging
import os
import sys
import time
import urllib.request
from pathlib import Path
from urllib.request import Request

_logger = logging.getLogger(__package__)


# Maps kinds to JSON schemas
# See https://www.schemastore.org/json/
store_file = Path(f"{__file__}/../__store__.json").resolve()
with open(store_file, encoding="utf-8") as json_file:
    JSON_SCHEMAS = json.load(json_file)


# pylint: disable=too-many-branches
def refresh_schemas(min_age_seconds: int = 3600 * 24) -> int:
    """Refresh JSON schemas by downloading latest versions.

    Returns number of changed schemas.
    """
    age = int(time.time() - store_file.stat().st_mtime)

    # never check for updated schemas more than once a day
    if min_age_seconds > age:
        return 0
    if not os.access(store_file, os.W_OK):
        _logger.debug(
            "Skipping schema update due to lack of writing rights on %s", store_file
        )
        return -1
    _logger.debug("Checking for updated schemas...")

    changed = 0
    # breakpoint()
    for kind, data in JSON_SCHEMAS.items():
        url = data["url"]
        if "#" in url:
            raise RuntimeError(
                f"Schema URLs cannot contain # due to python-jsonschema limitation: {url}"
            )
        if url.startswith("https://raw.githubusercontent.com/ansible/ansible-lint"):
            _logger.debug(
                "Skipped updating schema that is part of the ansible-lint repository: %s",
                url,
            )
            continue
        path = Path(f"{os.path.relpath(os.path.dirname(__file__))}/{kind}.json")
        _logger.debug("Refreshing %s schema ...", kind)
        request = Request(url)
        etag = data.get("etag", "")
        if etag:
            request.add_header("If-None-Match", f'"{data.get("etag")}"')
        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    content = response.read().decode("utf-8")
                    etag = response.headers["etag"].strip('"')
                    if etag != data.get("etag", ""):
                        JSON_SCHEMAS[kind]["etag"] = etag
                        changed += 1
                    with open(f"{path}", "w", encoding="utf-8") as f_out:
                        _logger.info("Schema %s was updated", kind)
                        f_out.write(content)
                        f_out.truncate()
                        os.fsync(f_out.fileno())
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                _logger.debug("Schema %s is not modified", url)
                continue
            _logger.warning(
                "Skipped schema refresh due to unexpected exception: %s", exc
            )
            return 0
    if changed:
        with open(store_file, "w", encoding="utf-8") as f_out:
            json.dump(JSON_SCHEMAS, f_out, indent=4, sort_keys=True)
    else:
        store_file.touch()
        changed = 1
    return changed


if __name__ == "__main__":

    if refresh_schemas():
        print("Schemas were updated.")
        sys.exit(1)
    else:
        print("Schemas not updated", 0)
