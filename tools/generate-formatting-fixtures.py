"""Script to re-generate formatting fixtures."""
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    """Re-generate formatting fixtures with prettier and internal formatter."""
    print("Looking for prettier on PATH...")
    subprocess.check_call(["which", "prettier"])

    fixtures_dir = Path("test/fixtures/")
    fixtures_dir_before = fixtures_dir / "formatting-before"
    fixtures_dir_prettier = fixtures_dir / "formatting-prettier"
    fixtures_dir_ruamel_yaml = fixtures_dir / "formatting-ruamel-yaml"

    fixtures_dir_prettier.mkdir(exist_ok=True)
    fixtures_dir_ruamel_yaml.mkdir(exist_ok=True)

    print("\nCopying before fixtures...")
    for fixture in fixtures_dir_before.glob("fmt-[0-9].yml"):
        shutil.copy(str(fixture), str(fixtures_dir_prettier / fixture.name))
        shutil.copy(str(fixture), str(fixtures_dir_ruamel_yaml / fixture.name))

    print("\nWriting fixtures with prettier...")
    subprocess.check_call(["prettier", "-w", str(fixtures_dir_prettier)])
    # NB: pre-commit end-of-file-fixer can also modify files.

    # prepare ruamel.yaml fixtures (diff in next PR will show how it compares).
    subprocess.check_call(["prettier", "-w", str(fixtures_dir_ruamel_yaml)])


if __name__ == "__main__":
    main()
