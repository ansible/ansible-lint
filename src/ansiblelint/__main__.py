#!/usr/bin/env python
# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Command line implementation."""

from __future__ import annotations

import errno
import logging
import os
import pathlib
import shutil
import site
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from ansible_compat.prerun import get_cache_dir
from filelock import BaseFileLock, FileLock, Timeout

from ansiblelint.constants import RC, SKIP_SCHEMA_UPDATE

# safety check for broken ansible core, needs to happen first
try:
    # pylint: disable=unused-import
    from ansible.parsing.dataloader import DataLoader  # noqa: F401

except Exception as _exc:  # pylint: disable=broad-exception-caught # noqa: BLE001
    logging.fatal(_exc)
    sys.exit(RC.INVALID_CONFIG)
# pylint: disable=ungrouped-imports
from ansiblelint import cli
from ansiblelint._mockings import _perform_mockings_cleanup
from ansiblelint.app import get_app
from ansiblelint.config import (
    Options,
    get_deps_versions,
    get_version_warning,
    log_entries,
    options,
)
from ansiblelint.loaders import IgnoreRule, IgnoreRuleQualifier, load_ignore_txt
from ansiblelint.output import (
    console,
    console_stderr,
    reconfigure,
    render_yaml,
    should_do_markup,
)
from ansiblelint.runner import get_matches
from ansiblelint.skip_utils import normalize_tag
from ansiblelint.version import __version__

if TYPE_CHECKING:
    # RulesCollection must be imported lazily or ansible gets imported too early.

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import LintResult


_logger = logging.getLogger(__name__)


class LintLogHandler(logging.Handler):
    """Custom handler that uses our rich stderr console."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            console_stderr.print(f"[dim]{msg}[/]")
        except RecursionError:  # See issue 36272
            raise
        except Exception:  # pylint: disable=broad-exception-caught # noqa: BLE001
            self.handleError(record)


def initialize_logger(level: int = 0) -> None:
    """Set up the global logging level based on the verbosity number."""
    # We are about to act on the root logger, which defaults to logging.WARNING.
    # That is where our 0 (default) value comes from.
    verbosity_map = {
        -2: logging.CRITICAL,
        -1: logging.ERROR,
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    handler = LintLogHandler()
    formatter = logging.Formatter("%(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    # Unknown logging level is treated as DEBUG
    logging_level = verbosity_map.get(level, logging.DEBUG)
    logger.setLevel(logging_level)
    logging.captureWarnings(True)  # pass all warnings.warn() messages through logging
    # Use module-level _logger instance to validate it
    _logger.debug("Logging initialized to level %s", logging_level)


def initialize_options(arguments: list[str] | None = None) -> BaseFileLock | None:
    """Load config options and store them inside options module."""
    cache_dir_lock = None
    new_options = cli.get_config(arguments or [])
    new_options.cwd = pathlib.Path.cwd()

    if new_options.colored is None:
        new_options.colored = should_do_markup()

    # persist loaded configuration inside options module
    for k, v in new_options.__dict__.items():
        setattr(options, k, v)

    # rename deprecated ids/tags to newer names
    options.tags = [normalize_tag(tag) for tag in options.tags]
    options.skip_list = [normalize_tag(tag) for tag in options.skip_list]
    options.warn_list = [normalize_tag(tag) for tag in options.warn_list]

    options.configured = True
    options.cache_dir = get_cache_dir(pathlib.Path(options.project_dir))

    # add a lock file so we do not have two instances running inside at the same time
    if options.cache_dir:
        options.cache_dir.mkdir(parents=True, exist_ok=True)

    if not options.offline:  # pragma: no cover
        cache_dir_lock = FileLock(
            f"{options.cache_dir}/.lock",
        )
        try:
            cache_dir_lock.acquire(timeout=180)
        except Timeout:  # pragma: no cover
            _logger.error(  # noqa: TRY400
                "Timeout waiting for another instance of ansible-lint to release the lock.",
            )
            sys.exit(RC.LOCK_TIMEOUT)

    # Avoid extra output noise from Ansible about using devel versions
    if "ANSIBLE_DEVEL_WARNING" not in os.environ:  # pragma: no branch
        os.environ["ANSIBLE_DEVEL_WARNING"] = "false"

    return cache_dir_lock


def _do_list(rules: RulesCollection) -> int:
    # On purpose lazy-imports to avoid pre-loading Ansible
    # pylint: disable=import-outside-toplevel
    from ansiblelint.generate_docs import rules_as_str

    if options.list_rules:
        console.print(
            rules_as_str(rules),
        )
        return 0

    if options.list_tags:
        console.print(render_yaml(rules.list_tags()))
        return 0

    # we should not get here!
    return 1


# noinspection PyShadowingNames
def _do_transform(result: LintResult, opts: Options) -> None:
    """Create and run Transformer."""
    if "yaml" in opts.skip_list:
        # The transformer rewrites yaml files, but the user requested to skip
        # the yaml rule or anything tagged with "yaml", so there is nothing to do.
        return

    # On purpose lazy-imports to avoid loading transforms unless requested
    # pylint: disable=import-outside-toplevel
    from ansiblelint.transformer import Transformer

    transformer = Transformer(result, options)

    # this will mark any matches as fixed if the transforms repaired the issue
    transformer.run()


def support_banner() -> None:
    """Display support banner when running on unsupported platform."""


def fix(runtime_options: Options, result: LintResult, rules: RulesCollection) -> None:
    """Fix the linting errors.

    :param options: Options object
    :param result: LintResult object
    """
    match_count = len(result.matches)
    _logger.debug("Begin fixing: %s matches", match_count)
    ruamel_safe_version = "0.17.26"

    # pylint: disable=import-outside-toplevel
    from packaging.version import Version
    from ruamel.yaml import __version__ as ruamel_yaml_version_str

    # pylint: enable=import-outside-toplevel

    if Version(ruamel_safe_version) > Version(
        ruamel_yaml_version_str
    ):  # pragma: no cover
        _logger.warning(
            "We detected use of `--fix` feature with a buggy ruamel-yaml %s library instead of >=%s, upgrade it before reporting any bugs like dropped comments.",
            ruamel_yaml_version_str,
            ruamel_safe_version,
        )
    acceptable_tags = {"all", "none", *rules.known_tags()}
    unknown_tags = set(options.write_list).difference(acceptable_tags)

    if unknown_tags:  # pragma: no cover
        _logger.error(
            "Found invalid value(s) (%s) for --fix arguments, must be one of: %s",
            ", ".join(unknown_tags),
            ", ".join(acceptable_tags),
        )
        sys.exit(RC.INVALID_CONFIG)
    _do_transform(result, options)

    rerun = ["yaml"]
    resolved = []
    for idx, match in reversed(list(enumerate(result.matches))):
        _logger.debug("Fixing: (%s of %s) %s", match_count - idx, match_count, match)
        if match.fixed:
            _logger.debug("Fixed, removed: %s", match)
            result.matches.pop(idx)
            continue
        if match.rule.id not in rerun:
            _logger.debug("Not rerun eligible: %s", match)
            continue

        uid = (match.rule.id, match.filename)
        if uid in resolved:
            _logger.debug("Previously resolved: %s", match)
            result.matches.pop(idx)
            continue
        _logger.debug("Rerunning: %s", match)
        runtime_options.tags = [match.rule.id]
        runtime_options.lintables = [match.filename]
        runtime_options._skip_ansible_syntax_check = True  # noqa: SLF001
        new_results = get_matches(rules, runtime_options)
        if not new_results.matches:
            _logger.debug("Newly resolved: %s", match)
            result.matches.pop(idx)
            resolved.append(uid)
            continue
        if match in new_results.matches:
            _logger.debug("Still found: %s", match)
            continue
        _logger.debug("Fixed, removed: %s", match)
        result.matches.pop(idx)


# By default, matches ignored in .ansible-lint-ignore are treated
# as warnings [1].  If the user explicitly adds a skip qualifier
# to the rule, it is treated as skipped here and does not show up
# even as a warning.
# [1] https://github.com/ansible/ansible-lint/issues/3068
def _rule_is_skipped(tag: str, rules: set[IgnoreRule]) -> bool:
    for rule in rules:
        if tag != rule.rule:
            return False
        return IgnoreRuleQualifier.SKIP in rule.qualifiers
    return False


# pylint: disable=too-many-locals,too-many-statements
def main(argv: list[str] | None = None) -> int:
    """Linter CLI entry point."""
    must_exit = False
    # alter PATH if needed (venv support)
    path_inject(argv[0] if argv and argv[0] else "")

    if argv is None:  # pragma: no cover
        argv = sys.argv

    warnings.simplefilter(
        "ignore", ResourceWarning
    )  # suppress "enable tracemalloc to get the object allocation traceback"
    with warnings.catch_warnings(record=True) as warns:
        # do not use "ignore" as we will miss to collect them
        warnings.simplefilter(action="default")

        cache_dir_lock = initialize_options(argv[1:])

        reconfigure(colored=options.colored)

        if options.version:
            deps = get_deps_versions()
            msg = f"ansible-lint [repr.number]{__version__}[/] using[dim]"
            for k, v in deps.items():
                msg += f" {k}:[repr.number]{v}[/]"
            msg += "[/]"
            console.print(msg)
            msg = get_version_warning()
            if msg:  # pragma: no cover
                console.print(msg)
            support_banner()
            must_exit = True
        else:
            support_banner()

        initialize_logger(options.verbosity)
        for level, message in log_entries:
            _logger.log(level, message)
        _logger.debug("Options: %s", options)
        _logger.debug("CWD: %s", Path.cwd())

    for warn in warns:  # pragma: no cover
        _logger.warning(str(warn.message))
    warnings.resetwarnings()

    if must_exit:
        sys.exit(0)
    # checks if we have `ANSIBLE_LINT_SKIP_SCHEMA_UPDATE` set to bypass schema
    # update. Also skip if in offline mode.
    # env var set to skip schema refresh
    skip_schema_update = (
        bool(
            int(
                os.environ.get(
                    SKIP_SCHEMA_UPDATE,
                    "0",
                ),
            ),
        )
        or options.offline
        or options.nodeps
    )

    if not skip_schema_update:  # pragma: no cover
        # pylint: disable=import-outside-toplevel
        from ansiblelint.schemas.__main__ import refresh_schemas

        refresh_schemas()

    # pylint: disable=import-outside-toplevel
    from ansiblelint.rules import RulesCollection

    if options.list_profiles:
        from ansiblelint.generate_docs import profiles_as_md

        profiles_as_md().display()
        return 0

    app = get_app(
        offline=None,
        cached=True,
    )  # to be sure we use the offline value from settings
    rules = RulesCollection(
        options.rulesdirs,
        profile_name=options.profile,
        app=app,
        options=options,
    )

    if options.list_rules or options.list_tags:
        return _do_list(rules)

    if isinstance(options.tags, str):
        options.tags = options.tags.split(",")  # pragma: no cover
    result = get_matches(rules, options)

    mark_as_success = True

    if options.strict and result.matches:
        mark_as_success = False

    # Remove skip_list items from the result
    result.matches = [m for m in result.matches if m.tag not in app.options.skip_list]
    # load ignore file
    ignore_map = load_ignore_txt(options.ignore_file)
    # prune qualified skips from ignore file
    result.matches = [
        m for m in result.matches if not _rule_is_skipped(m.tag, ignore_map[m.filename])
    ]
    # others entries are ignored
    for match in result.matches:
        if match.tag in [
            i.rule for i in ignore_map[match.filename]
        ]:  # pragma: no cover
            match.ignored = True
            _logger.debug("Ignored: %s", match)

    if app.yamllint_config.incompatible:  # pragma: no cover
        _logger.log(
            level=logging.ERROR if options.write_list else logging.WARNING,
            msg=app.yamllint_config.incompatible,
        )

    if options.write_list:
        if app.yamllint_config.incompatible:  # pragma: no cover
            sys.exit(RC.INVALID_CONFIG)
        fix(runtime_options=options, result=result, rules=rules)

    app.render_matches(result.matches)

    _perform_mockings_cleanup(app.options)
    if cache_dir_lock:
        cache_dir_lock.release()
        pathlib.Path(cache_dir_lock.lock_file).unlink(missing_ok=True)
    if options.mock_filters:
        _logger.warning(
            "The following filters were mocked during the run: %s",
            ",".join(options.mock_filters),
        )

    return app.report_outcome(result, mark_as_success=mark_as_success)


def _run_cli_entrypoint() -> None:
    """Invoke the main entrypoint with current CLI args.

    This function also processes the runtime exceptions.
    """
    try:
        sys.exit(main(sys.argv))
    except OSError as exc:
        # NOTE: Only "broken pipe" is acceptable to ignore
        if exc.errno != errno.EPIPE:  # pragma: no cover
            raise
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(RC.EXIT_CONTROL_C)
    except RuntimeError as exc:  # pragma: no cover
        raise SystemExit(exc) from exc


def path_inject(own_location: str = "") -> None:
    """Add python interpreter path to top of PATH to fix outside venv calling."""
    # This make it possible to call ansible-lint that was installed inside a
    # virtualenv without having to pre-activate it. Otherwise subprocess will
    # either fail to find ansible executables or call the wrong ones.
    #
    # This must be run before we do run any subprocesses, and loading config
    # does this as part of the ansible detection.
    paths = [x for x in os.environ.get("PATH", "").split(os.pathsep) if x]

    # Expand ~ in PATH as it known to break many tools
    expanded = False
    for idx, path in enumerate(paths):
        if path.startswith("~"):  # pragma: no cover
            paths[idx] = str(Path(path).expanduser())
            expanded = True
    if expanded:  # pragma: no cover
        print(  # noqa: T201
            "WARNING: PATH altered to expand ~ in it. Read https://stackoverflow.com/a/44704799/99834 and correct your system configuration.",
            file=sys.stderr,
        )

    inject_paths = []

    userbase_bin_path = Path(site.getuserbase()) / "bin"

    if (
        str(userbase_bin_path) not in paths
        and (userbase_bin_path / "bin" / "ansible").exists()
    ):
        inject_paths.append(userbase_bin_path.resolve().as_posix())

    py_path = Path(sys.executable).parent.resolve()
    pipx_path = os.environ.get("PIPX_HOME", "pipx")
    if (
        str(py_path) not in paths
        and (py_path / "ansible").exists()
        and pipx_path not in str(py_path)
    ):
        inject_paths.append(py_path.as_posix())

    # last option, if nothing else is found, just look next to ourselves...
    if own_location:
        own_location = os.path.realpath(own_location)
        parent = Path(own_location).parent
        if (parent / "ansible").exists() and str(parent) not in paths:
            inject_paths.append(str(parent))

    if not os.environ.get("PYENV_VIRTUAL_ENV", None):
        if inject_paths and not all("pipx" in p for p in inject_paths):
            print(  # noqa: T201
                f"WARNING: PATH altered to include {', '.join(inject_paths)} :: This is usually a sign of broken local setup, which can cause unexpected behaviors.",
                file=sys.stderr,
            )
        if inject_paths or expanded:
            os.environ["PATH"] = os.pathsep.join([*inject_paths, *paths])

    # We do know that finding ansible in PATH does not guarantee that it is
    # functioning or that is in fact the same version that was installed as
    # our dependency, but addressing this would be done by ansible-compat.
    for cmd in ("ansible",):
        if not shutil.which(cmd):  # pragma: no cover
            msg = f"Failed to find runtime dependency '{cmd}' in PATH"
            raise RuntimeError(msg)


if __name__ == "__main__":
    _run_cli_entrypoint()
