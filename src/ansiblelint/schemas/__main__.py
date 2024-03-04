"""Module containing cached JSON schemas."""

import json
import logging
import os
import sys
import time
import urllib.request
from collections import defaultdict
from functools import cache
from http.client import HTTPException
from pathlib import Path
from typing import Any
from urllib.request import Request

_logger = logging.getLogger(__package__)

# Maps kinds to JSON schemas
# See https://www.schemastore.org/json/
store_file = Path(f"{__file__}/../__store__.json").resolve()
with store_file.open(encoding="utf-8") as json_file:
    JSON_SCHEMAS = json.load(json_file)


class SchemaCacheDict(defaultdict):  # type: ignore[type-arg]
    """Caching schema store."""

    def __missing__(self, key: str) -> Any:
        """Load schema on its first use."""
        value = get_schema(key)
        self[key] = value
        return value


@cache
def get_schema(kind: str) -> Any:
    """Return the schema for the given kind."""
    schema_file = Path(__file__).parent / f"{kind}.json"
    with schema_file.open(encoding="utf-8") as f:
        return json.load(f)


_schema_cache = SchemaCacheDict()


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
            "Skipping schema update due to lack of writing rights on %s",
            store_file,
        )
        return -1
    _logger.debug("Checking for updated schemas...")

    changed = 0
    for kind, data in JSON_SCHEMAS.items():
        url = data["url"]
        if "#" in url:
            msg = f"Schema URLs cannot contain # due to python-jsonschema limitation: {url}"
            raise RuntimeError(msg)
        path = Path(__file__).parent.resolve() / f"{kind}.json"
        _logger.debug("Refreshing %s schema ...", kind)
        if not url.startswith(("http:", "https:")):
            msg = f"Unexpected url schema: {url}"
            raise ValueError(msg)
        request = Request(url)  # noqa: S310
        etag = data.get("etag", "")
        if etag:
            request.add_header("If-None-Match", f'"{data.get("etag")}"')
        try:
            with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
                if response.status == 200:
                    content = response.read().decode("utf-8").rstrip()
                    etag = response.headers["etag"].strip('"')
                    if etag != data.get("etag", ""):
                        JSON_SCHEMAS[kind]["etag"] = etag
                        changed += 1
                    with path.open("w", encoding="utf-8") as f_out:
                        _logger.info("Schema %s was updated", kind)
                        f_out.write(content)
                        f_out.write("\n")  # prettier/editors
                        f_out.truncate()
                        os.fsync(f_out.fileno())
                        # unload possibly loaded schema
                        if kind in _schema_cache:  # pragma: no cover
                            del _schema_cache[kind]
        except (ConnectionError, OSError, HTTPException) as exc:
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
        with store_file.open("w", encoding="utf-8") as f_out:
            # formatting should match our .prettierrc.yaml
            json.dump(JSON_SCHEMAS, f_out, indent=2, sort_keys=True)
            f_out.write("\n")  # prettier and editors in general
        # clear schema cache
        get_schema.cache_clear()
    else:
        store_file.touch()
    return changed


if __name__ == "__main__":
    if refresh_schemas(60 * 10):  # pragma: no cover
        print("Schemas were updated.")  # noqa: T201
        sys.exit(1)
    else:  # pragma: no cover
        print("Schemas not updated", 0)  # noqa: T201
