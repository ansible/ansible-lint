"""Module containing cached JSON schemas."""
import json
import logging
import os
import sys
import time
import urllib.request
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.request import Request

_logger = logging.getLogger(__package__)

# Maps kinds to JSON schemas
# See https://www.schemastore.org/json/
store_file = Path(f"{__file__}/../__store__.json").resolve()
with open(store_file, encoding="utf-8") as json_file:
    JSON_SCHEMAS = json.load(json_file)


class SchemaCacheDict(defaultdict):  # type: ignore
    """Caching schema store."""

    def __missing__(self, key: str) -> Any:
        """Load schema on its first use."""
        value = get_schema(key)
        self[key] = value
        return value


@lru_cache(maxsize=None)
def get_schema(kind: str) -> Any:
    """Return the schema for the given kind."""
    schema_file = os.path.dirname(__file__) + "/" + kind + ".json"
    with open(schema_file, encoding="utf-8") as f:
        return json.load(f)


_schema_cache = SchemaCacheDict()


# pylint: disable=too-many-branches
def refresh_schemas(min_age_seconds: int = 3600 * 24) -> int:
    """Refresh JSON schemas by downloading latest versions.

    Returns number of changed schemas.
    """
    age = int(time.time() - store_file.stat().st_mtime)

    # never check for updated schemas more than once a day
    if min_age_seconds > age:
        return 0
    if not os.access(store_file, os.W_OK):  # pragma: no cover
        _logger.debug(
            "Skipping schema update due to lack of writing rights on %s", store_file
        )
        return -1
    _logger.debug("Checking for updated schemas...")

    changed = 0
    for kind, data in JSON_SCHEMAS.items():
        url = data["url"]
        if "#" in url:
            raise RuntimeError(
                f"Schema URLs cannot contain # due to python-jsonschema limitation: {url}"
            )
        path = Path(f"{os.path.relpath(os.path.dirname(__file__))}/{kind}.json")
        _logger.debug("Refreshing %s schema ...", kind)
        request = Request(url)
        etag = data.get("etag", "")
        if etag:
            request.add_header("If-None-Match", f'"{data.get("etag")}"')
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    content = response.read().decode("utf-8").rstrip()
                    etag = response.headers["etag"].strip('"')
                    if etag != data.get("etag", ""):
                        JSON_SCHEMAS[kind]["etag"] = etag
                        changed += 1
                    with open(f"{path}", "w", encoding="utf-8") as f_out:
                        _logger.info("Schema %s was updated", kind)
                        f_out.write(content)
                        f_out.write("\n")  # prettier/editors
                        f_out.truncate()
                        os.fsync(f_out.fileno())
                        # unload possibly loaded schema
                        if kind in _schema_cache:  # pragma: no cover
                            del _schema_cache[kind]
        except (ConnectionError, OSError) as exc:
            if (
                isinstance(exc, urllib.error.HTTPError)
                and getattr(exc, "code", None) == 304
            ):
                _logger.debug("Schema %s is not modified", url)
                continue
            # In case of networking issues, we just stop and use last-known good
            _logger.debug("Skipped schema refresh due to unexpected exception: %s", exc)
            break
    if changed:  # pragma: no cover
        with open(store_file, "w", encoding="utf-8") as f_out:
            # formatting should match our .prettierrc.yaml
            json.dump(JSON_SCHEMAS, f_out, indent=2, sort_keys=True)
            f_out.write("\n")  # prettier and editors in general
        # clear schema cache
        get_schema.cache_clear()
    else:
        store_file.touch()
        changed = 1
    return changed


if __name__ == "__main__":
    if refresh_schemas(60 * 10):  # pragma: no cover
        # flake8: noqa: T201
        print("Schemas were updated.")
        sys.exit(1)
    else:  # pragma: no cover
        # flake8: noqa: T201
        print("Schemas not updated", 0)
