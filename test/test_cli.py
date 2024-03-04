"""Test cli arguments and config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ansiblelint import cli

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(name="base_arguments")
def fixture_base_arguments() -> list[str]:
    """Define reusable base arguments for tests in current module."""
    return ["../test/skiptasks.yml"]


@pytest.mark.parametrize(
    ("args", "config_path"),
    (
        pytest.param(["-p"], "test/fixtures/parseable.yml", id="1"),
        pytest.param(["-q"], "test/fixtures/quiet.yml", id="2"),
        pytest.param(
            ["-r", "test/fixtures/rules/"],
            "test/fixtures/rulesdir.yml",
            id="3",
        ),
        pytest.param(
            ["-R", "-r", "test/fixtures/rules/"],
            "test/fixtures/rulesdir-defaults.yml",
            id="4",
        ),
        pytest.param(["-s"], "test/fixtures/strict.yml", id="5"),
        pytest.param(["-t", "skip_ansible_lint"], "test/fixtures/tags.yml", id="6"),
        pytest.param(["-v"], "test/fixtures/verbosity.yml", id="7"),
        pytest.param(["-x", "bad_tag"], "test/fixtures/skip-tags.yml", id="8"),
        pytest.param(["--exclude", "../"], "test/fixtures/exclude-paths.yml", id="9"),
        pytest.param(["--show-relpath"], "test/fixtures/show-abspath.yml", id="10"),
        pytest.param([], "test/fixtures/show-relpath.yml", id="11"),
    ),
)
def test_ensure_config_are_equal(
    base_arguments: list[str],
    args: list[str],
    config_path: str,
) -> None:
    """Check equality of the CLI options to config files."""
    command = base_arguments + args
    cli_parser = cli.get_cli_parser()

    options = cli_parser.parse_args(command)
    file_config = cli.load_config(config_path)[0]
    for key, val in file_config.items():
        # config_file does not make sense in file_config
        if key == "config_file":
            continue

        if key == "rulesdir":
            # this is list of Paths
            val = [Path(p) for p in val]
        assert val == getattr(options, key), f"Mismatch for {key}"


@pytest.mark.parametrize(
    ("with_base", "args", "config", "expected"),
    (
        pytest.param(
            True,
            ["--fix"],
            "test/fixtures/config-with-write-all.yml",
            ["all"],
            id="1",
        ),
        pytest.param(
            True,
            ["--fix=all"],
            "test/fixtures/config-with-write-all.yml",
            ["all"],
            id="2",
        ),
        pytest.param(
            True,
            ["--fix", "all"],
            "test/fixtures/config-with-write-all.yml",
            ["all"],
            id="3",
        ),
        pytest.param(
            True,
            ["--fix=none"],
            "test/fixtures/config-with-write-none.yml",
            [],
            id="4",
        ),
        pytest.param(
            True,
            ["--fix", "none"],
            "test/fixtures/config-with-write-none.yml",
            [],
            id="5",
        ),
        pytest.param(
            True,
            ["--fix=rule-tag,rule-id"],
            "test/fixtures/config-with-write-subset.yml",
            ["rule-tag", "rule-id"],
            id="6",
        ),
        pytest.param(
            True,
            ["--fix", "rule-tag,rule-id"],
            "test/fixtures/config-with-write-subset.yml",
            ["rule-tag", "rule-id"],
            id="7",
        ),
        pytest.param(
            True,
            ["--fix", "rule-tag", "--fix", "rule-id"],
            "test/fixtures/config-with-write-subset.yml",
            ["rule-tag", "rule-id"],
            id="8",
        ),
        pytest.param(
            False,
            ["--fix", "examples/playbooks/example.yml"],
            "test/fixtures/config-with-write-all.yml",
            ["all"],
            id="9",
        ),
        pytest.param(
            False,
            ["--fix", "examples/playbooks/example.yml", "non-existent.yml"],
            "test/fixtures/config-with-write-all.yml",
            ["all"],
            id="10",
        ),
    ),
)
def test_ensure_write_cli_does_not_consume_lintables(
    base_arguments: list[str],
    with_base: bool,
    args: list[str],
    config: str,
    expected: list[str],
) -> None:
    """Check equality of the CLI --fix options to config files."""
    cli_parser = cli.get_cli_parser()

    command = base_arguments + args if with_base else args
    options = cli_parser.parse_args(command)
    file_config = cli.load_config(config)[0]

    file_config.get("write_list")
    orig_cli_value = options.write_list
    cli_value = cli.WriteArgAction.merge_fix_list_config(
        from_file=[],
        from_cli=orig_cli_value,
    )
    assert cli_value == expected


def test_config_can_be_overridden(base_arguments: list[str]) -> None:
    """Check that config can be overridden from CLI."""
    no_override = cli.get_config([*base_arguments, "-t", "bad_tag"])

    overridden = cli.get_config(
        [*base_arguments, "-t", "bad_tag", "-c", "test/fixtures/tags.yml"],
    )

    assert [*no_override.tags, "skip_ansible_lint"] == overridden.tags


def test_different_config_file(base_arguments: list[str]) -> None:
    """Ensures an alternate config_file can be used."""
    diff_config = cli.get_config(
        [*base_arguments, "-c", "test/fixtures/ansible-config.yml"],
    )
    no_config = cli.get_config([*base_arguments, "-v"])

    assert diff_config.verbosity == no_config.verbosity


def test_expand_path_user_and_vars_config_file(base_arguments: list[str]) -> None:
    """Ensure user and vars are expanded when specified as exclude_paths."""
    config1 = cli.get_config(
        [*base_arguments, "-c", "test/fixtures/exclude-paths-with-expands.yml"],
    )
    config2 = cli.get_config(
        [
            *base_arguments,
            "--exclude",
            "~/.ansible/roles",
            "--exclude",
            "$HOME/.ansible/roles",
        ],
    )

    assert str(config1.exclude_paths[0]) == os.path.expanduser(  # noqa: PTH111
        "~/.ansible/roles",
    )
    assert str(config1.exclude_paths[1]) == os.path.expandvars("$HOME/.ansible/roles")

    # exclude-paths coming in via cli are PosixPath objects; which hold the (canonical) real path (without symlinks)
    assert str(config2.exclude_paths[0]) == os.path.realpath(
        os.path.expanduser("~/.ansible/roles"),  # noqa: PTH111
    )
    assert str(config2.exclude_paths[1]) == os.path.realpath(
        os.path.expandvars("$HOME/.ansible/roles"),
    )


def test_path_from_config_do_not_depend_on_cwd(
    monkeypatch: MonkeyPatch,
) -> None:  # Issue 572
    """Check that config-provided paths are decoupled from CWD."""
    config1 = cli.load_config("test/fixtures/config-with-relative-path.yml")[0]
    monkeypatch.chdir("test")
    config2 = cli.load_config("fixtures/config-with-relative-path.yml")[0]

    assert config1["exclude_paths"].sort() == config2["exclude_paths"].sort()


@pytest.mark.parametrize(
    "config_file",
    (
        pytest.param("test/fixtures/ansible-config-invalid.yml", id="invalid"),
        pytest.param("/dev/null/ansible-config-missing.yml", id="missing"),
    ),
)
def test_config_failure(base_arguments: list[str], config_file: str) -> None:
    """Ensures specific config files produce error code 3."""
    with pytest.raises(SystemExit, match="^3$"):
        cli.get_config([*base_arguments, "-c", config_file])


def test_extra_vars_loaded(base_arguments: list[str]) -> None:
    """Ensure ``extra_vars`` option is loaded from file config."""
    config = cli.get_config(
        [*base_arguments, "-c", "test/fixtures/config-with-extra-vars.yml"],
    )

    assert config.extra_vars == {"foo": "bar", "knights_favorite_word": "NI"}


@pytest.mark.parametrize(
    "config_file",
    (pytest.param("/dev/null", id="dev-null"),),
)
def test_config_dev_null(base_arguments: list[str], config_file: str) -> None:
    """Ensures specific config files produce error code 3."""
    cfg = cli.get_config([*base_arguments, "-c", config_file])
    assert cfg.config_file == "/dev/null"
