"""Test schemas modules."""
import json
import logging
import os
import subprocess
import sys
import urllib
from time import sleep
from typing import Any
from unittest.mock import DEFAULT, MagicMock, patch

import pytest
from spdx.config import __file__ as spdx_config_path

from ansiblelint.file_utils import Lintable
from ansiblelint.schemas import __file__ as schema_path
from ansiblelint.schemas import refresh_schemas, validate_file_schema


def test_refresh_schemas() -> None:
    """Test for schema update skip."""
    # This is written as a single test in order to avoid concurrency issues,
    # which caused random issues on CI when the two tests run in parallel
    # and or in different order.
    assert refresh_schemas(min_age_seconds=3600 * 24 * 365 * 10) == 0
    sleep(1)
    # this should disable the cache and force an update
    assert refresh_schemas(min_age_seconds=0) == 1
    sleep(1)
    # should be cached now
    assert refresh_schemas(min_age_seconds=10) == 0


def urlopen_side_effect(*_args: Any, **kwargs: Any) -> DEFAULT:
    """Actual test that timeout parameter is defined."""
    assert "timeout" in kwargs
    assert kwargs["timeout"] > 0
    return DEFAULT


@patch("urllib.request")
def test_requests_uses_timeout(mock_request: MagicMock) -> None:
    """Test that schema refresh uses timeout."""
    mock_request.urlopen.side_effect = urlopen_side_effect
    refresh_schemas(min_age_seconds=0)
    mock_request.urlopen.assert_called()


@patch("urllib.request")
def test_request_timeouterror_handling(
    mock_request: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that schema refresh can handle time out errors."""
    error_msg = "Simulating handshake operation time out."
    mock_request.urlopen.side_effect = urllib.error.URLError(TimeoutError(error_msg))
    with caplog.at_level(logging.DEBUG):
        assert refresh_schemas(min_age_seconds=0) == 1
    mock_request.urlopen.assert_called()
    assert "Skipped schema refresh due to unexpected exception: " in caplog.text
    assert error_msg in caplog.text


def test_schema_refresh_cli() -> None:
    """Ensure that we test the cli schema refresh command."""
    proc = subprocess.run(
        [sys.executable, "-m", "ansiblelint.schemas"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0


def test_validate_file_schema() -> None:
    """Test file schema validation failure on unknown file kind."""
    lintable = Lintable("foo.bar", kind="")
    result = validate_file_schema(lintable)
    assert len(result) == 1, result
    assert "Unable to find JSON Schema" in result[0]


def test_spdx() -> None:
    """Test that SPDX license identifiers are in sync."""
    _base_dir = os.path.dirname(spdx_config_path)
    _licenses = os.path.join(_base_dir, "licenses.json")

    license_ids = set()
    with open(_licenses, encoding="utf-8") as license_fh:
        licenses = json.load(license_fh)
    for lic in licenses["licenses"]:
        if lic.get("isDeprecatedLicenseId"):
            continue
        license_ids.add(lic["licenseId"])

    with open(
        os.path.join(os.path.dirname(schema_path), "galaxy.json"), encoding="utf-8"
    ) as f:
        schema = json.load(f)
        spx_enum = schema["$defs"]["SPDXLicenseEnum"]["enum"]
    if set(spx_enum) != license_ids:
        with open(
            os.path.join(os.path.dirname(schema_path), "galaxy.json"),
            "w",
            encoding="utf-8",
        ) as f:
            schema["$defs"]["SPDXLicenseEnum"]["enum"] = sorted(license_ids)
            json.dump(schema, f, indent=2)
        pytest.fail(
            "SPDX license list inside galaxy.json JSON Schema file was updated."
        )
