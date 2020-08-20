import os
import sys
from pathlib import Path

import pytest

from ansiblelint import cli


@pytest.fixture
def base_arguments():
    return ['../test/skiptasks.yml']


@pytest.mark.parametrize(('args', 'config'), (
                         (["-p"], "test/fixtures/parseable.yml"),
                         (["-q"], "test/fixtures/quiet.yml"),
                         (["-r", "test/fixtures/rules/"],
                          "test/fixtures/rulesdir.yml"),
                         (["-R", "-r", "test/fixtures/rules/"],
                          "test/fixtures/rulesdir-defaults.yml"),
                         (["-t", "skip_ansible_lint"],
                          "test/fixtures/tags.yml"),
                         (["-v"], "test/fixtures/verbosity.yml"),
                         (["-x", "bad_tag"],
                          "test/fixtures/skip-tags.yml"),
                         (["--exclude", "test/"],
                          "test/fixtures/exclude-paths.yml"),
                         (["--show-relpath"],
                          "test/fixtures/show-abspath.yml"),
                         ([],
                          "test/fixtures/show-relpath.yml"),
                         ))
def test_ensure_config_are_equal(base_arguments, args, config, monkeypatch):
    command = base_arguments + args
    cli_parser = cli.get_cli_parser()

    _real_pathlib_resolve = Path.resolve

    def _fake_pathlib_resolve(self):
        try:
            return _real_pathlib_resolve(self)
        except FileNotFoundError:
            if self != Path(args[-1]):
                raise
            return Path.cwd() / self

    with monkeypatch.context() as mp_ctx:
        if (
                sys.version_info[:2] < (3, 6) and
                args[-2:] == ["-r", "test/fixtures/rules/"]
        ):
            mp_ctx.setattr(Path, 'resolve', _fake_pathlib_resolve)
        options = cli_parser.parse_args(command)

    file_config = cli.load_config(config)

    for key, val in file_config.items():
        if key in {'exclude_paths', 'rulesdir'}:
            val = [Path(p) for p in val]
        assert val == getattr(options, key)


def test_config_can_be_overridden(base_arguments):
    no_override = cli.get_config(base_arguments + ["-t", "bad_tag"])

    overridden = cli.get_config(base_arguments +
                                ["-t", "bad_tag",
                                 "-c", "test/fixtures/tags.yml"])

    assert no_override.tags + ["skip_ansible_lint"] == overridden.tags


def test_different_config_file(base_arguments):
    """Ensures an alternate config_file can be used."""
    diff_config = cli.get_config(base_arguments +
                                 ["-c", "test/fixtures/ansible-config.yml"])
    no_config = cli.get_config(base_arguments + ["-v"])

    assert diff_config.verbosity == no_config.verbosity


def test_expand_path_user_and_vars_config_file(base_arguments):
    """Ensure user and vars are expanded when specified as exclude_paths."""
    config1 = cli.get_config(base_arguments +
                             ["-c", "test/fixtures/exclude-paths-with-expands.yml"])
    config2 = cli.get_config(base_arguments + [
        "--exclude", "~/.ansible/roles",
        "--exclude", "$HOME/.ansible/roles"
    ])

    assert str(config1.exclude_paths[0]) == os.path.expanduser("~/.ansible/roles")
    assert str(config2.exclude_paths[0]) == os.path.expanduser("~/.ansible/roles")
    assert str(config1.exclude_paths[1]) == os.path.expandvars("$HOME/.ansible/roles")
    assert str(config2.exclude_paths[1]) == os.path.expandvars("$HOME/.ansible/roles")


def test_path_from_config_do_not_depend_on_cwd(monkeypatch):  # Issue 572
    config1 = cli.load_config("test/fixtures/config-with-relative-path.yml")
    monkeypatch.chdir('test')
    config2 = cli.load_config("fixtures/config-with-relative-path.yml")

    assert config1['exclude_paths'].sort() == config2['exclude_paths'].sort()


def test_path_from_cli_depend_on_cwd(base_arguments, monkeypatch, tmp_path):
    # Issue 572
    arguments = base_arguments + ["--exclude",
                                  "test/fixtures/config-with-relative-path.yml"]

    options1 = cli.get_cli_parser().parse_args(arguments)
    assert 'test/test' not in str(options1.exclude_paths[0])

    test_dir = 'test'
    if sys.version_info[:2] < (3, 6):
        test_dir = tmp_path / 'test' / 'test' / 'fixtures'
        test_dir.mkdir(parents=True)
        (test_dir / 'config-with-relative-path.yml').write_text('')
        test_dir = test_dir / '..' / '..'
    monkeypatch.chdir(test_dir)
    options2 = cli.get_cli_parser().parse_args(arguments)

    assert 'test/test' in str(options2.exclude_paths[0])


@pytest.mark.parametrize(
    "config_file",
    (
        pytest.param("test/fixtures/ansible-config-invalid.yml", id="invalid"),
        pytest.param("/dev/null/ansible-config-missing.yml", id="missing")
    ),
)
def test_config_failure(base_arguments, config_file):
    """Ensures specific config files produce error code 2."""
    with pytest.raises(SystemExit, match="^2$"):
        cli.get_config(base_arguments +
                       ["-c", config_file])
