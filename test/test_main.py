"""Tests related to ansiblelint.__main__ module."""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from copy import deepcopy
from http.client import RemoteDisconnected
from os.path import abspath
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ansiblelint.config import Options, get_version_warning, options
from ansiblelint.constants import RC
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.loaders import yaml_load_safe
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import LintResult


@pytest.mark.parametrize(
    ("in_path"),
    (False, True),
    ids=("in", "missing"),
)
def test_call_from_outside_venv(in_path: bool) -> None:
    """Asserts ability to be called w/ or w/o venv activation."""
    git_location = shutil.which("git")
    if not git_location:
        pytest.fail("git not found")
    git_path = Path(git_location).parent
    py_path = Path(sys.executable).parent.resolve().as_posix()

    env = os.environ.copy()
    env["VIRTUAL_ENV"] = ""
    env["NO_COLOR"] = "1"
    if in_path:
        # VIRTUAL_ENV obliterated here to emulate call from outside a virtual environment
        env["HOME"] = Path.home().as_posix()
        env["PATH"] = git_path.as_posix()
    else:
        if py_path not in env["PATH"]:
            env["PATH"] = f"{py_path}:{env['PATH']}"

    for v in ("COVERAGE_FILE", "COVERAGE_PROCESS_START"):
        if v in os.environ:
            env[v] = os.environ[v]

    # Passing custom env prevents the process from inheriting PATH or other
    # environment variables from the current process, so we emulate being
    # called from outside the venv.
    proc = subprocess.run(
        [f"{py_path}/ansible-lint", "--version"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc
    warning_found = "PATH altered to include" in proc.stderr
    assert warning_found is in_path


@pytest.mark.parametrize(
    ("ver_diff", "found", "check", "outlen"),
    (
        pytest.param("v1.2.2", True, "pre-release", 1, id="0"),
        pytest.param("v1.2.3", False, "", 1, id="1"),
        pytest.param("v1.2.4", True, "new release", 2, id="2"),
    ),
)
def test_get_version_warning(
    mocker: MockerFixture,
    ver_diff: str,
    found: bool,
    check: str,
    outlen: int,
) -> None:
    """Assert get_version_warning working as expected."""
    data = f'{{"html_url": "https://127.0.0.1", "tag_name": "{ver_diff}"}}'
    # simulate cache file
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.getmtime", return_value=time.time())
    mocker.patch("builtins.open", mocker.mock_open(read_data=data))
    # overwrite ansible-lint version
    mocker.patch("ansiblelint.config.__version__", "1.2.3")
    # overwrite install method to custom one. This one will increase msg line count
    # to easily detect unwanted call to it.
    mocker.patch("ansiblelint.config.guess_install_method", return_value="\n")
    msg = get_version_warning()

    if not found:
        assert msg == check
    else:
        assert check in msg
    assert len(msg.split("\n")) == outlen


def test_get_version_warning_no_pip(mocker: MockerFixture) -> None:
    """Test that we do not display any message if install method is not pip."""
    mocker.patch("ansiblelint.config.guess_install_method", return_value="")
    assert get_version_warning() == ""  # noqa: PLC1901


def test_get_version_warning_remote_disconnect(mocker: MockerFixture) -> None:
    """Test that we can handle remote disconnect when fetching release url."""
    mocker.patch("urllib.request.urlopen", side_effect=RemoteDisconnected)
    try:
        get_version_warning()
    except RemoteDisconnected:
        pytest.fail("Failed to handle a remote disconnect")


def test_get_version_warning_offline(mocker: MockerFixture) -> None:
    """Test that offline mode does not display any message."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        # ensures a real cache_file is not loaded
        mocker.patch("ansiblelint.config.CACHE_DIR", Path(temporary_directory))
        options.offline = True
        assert get_version_warning() == ""  # noqa: PLC1901


@pytest.mark.parametrize(
    ("offline", "cache_created"),
    (
        pytest.param(True, False, id="offline"),
        pytest.param(False, True, id="online"),
    ),
)
def test_initialize_options_cache_dir_creation(
    tmp_path: Path,
    offline: bool,
    cache_created: bool,
) -> None:
    """Check that offline mode does not create an isolated cache directory."""
    from ansiblelint.__main__ import initialize_options

    old_options = deepcopy(options)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    cache_dir = project_dir / ".ansible"

    arguments = ["--config-file", "/dev/null", "--project-dir", str(project_dir)]
    if offline:
        arguments.append("--offline")

    cache_dir_lock = initialize_options(arguments)
    try:
        expected_cache_dir = (
            Path(os.environ.get("ANSIBLE_HOME", "~/.ansible")).expanduser()
            if offline
            else cache_dir
        )
        assert options.cache_dir == expected_cache_dir
        assert cache_dir.exists() is cache_created
    finally:
        if cache_dir_lock:
            cache_dir_lock.release()
            Path(cache_dir_lock.lock_file).unlink(missing_ok=True)
        options.__dict__.clear()
        options.__dict__.update(old_options.__dict__)


@pytest.mark.parametrize(
    ("lintable"),
    (
        pytest.param("examples/playbooks/nodeps.yml", id="1"),
        pytest.param("examples/playbooks/nodeps2.yml", id="2"),
    ),
)
def test_nodeps(lintable: str) -> None:
    """Asserts ability to be called w/ or w/o venv activation."""
    env = os.environ.copy()
    env["ANSIBLE_LINT_NODEPS"] = "1"
    py_path = Path(sys.executable).parent
    proc = subprocess.run(
        [str(py_path / "ansible-lint"), lintable],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc


def test_broken_ansible_cfg() -> None:
    """Asserts behavior when encountering broken ansible.cfg files."""
    py_path = Path(sys.executable).parent
    proc = subprocess.run(
        [str(py_path / "ansible-lint"), "--version"],
        check=False,
        capture_output=True,
        text=True,
        cwd="test/fixtures/broken-ansible.cfg",
    )
    assert proc.returncode == RC.INVALID_CONFIG, proc
    # 2.19 had different errors
    assert any(
        x in proc.stderr
        for x in (
            "Invalid type for configuration option setting: CACHE_PLUGIN_TIMEOUT",
            "has an invalid value: Invalid type provided for 'int': 'invalid-value'",
            "has an invalid value: Invalid value provided for 'integer': 'invalid-value'",
        )
    ), proc.stderr


def test_list_tags() -> None:
    """Asserts that we can list tags and that the output is parsable yaml."""
    result = subprocess.run(
        ["ansible-lint", "--list-tags"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = yaml_load_safe(result.stdout)
    assert isinstance(data, Mapping)
    for key, value in data.items():
        assert isinstance(key, str)
        assert isinstance(value, list)
        for item in value:
            assert isinstance(item, str)


def test_ro_venv(tmp_path: Path) -> None:
    """Tests behavior when the virtual environment is read-only."""
    tox_work_dir = os.environ.get("TOX_WORK_DIR", ".tox")
    venv_path = f"{tox_work_dir}/ro"
    commands = [
        f"mkdir -p {venv_path}",
        f"chmod -R a+w {venv_path}",
        f"rm -rf {venv_path}",
        f"uv venv --seed --no-project {venv_path}",
        f"VIRTUAL_ENV={venv_path} uv pip install -q -e .",
        f"chmod -R a-w {venv_path}",
        # running with a ro venv and default cwd
        f"{venv_path}/bin/ansible-lint --version",
        # running from a read-only cwd:
        f"cd / && {abspath(venv_path)}/bin/ansible-lint --version",  # noqa: PTH100
        # running with a ro venv and a custom project path in forced non-online mode, so it will need to install requirements
        f"{venv_path}/bin/ansible-lint -vv --nocolor --no-offline --project-dir {tmp_path.as_posix()} ./examples/reqs_v2/",
    ]
    for cmd in commands:
        result = subprocess.run(
            cmd, capture_output=True, shell=True, text=True, check=False
        )
        assert result.returncode == 0, (
            f"Got {result.returncode} running {cmd}\n\tstderr: {result.stderr}\n\tstdout: {result.stdout}"
        )


def _yaml_line_length_match(
    lintable_name: str = "roles/demo/tasks/main.yml",
) -> MatchError:
    from ansiblelint.rules.yaml_rule import YamllintRule

    rule = YamllintRule()
    lintable = Lintable(lintable_name, content="---\n- debug: msg=hi\n")
    return MatchError(
        message="Line too long (267 > 160 characters)",
        lintable=lintable,
        tag="yaml[line-length]",
        lineno=5,
        rule=rule,
    )


def test_is_warn_list_match() -> None:
    """warn_list membership must match rule id, tag, or rule tags."""
    from ansiblelint.__main__ import _is_warn_list_match

    match = _yaml_line_length_match()
    assert _is_warn_list_match(match, ["yaml[line-length]"])
    assert _is_warn_list_match(match, ["yaml"])
    assert not _is_warn_list_match(match, ["name"])


def test_handle_warn_list_rerun() -> None:
    """warn_list yaml matches must be refreshed, not dropped, after rerun."""
    from ansiblelint.__main__ import _handle_warn_list_rerun

    match = _yaml_line_length_match()
    result = LintResult([match], {match.lintable})
    refreshed = MatchError(
        message=match.message,
        lintable=match.lintable,
        tag="yaml[line-length]",
        lineno=6,
        rule=match.rule,
    )
    new_results = LintResult([refreshed], set())

    assert _handle_warn_list_rerun(0, match, new_results, result, ["yaml[line-length]"])
    assert result.matches[0].lineno == 6
    assert not _handle_warn_list_rerun(0, match, new_results, result, ["name"])


def test_apply_rerun_outcome() -> None:
    """Non-warn yaml rerun outcomes must update the match list."""
    from ansiblelint.__main__ import _apply_rerun_outcome

    match = _yaml_line_length_match()
    result = LintResult([match], set())
    resolved: list[tuple[str, str]] = []

    _apply_rerun_outcome(0, match, LintResult([], set()), result, resolved)
    assert result.matches == []
    assert resolved == [("yaml", match.filename)]

    result = LintResult([match], set())
    _apply_rerun_outcome(0, match, LintResult([match], set()), result, resolved)
    assert len(result.matches) == 1

    other = MatchError(
        message="Wrong indentation",
        lintable=match.lintable,
        tag="yaml[indentation]",
        lineno=1,
        rule=match.rule,
    )
    result = LintResult([match], set())
    _apply_rerun_outcome(0, match, LintResult([other], set()), result, resolved)
    assert result.matches == []


def test_handle_warn_list_rerun_retains_when_no_refresh_match() -> None:
    """warn_list matches must stay when rerun finds no same-tag refresh."""
    from ansiblelint.__main__ import _handle_warn_list_rerun

    match = _yaml_line_length_match()
    result = LintResult([match], set())
    other = MatchError(
        message="Wrong indentation",
        lintable=match.lintable,
        tag="yaml[indentation]",
        lineno=1,
        rule=match.rule,
    )

    assert _handle_warn_list_rerun(
        0,
        match,
        LintResult([other], set()),
        result,
        ["yaml[line-length]"],
    )
    assert result.matches[0] is match


def test_process_fix_rerun_matches(
    mocker: MockerFixture,
    config_options: Options,
    default_rules_collection: RulesCollection,
) -> None:
    """Post-fix yaml reruns must honor fixed, skipped, resolved, and warn_list paths."""
    from ansiblelint.__main__ import _process_fix_rerun_matches
    from ansiblelint.rules.name import NameRule

    yaml_match = _yaml_line_length_match()
    fixed_match = _yaml_line_length_match()
    fixed_match.fixed = True

    name_rule = NameRule()
    name_match = MatchError(
        message=name_rule.shortdesc,
        lintable=Lintable("play.yml", content="---\n- name: x\n  debug: msg=hi\n"),
        tag="name[casing]",
        lineno=2,
        rule=name_rule,
    )

    config_options.warn_list = ["yaml[line-length]"]
    refreshed = MatchError(
        message=yaml_match.message,
        lintable=yaml_match.lintable,
        tag="yaml[line-length]",
        lineno=8,
        rule=yaml_match.rule,
    )
    mocker.patch(
        "ansiblelint.__main__.get_matches",
        return_value=LintResult([refreshed], set()),
    )

    result = LintResult(
        [fixed_match, name_match, yaml_match],
        {yaml_match.lintable},
    )
    match_count = len(result.matches)

    _process_fix_rerun_matches(
        config_options,
        result,
        default_rules_collection,
        match_count,
    )

    assert fixed_match not in result.matches
    assert name_match in result.matches
    yaml_matches = [m for m in result.matches if m.tag == "yaml[line-length]"]
    assert len(yaml_matches) == 1
    assert yaml_matches[0].lineno == 8


def test_process_fix_rerun_matches_drops_previously_resolved(
    mocker: MockerFixture,
    config_options: Options,
    default_rules_collection: RulesCollection,
) -> None:
    """Second yaml match for the same file must drop after the first resolves."""
    from ansiblelint.__main__ import _process_fix_rerun_matches

    yaml_match = _yaml_line_length_match()
    yaml_dup = _yaml_line_length_match()
    config_options.warn_list = []
    mocker.patch(
        "ansiblelint.__main__.get_matches",
        return_value=LintResult([], set()),
    )

    result = LintResult([yaml_match, yaml_dup], set())
    _process_fix_rerun_matches(
        config_options,
        result,
        default_rules_collection,
        len(result.matches),
    )

    assert result.matches == []
