"""PyTest fixtures for testing the project."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# pylint: disable=wildcard-import,unused-wildcard-import
from ansiblelint.testing.fixtures import *  # noqa: F403
from ansiblelint.yaml_utils import FormattedYAML

if TYPE_CHECKING:
    from _pytest import nodes
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser) -> None:
    """Add --regenerate-formatting-fixtures option to pytest."""
    parser.addoption(
        "--regenerate-formatting-fixtures",
        action="store_true",
        default=False,
        help="Regenerate formatting fixtures with prettier and internal formatter",
    )


def pytest_collection_modifyitems(items: list[nodes.Item], config: Config) -> None:
    """Skip tests based on --regenerate-formatting-fixtures option."""
    do_regenerate = config.getoption("--regenerate-formatting-fixtures")
    skip_other = pytest.mark.skip(
        reason="not a formatting_fixture test and "
        "--regenerate-formatting-fixtures was specified",
    )
    skip_formatting_fixture = pytest.mark.skip(
        reason="specify --regenerate-formatting-fixtures to "
        "only run formatting_fixtures test",
    )
    for item in items:
        if do_regenerate and "formatting_fixtures" not in item.keywords:
            item.add_marker(skip_other)
        elif not do_regenerate and "formatting_fixtures" in item.keywords:
            item.add_marker(skip_formatting_fixture)


def pytest_configure(config: Config) -> None:
    """Register custom markers."""
    if config.getoption("--regenerate-formatting-fixtures"):
        regenerate_formatting_fixtures()


def regenerate_formatting_fixtures() -> None:
    """Re-generate formatting fixtures with prettier and internal formatter.

    Pass ``--regenerate-formatting-fixtures`` to run this and skip all other tests.
    This is a "test" because once fixtures are regenerated,
    we run prettier again to make sure it does not change files formatted
    with our internal formatting code.
    """
    subprocess.check_call(["which", "prettier"])

    yaml = FormattedYAML()

    fixtures_dir = Path("test/fixtures/")
    fixtures_dir_before = fixtures_dir / "formatting-before"
    fixtures_dir_prettier = fixtures_dir / "formatting-prettier"
    fixtures_dir_after = fixtures_dir / "formatting-after"

    fixtures_dir_prettier.mkdir(exist_ok=True)
    fixtures_dir_after.mkdir(exist_ok=True)

    # Copying before fixtures...
    for fixture in fixtures_dir_before.glob("fmt-[0-9].yml"):
        shutil.copy(str(fixture), str(fixtures_dir_prettier / fixture.name))
        shutil.copy(str(fixture), str(fixtures_dir_after / fixture.name))

    # Writing fixtures with prettier...
    subprocess.check_call(["prettier", "-w", str(fixtures_dir_prettier)])
    # NB: pre-commit end-of-file-fixer can also modify files.

    # Writing fixtures with ansiblelint.yaml_utils.FormattedYAML()
    for fixture in fixtures_dir_after.glob("fmt-[0-9].yml"):
        data = yaml.load(fixture.read_text())
        output = yaml.dumps(data)
        fixture.write_text(output)

    # Make sure prettier won't make changes in {fixtures_dir_after}
    subprocess.check_call(["prettier", "-c", str(fixtures_dir_after)])
