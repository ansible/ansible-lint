"""Test that re-generates formatting fixtures."""
import shutil
import subprocess
from pathlib import Path

import pytest

from ansiblelint.yaml_utils import FormattedYAML


@pytest.mark.formatting_fixtures()
def test_regenerate_formatting_fixtures() -> None:
    """Re-generate formatting fixtures with prettier and internal formatter.

    Pass ``--regenerate-formatting-fixtures`` to run this and skip all other tests.
    This is a "test" because once fixtures are regenerated,
    we run prettier again to make sure it does not change files formatted
    with our internal formatting code.
    """
    print("Looking for prettier on PATH...")
    subprocess.check_call(["which", "prettier"])

    yaml = FormattedYAML()

    fixtures_dir = Path("test/fixtures/")
    fixtures_dir_before = fixtures_dir / "formatting-before"
    fixtures_dir_prettier = fixtures_dir / "formatting-prettier"
    fixtures_dir_after = fixtures_dir / "formatting-after"

    fixtures_dir_prettier.mkdir(exist_ok=True)
    fixtures_dir_after.mkdir(exist_ok=True)

    print("\nCopying before fixtures...")
    for fixture in fixtures_dir_before.glob("fmt-[0-9].yml"):
        shutil.copy(str(fixture), str(fixtures_dir_prettier / fixture.name))
        shutil.copy(str(fixture), str(fixtures_dir_after / fixture.name))

    print("\nWriting fixtures with prettier...")
    subprocess.check_call(["prettier", "-w", str(fixtures_dir_prettier)])
    # NB: pre-commit end-of-file-fixer can also modify files.

    print("\nWriting fixtures with ansiblelint.yaml_utils.FormattedYAML()...")
    for fixture in fixtures_dir_after.glob("fmt-[0-9].yml"):
        data = yaml.loads(fixture.read_text())
        output = yaml.dumps(data)
        print(fixture)
        fixture.write_text(output)

    print(f"\nMake sure prettier won't make changes in {fixtures_dir_after}...")
    subprocess.check_call(["prettier", "-c", str(fixtures_dir_after)])
