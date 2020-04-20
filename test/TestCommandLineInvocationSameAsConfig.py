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
def test_ensure_config_are_equal(base_arguments, args, config):
    command = base_arguments + args
    options, _ = cli.get_cli_parser().parse_args(command)

    file_config = cli.load_config(config)

    for key in file_config.keys():
        assert file_config[key] == getattr(options, key)


def test_config_can_be_overridden(base_arguments):
    no_override, _ = cli.get_config(base_arguments + ["-t", "bad_tag"])

    overridden, _ = cli.get_config(base_arguments +
                                   ["-t", "bad_tag",
                                    "-c", "test/fixtures/tags.yml"])

    assert no_override.tags + ["skip_ansible_lint"] == overridden.tags


def test_different_config_file(base_arguments):
    """Ensures an alternate config_file can be used."""
    diff_config, _ = cli.get_config(base_arguments +
                                    ["-c", "test/fixtures/ansible-config.yml"])
    no_config, _ = cli.get_config(base_arguments + ["-v"])

    assert diff_config.verbosity == no_config.verbosity


def test_path_from_config_do_not_depend_on_cwd(monkeypatch):  # Issue 572
    config1 = cli.load_config("test/fixtures/config-with-relative-path.yml")
    monkeypatch.chdir('test')
    config2 = cli.load_config("fixtures/config-with-relative-path.yml")

    assert config1['exclude_paths'].sort() == config2['exclude_paths'].sort()


def test_path_from_cli_depend_on_cwd(base_arguments, monkeypatch):  # Issue 572
    arguments = base_arguments + ["--exclude",
                                  "test/fixtures/config-with-relative-path.yml"]

    options1, _ = cli.get_cli_parser().parse_args(arguments)
    monkeypatch.chdir('test')
    options2, _ = cli.get_cli_parser().parse_args(arguments)

    assert 'test/test' not in options1.exclude_paths[0]
    assert 'test/test' in options2.exclude_paths[0]


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
