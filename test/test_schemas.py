"""Test schemas modules."""

import json
import logging
import os
import re
import subprocess
import sys
import urllib
from pathlib import Path
from typing import Any
from unittest.mock import DEFAULT, MagicMock, patch

import license_expression
import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.schemas import __file__ as schema_module
from ansiblelint.schemas.__main__ import refresh_schemas
from ansiblelint.schemas.main import validate_file_schema

schema_path = Path(schema_module).parent
spdx_config_path = (
    Path(license_expression.__file__).parent / "data" / "scancode-licensedb-index.json"
)
RE_SPDX_SAFE_TOX_ENV_NAME = re.compile(r"^py[\d\.]*$")


def urlopen_side_effect(*_args: Any, **kwargs: Any) -> Any:
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
    mock_request: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that schema refresh can handle time out errors."""
    error_msg = "Simulating handshake operation time out."
    mock_request.urlopen.side_effect = urllib.error.URLError(  # pyright: ignore[reportAttributeAccessIssue]
        TimeoutError(error_msg)
    )
    with caplog.at_level(logging.DEBUG):
        assert refresh_schemas(min_age_seconds=0) == 0
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
    assert proc.returncode == 0, proc


def test_validate_file_schema() -> None:
    """Test file schema validation failure on unknown file kind."""
    lintable = Lintable("foo.bar", kind="")
    result = validate_file_schema(lintable)
    assert len(result) == 1, result
    assert "Unable to find JSON Schema" in result[0]


@pytest.mark.skipif(
    not RE_SPDX_SAFE_TOX_ENV_NAME.match(os.environ.get("TOX_ENV_NAME", "")),
    reason="Skipping SPDX license test due to constraints not being used by current job.",
)
def test_spdx() -> None:
    """Test that SPDX license identifiers are in sync."""
    license_ids = set()
    with spdx_config_path.open(encoding="utf-8") as license_fh:
        licenses = json.load(license_fh)
    for lic in licenses:
        if lic.get("is_deprecated"):
            continue
        lic_id = lic["spdx_license_key"]
        if lic_id.startswith("LicenseRef"):
            continue
        license_ids.add(lic_id)

    galaxy_json = schema_path / "galaxy.json"
    with galaxy_json.open(encoding="utf-8") as f:
        schema = json.load(f)
        spx_enum = schema["$defs"]["SPDXLicenseEnum"]["enum"]
    if set(spx_enum) != license_ids:
        pytest.fail(
            "SPDX license list inside galaxy.json JSON Schema file was updated.",
        )
