import os
from pathlib import Path
from typing import List

import pytest
from _pytest.monkeypatch import MonkeyPatch

from ansiblelint import cli


@pytest.fixture
def base_arguments() -> List[str]:
    """Define reusable base arguments for tests in current module."""
    return ['../test/skiptasks.yml']


@pytest.mark.parametrize(
    ('args', 'config'),
    (
        (["-p"], "test/fixtures/parseable.yml"),
        (["-q"], "test/fixtures/quiet.yml"),
        (["-r", "test/fixtures/rules/"], "test/fixtures/rulesdir.yml"),
        (["-R", "-r", "test/fixtures/rules/"], "test/fixtures/rulesdir-defaults.yml"),
        (["-t", "skip_ansible_lint"], "test/fixtures/tags.yml"),
        (["-v"], "test/fixtures/verbosity.yml"),
        (["-x", "bad_tag"], "test/fixtures/skip-tags.yml"),
        (["--exclude", "test/"], "test/fixtures/exclude-paths.yml"),
        (["--show-relpath"], "test/fixtures/show-abspath.yml"),
        ([], "test/fixtures/show-relpath.yml"),
    ),
)
def test_ensure_config_are_equal(
    base_arguments: List[str], args: List[str], config: str
) -> None:
    """Check equality of the CLI options to config files."""
    command = base_arguments + args
    cli_parser = cli.get_cli_parser()

    options = cli_parser.parse_args(command)
    file_config = cli.load_config(config)

    for key, val in file_config.items():

        # config_file does not make sense in file_config
        if key == 'config_file':
            continue

        if key in {'exclude_paths', 'rulesdir'}:
            val = [Path(p) for p in val]
        assert val == getattr(options, key)


def test_config_can_be_overridden(base_arguments: List[str]) -> None:
    """Check that config can be overridden from CLI."""
    no_override = cli.get_config(base_arguments + ["-t", "bad_tag"])

    overridden = cli.get_config(
        base_arguments + ["-t", "bad_tag", "-c", "test/fixtures/tags.yml"]
    )

    assert no_override.tags + ["skip_ansible_lint"] == overridden.tags


def test_different_config_file(base_arguments: List[str]) -> None:
    """Ensures an alternate config_file can be used."""
    diff_config = cli.get_config(
        base_arguments + ["-c", "test/fixtures/ansible-config.yml"]
    )
    no_config = cli.get_config(base_arguments + ["-v"])

    assert diff_config.verbosity == no_config.verbosity


def test_expand_path_user_and_vars_config_file(base_arguments: List[str]) -> None:
    """Ensure user and vars are expanded when specified as exclude_paths."""
    config1 = cli.get_config(
        base_arguments + ["-c", "test/fixtures/exclude-paths-with-expands.yml"]
    )
    config2 = cli.get_config(
        base_arguments
        + ["--exclude", "~/.ansible/roles", "--exclude", "$HOME/.ansible/roles"]
    )

    assert str(config1.exclude_paths[0]) == os.path.expanduser("~/.ansible/roles")
    assert str(config2.exclude_paths[0]) == os.path.expanduser("~/.ansible/roles")
    assert str(config1.exclude_paths[1]) == os.path.expandvars("$HOME/.ansible/roles")
    assert str(config2.exclude_paths[1]) == os.path.expandvars("$HOME/.ansible/roles")


def test_path_from_config_do_not_depend_on_cwd(
    monkeypatch: MonkeyPatch,
) -> None:  # Issue 572
    """Check that config-provided paths are decoupled from CWD."""
    config1 = cli.load_config("test/fixtures/config-with-relative-path.yml")
    monkeypatch.chdir('test')
    config2 = cli.load_config("fixtures/config-with-relative-path.yml")

    assert config1['exclude_paths'].sort() == config2['exclude_paths'].sort()


def test_path_from_cli_depend_on_cwd(
    base_arguments: List[str], monkeypatch: MonkeyPatch
) -> None:
    """Check that CLI-provided paths are relative to CWD."""
    # Issue 572
    arguments = base_arguments + [
        "--exclude",
        "test/fixtures/config-with-relative-path.yml",
    ]

    options1 = cli.get_cli_parser().parse_args(arguments)
    assert 'test/test' not in str(options1.exclude_paths[0])

    test_dir = 'test'
    monkeypatch.chdir(test_dir)
    options2 = cli.get_cli_parser().parse_args(arguments)

    assert 'test/test' in str(options2.exclude_paths[0])


@pytest.mark.parametrize(
    "config_file",
    (
        pytest.param("test/fixtures/ansible-config-invalid.yml", id="invalid"),
        pytest.param("/dev/null/ansible-config-missing.yml", id="missing"),
    ),
)
def test_config_failure(base_arguments: List[str], config_file: str) -> None:
    """Ensures specific config files produce error code 2."""
    with pytest.raises(SystemExit, match="^2$"):
        cli.get_config(base_arguments + ["-c", config_file])


def test_extra_vars_loaded(base_arguments: List[str]) -> None:
    """Ensure ``extra_vars`` option is loaded from file config."""
    config = cli.get_config(
        base_arguments + ["-c", "test/fixtures/config-with-extra-vars.yml"]
    )

    assert config.extra_vars == {'foo': 'bar', 'knights_favorite_word': 'NI'}
