"""Runner implementation."""

from __future__ import annotations

import json
import logging
import math
import multiprocessing
import multiprocessing.pool
import os
import re
import subprocess
import tempfile
import warnings
from dataclasses import dataclass
from fnmatch import fnmatch
from functools import cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any

from ansible.errors import AnsibleError
from ansible.parsing.splitter import split_args
from ansible.parsing.yaml.constructor import AnsibleMapping
from ansible.plugins.loader import add_all_plugin_dirs
from ansible_compat.runtime import AnsibleWarning

import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint.app import App, get_app
from ansiblelint.constants import States
from ansiblelint.errors import LintWarning, MatchError, WarnSource
from ansiblelint.file_utils import Lintable, expand_dirs_in_lintables
from ansiblelint.logger import timed_info
from ansiblelint.rules.syntax_check import OUTPUT_PATTERNS
from ansiblelint.text import strip_ansi_escape
from ansiblelint.utils import (
    PLAYBOOK_DIR,
    HandleChildren,
    parse_examples_from_plugin,
    template,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from ansiblelint._internal.rules import BaseRule
    from ansiblelint.config import Options
    from ansiblelint.constants import FileType
    from ansiblelint.rules import RulesCollection

_logger = logging.getLogger(__name__)


@dataclass
class LintResult:
    """Class that tracks result of linting."""

    matches: list[MatchError]
    files: set[Lintable]


class Runner:
    """Runner class performs the linting process."""

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(
        self,
        *lintables: Lintable | str | Path,
        rules: RulesCollection,
        tags: frozenset[Any] = frozenset(),
        skip_list: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        verbosity: int = 0,
        checked_files: set[Lintable] | None = None,
        project_dir: str | None = None,
        _skip_ansible_syntax_check: bool = False,
    ) -> None:
        """Initialize a Runner instance."""
        self.rules = rules
        self.lintables: set[Lintable] = set()
        self.project_dir = os.path.abspath(project_dir) if project_dir else None
        self.skip_ansible_syntax_check = _skip_ansible_syntax_check

        if skip_list is None:
            skip_list = []
        if exclude_paths is None:
            exclude_paths = []

        # Assure consistent type and configure given lintables as explicit (so
        # excludes paths would not apply on them).
        for item in lintables:
            if not isinstance(item, Lintable):
                item = Lintable(item)
            item.explicit = True
            self.lintables.add(item)

        # Expand folders (roles) to their components
        expand_dirs_in_lintables(self.lintables)

        self.tags = tags
        self.skip_list = skip_list
        self._update_exclude_paths(exclude_paths)
        self.verbosity = verbosity
        if checked_files is None:
            checked_files = set()
        self.checked_files = checked_files

        self.app = get_app(cached=True)

    def _update_exclude_paths(self, exclude_paths: list[str]) -> None:
        if exclude_paths:
            # These will be (potentially) relative paths
            paths = ansiblelint.file_utils.expand_paths_vars(exclude_paths)
            # Since ansiblelint.utils.find_children returns absolute paths,
            # and the list of files we create in `Runner.run` can contain both
            # relative and absolute paths, we need to cover both bases.
            self.exclude_paths = paths + [os.path.abspath(p) for p in paths]
        else:
            self.exclude_paths = []

    def is_excluded(self, lintable: Lintable) -> bool:
        """Verify if a file path should be excluded."""
        # Any will short-circuit as soon as something returns True, but will
        # be poor performance for the case where the path under question is
        # not excluded.

        # Exclusions should be evaluated only using absolute paths in order
        # to work correctly.

        # Explicit lintables are never excluded
        if lintable.explicit:
            return False

        abs_path = str(lintable.abspath)
        if self.project_dir and not abs_path.startswith(self.project_dir):
            _logger.debug(
                "Skipping %s as it is outside of the project directory.",
                abs_path,
            )
            return True

        return any(
            abs_path.startswith(path)
            or lintable.path.match(path)
            or fnmatch(str(abs_path), path)
            or fnmatch(str(lintable), path)
            for path in self.exclude_paths
        )

    def run(self) -> list[MatchError]:
        """Execute the linting process."""
        matches: list[MatchError] = []
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            matches = self._run()
            for warn in captured_warnings:
                # Silence Ansible runtime warnings that are unactionable
                # https://github.com/ansible/ansible-lint/issues/3216
                if warn.category is AnsibleWarning and isinstance(warn.source, dict):
                    msg = warn.source["msg"]
                    if msg.startswith(
                        "Falling back to Ansible unique filter as Jinja2 one failed",
                    ):
                        continue
                # For the moment we are ignoring deprecation warnings as Ansible
                # modules outside current content can generate them and user
                # might not be able to do anything about them.
                if warn.category is DeprecationWarning:
                    continue
                if warn.category is LintWarning:
                    filename: None | Lintable = None
                    if isinstance(warn.source, WarnSource):
                        match = MatchError(
                            message=warn.source.message or warn.category.__name__,
                            rule=self.rules["warning"],
                            filename=warn.source.filename.filename,
                            tag=warn.source.tag,
                            lineno=warn.source.lineno,
                        )
                    else:
                        filename = warn.source
                        match = MatchError(
                            message=(
                                warn.message if isinstance(warn.message, str) else "?"
                            ),
                            rule=self.rules["warning"],
                            filename=str(filename),
                        )
                    matches.append(match)
                    continue
                _logger.warning(
                    "%s:%s %s %s",
                    warn.filename,
                    warn.lineno or 1,
                    warn.category.__name__,
                    warn.message,
                )
        return matches

    def _run(self) -> list[MatchError]:
        """Run the linting (inner loop)."""
        files: list[Lintable] = []
        matches: list[MatchError] = []

        # remove exclusions
        for lintable in self.lintables.copy():
            if self.is_excluded(lintable):
                _logger.debug("Excluded %s", lintable)
                self.lintables.remove(lintable)
                continue
            if isinstance(lintable.data, States) and lintable.exc:
                lintable.exc.__class__.__name__.lower()
                matches.append(
                    MatchError(
                        lintable=lintable,
                        message=str(lintable.exc),
                        details=str(lintable.exc.__cause__),
                        rule=self.rules["load-failure"],
                        tag=f"load-failure[{lintable.exc.__class__.__name__.lower()}]",
                    ),
                )
                lintable.stop_processing = True
            # identify missing files/folders
            if not lintable.path.exists():
                matches.append(
                    MatchError(
                        lintable=lintable,
                        message="File or directory not found.",
                        rule=self.rules["load-failure"],
                        tag="load-failure[not-found]",
                    ),
                )

        # -- phase 1 : syntax check in parallel --
        if not self.skip_ansible_syntax_check:
            # app = get_app(cached=True)

            def worker(lintable: Lintable) -> list[MatchError]:
                return self._get_ansible_syntax_check_matches(
                    lintable=lintable,
                    app=self.app,
                )

            for lintable in self.lintables:
                if (
                    lintable.kind not in ("playbook", "role")
                    or lintable.stop_processing
                ):
                    continue
                files.append(lintable)

            # avoid resource leak warning, https://github.com/python/cpython/issues/90549
            # pylint: disable=unused-variable
            global_resource = multiprocessing.Semaphore()  # noqa: F841

            pool = multiprocessing.pool.ThreadPool(processes=threads())
            return_list = pool.map(worker, files, chunksize=1)
            pool.close()
            pool.join()
            for data in return_list:
                matches.extend(data)

            matches = self._filter_excluded_matches(matches)

        # -- phase 2 ---
        # do our processing only when ansible syntax check passed in order
        # to avoid causing runtime exceptions. Our processing is not as
        # resilient to be able process garbage.
        matches.extend(self._emit_matches(files))

        # remove duplicates from files list
        files = [value for n, value in enumerate(files) if value not in files[:n]]

        for file in self.lintables:
            if file in self.checked_files or not file.kind or file.failed():
                continue
            _logger.debug(
                "Examining %s of type %s",
                ansiblelint.file_utils.normpath(file.path),
                file.kind,
            )

            matches.extend(
                self.rules.run(file, tags=set(self.tags), skip_list=self.skip_list),
            )

        # update list of checked files
        self.checked_files.update(self.lintables)

        # remove any matches made inside excluded files
        matches = self._filter_excluded_matches(matches)

        return sorted(set(matches))

    # pylint: disable=too-many-locals
    def _get_ansible_syntax_check_matches(
        self,
        lintable: Lintable,
        app: App,
    ) -> list[MatchError]:
        """Run ansible syntax check and return a list of MatchError(s)."""
        try:
            default_rule: BaseRule = self.rules["syntax-check"]
        except ValueError:
            # if syntax-check is not loaded, we do not perform any syntax check,
            # that might happen during testing
            return []
        fh = None
        results = []
        if lintable.kind not in ("playbook", "role"):
            return []

        with timed_info(
            "Executing syntax check on %s %s",
            lintable.kind,
            lintable.path,
        ):
            if lintable.kind == "role":
                playbook_text = f"""
---
- name: Temporary playbook for role syntax check
  hosts: localhost
  tasks:
    - ansible.builtin.import_role:
        name: {lintable.path.expanduser()!s}
"""
                # pylint: disable=consider-using-with
                fh = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", prefix="play")
                fh.write(playbook_text)
                fh.flush()
                playbook_path = fh.name
            else:
                playbook_path = str(lintable.path.expanduser())
            # To avoid noisy warnings we pass localhost as current inventory:
            # [WARNING]: No inventory was parsed, only implicit localhost is available
            # [WARNING]: provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'
            cmd = [
                "ansible-playbook",
                "-i",
                "localhost,",
                "--syntax-check",
                playbook_path,
            ]
            if app.options.extra_vars:
                cmd.extend(["--extra-vars", json.dumps(app.options.extra_vars)])

            # To reduce noisy warnings like
            # CryptographyDeprecationWarning: Blowfish has been deprecated
            # https://github.com/paramiko/paramiko/issues/2038
            env = app.runtime.environ.copy()
            env["PYTHONWARNINGS"] = "ignore"
            # Avoid execution failure if user customized any_unparsed_is_failed setting
            # https://github.com/ansible/ansible-lint/issues/3650
            env["ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED"] = "False"

            run = subprocess.run(
                cmd,
                stdin=subprocess.PIPE,
                capture_output=True,
                shell=False,  # needed when command is a list # noqa: S603
                text=True,
                check=False,
                env=env,
            )

        if run.returncode != 0:
            message = None
            filename = lintable
            lineno = 1
            column = None
            ignore_rc = False

            stderr = strip_ansi_escape(run.stderr)
            stdout = strip_ansi_escape(run.stdout)
            if stderr:
                details = stderr
                if stdout:
                    details += "\n" + stdout
            else:
                details = stdout

            for pattern in OUTPUT_PATTERNS:
                rule = default_rule
                match = re.search(pattern.regex, stderr)
                if match:
                    groups = match.groupdict()
                    title = groups.get("title", match.group(0))
                    details = groups.get("details", "")
                    lineno = int(groups.get("line", 1))

                    if (
                        "filename" in groups
                        and str(lintable.path.absolute()) != groups["filename"]
                        and lintable.filename != groups["filename"]
                    ):
                        # avoids creating a new lintable object if the filename
                        # is matching as this might prevent Lintable.failed()
                        # feature from working well.
                        filename = Lintable(groups["filename"])
                    else:
                        filename = lintable
                    column = int(groups.get("column", 1))

                    if (
                        pattern.tag in ("unknown-module", "specific")
                        and app.options.nodeps
                    ):
                        ignore_rc = True
                    else:
                        results.append(
                            MatchError(
                                message=title,
                                lintable=filename,
                                lineno=lineno,
                                column=column,
                                rule=rule,
                                details=details,
                                tag=f"{rule.id}[{pattern.tag}]",
                            ),
                        )
                    break

            if not results and not ignore_rc:
                rule = self.rules["internal-error"]
                message = (
                    f"Unexpected error code {run.returncode} from "
                    f"execution of: {' '.join(cmd)}"
                )
                results.append(
                    MatchError(
                        message=message,
                        lintable=filename,
                        lineno=lineno,
                        column=column,
                        rule=rule,
                        details=details,
                        tag="",
                    ),
                )

        if fh:
            fh.close()
        return results

    def _filter_excluded_matches(self, matches: list[MatchError]) -> list[MatchError]:
        return [
            match
            for match in matches
            if not self.is_excluded(match.lintable)
            and match.tag not in match.lintable.line_skips[match.lineno]
        ]

    def _emit_matches(self, files: list[Lintable]) -> Generator[MatchError, None, None]:
        visited: set[Lintable] = set()
        while visited != self.lintables:
            for lintable in self.lintables - visited:
                try:
                    children = self.find_children(lintable)
                    for child in children:
                        if self.is_excluded(child):
                            continue
                        self.lintables.add(child)
                        files.append(child)
                except MatchError as exc:
                    if not exc.filename:  # pragma: no branch
                        exc.filename = str(lintable.path)
                    exc.rule = self.rules["load-failure"]
                    yield exc
                except AttributeError:
                    yield MatchError(lintable=lintable, rule=self.rules["load-failure"])
                visited.add(lintable)

    def find_children(self, lintable: Lintable) -> list[Lintable]:
        """Traverse children of a single file or folder."""
        if not lintable.path.exists():
            return []
        playbook_dir = str(lintable.path.parent)
        ansiblelint.utils.set_collections_basedir(lintable.path.parent)
        add_all_plugin_dirs(playbook_dir or ".")
        if lintable.kind == "role":
            playbook_ds = AnsibleMapping({"roles": [{"role": str(lintable.path)}]})
        elif lintable.kind == "plugin":
            return self.plugin_children(lintable)
        elif lintable.kind not in ("playbook", "tasks"):
            return []
        else:
            try:
                playbook_ds = ansiblelint.utils.parse_yaml_from_file(str(lintable.path))
            except AnsibleError as exc:
                msg = f"Loading {lintable.filename} caused an {type(exc).__name__} exception: {exc}, file was ignored."
                logging.exception(msg)
                # raise SystemExit(exc) from exc
                return []
        results = []
        # playbook_ds can be an AnsibleUnicode string, which we consider invalid
        if isinstance(playbook_ds, str):
            raise MatchError(lintable=lintable, rule=self.rules["load-failure"])
        for item in ansiblelint.utils.playbook_items(playbook_ds):
            # if lintable.kind not in ["playbook"]:
            for child in self.play_children(
                lintable.path.parent,
                item,
                lintable.kind,
                playbook_dir,
            ):
                # We avoid processing parametrized children
                path_str = str(child.path)
                if "$" in path_str or "{{" in path_str:
                    continue

                # Repair incorrect paths obtained when old syntax was used, like:
                # - include: simpletask.yml tags=nginx
                valid_tokens = []
                for token in split_args(path_str):
                    if "=" in token:
                        break
                    valid_tokens.append(token)
                path = " ".join(valid_tokens)
                if path != path_str:
                    child.path = Path(path)
                    child.name = child.path.name
                results.append(child)
        return results

    def play_children(
        self,
        basedir: Path,
        item: tuple[str, Any],
        parent_type: FileType,
        playbook_dir: str,
    ) -> list[Lintable]:
        """Flatten the traversed play tasks."""
        # pylint: disable=unused-argument

        handlers = HandleChildren(self.rules, app=self.app)

        delegate_map: dict[
            str,
            Callable[[str, Any, Any, FileType], list[Lintable]],
        ] = {
            "tasks": handlers.taskshandlers_children,
            "pre_tasks": handlers.taskshandlers_children,
            "post_tasks": handlers.taskshandlers_children,
            "block": handlers.taskshandlers_children,
            "include": handlers.include_children,
            "ansible.builtin.include": handlers.include_children,
            "import_playbook": handlers.include_children,
            "ansible.builtin.import_playbook": handlers.include_children,
            "roles": handlers.roles_children,
            "dependencies": handlers.roles_children,
            "handlers": handlers.taskshandlers_children,
            "include_tasks": handlers.include_children,
            "ansible.builtin.include_tasks": handlers.include_children,
            "import_tasks": handlers.include_children,
            "ansible.builtin.import_tasks": handlers.include_children,
        }
        (k, v) = item
        add_all_plugin_dirs(str(basedir.resolve()))

        if k in delegate_map and v:
            v = template(
                basedir,
                v,
                {"playbook_dir": PLAYBOOK_DIR or str(basedir.resolve())},
                fail_on_undefined=False,
            )
            return delegate_map[k](str(basedir), k, v, parent_type)
        return []

    def plugin_children(self, lintable: Lintable) -> list[Lintable]:
        """Collect lintable sections from plugin file."""
        offset, content = parse_examples_from_plugin(lintable)
        if not content:
            # No examples, nothing to see here
            return []
        examples = Lintable(
            name=lintable.name,
            content=content,
            kind="yaml",
            base_kind="text/yaml",
            parent=lintable,
        )
        examples.line_offset = offset

        # pylint: disable=consider-using-with
        examples.file = NamedTemporaryFile(
            mode="w+",
            suffix=f"_{lintable.path.name}.yaml",
        )
        examples.file.write(content)
        examples.file.flush()
        examples.filename = examples.file.name
        examples.path = Path(examples.file.name)
        return [examples]


@cache
def threads() -> int:
    """Determine how many threads to use.

    Inside containers we want to respect limits imposed.

    When present /sys/fs/cgroup/cpu.max can contain something like:
    $ podman/docker run -it --rm --cpus 1.5 ubuntu:latest cat /sys/fs/cgroup/cpu.max
    150000 100000
    # "max 100000" is returned when no limits are set.

    See: https://github.com/python/cpython/issues/80235
    See: https://github.com/python/cpython/issues/70879
    """
    os_cpu_count = multiprocessing.cpu_count()
    # Cgroup CPU bandwidth limit available in Linux since 2.6 kernel

    cpu_max_fname = "/sys/fs/cgroup/cpu.max"
    cfs_quota_fname = "/sys/fs/cgroup/cpu/cpu.cfs_quota_us"
    cfs_period_fname = "/sys/fs/cgroup/cpu/cpu.cfs_period_us"
    if os.path.exists(cpu_max_fname):
        # cgroup v2
        # https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html
        with open(cpu_max_fname, encoding="utf-8") as fh:
            cpu_quota_us, cpu_period_us = fh.read().strip().split()
    elif os.path.exists(cfs_quota_fname) and os.path.exists(cfs_period_fname):
        # cgroup v1
        # https://www.kernel.org/doc/html/latest/scheduler/sched-bwc.html#management
        with open(cfs_quota_fname, encoding="utf-8") as fh:
            cpu_quota_us = fh.read().strip()
        with open(cfs_period_fname, encoding="utf-8") as fh:
            cpu_period_us = fh.read().strip()
    else:
        # No Cgroup CPU bandwidth limit (e.g. non-Linux platform)
        cpu_quota_us = "max"
        cpu_period_us = "100000"  # unused, for consistency with default values

    if cpu_quota_us == "max":
        # No active Cgroup quota on a Cgroup-capable platform
        return os_cpu_count
    cpu_quota_us_int = int(cpu_quota_us)
    cpu_period_us_int = int(cpu_period_us)
    if cpu_quota_us_int > 0 and cpu_period_us_int > 0:
        return math.ceil(cpu_quota_us_int / cpu_period_us_int)
    # Setting a negative cpu_quota_us value is a valid way to disable
    # cgroup CPU bandwidth limits
    return os_cpu_count


def get_matches(rules: RulesCollection, options: Options) -> LintResult:
    """Get matches for given rules and options.

    :param rules: Rules to use for linting.
    :param options: Options to use for linting.
    :returns: LintResult containing matches and checked files.
    """
    lintables = ansiblelint.utils.get_lintables(opts=options, args=options.lintables)

    for rule in rules:
        if "unskippable" in rule.tags:
            for entry in (*options.skip_list, *options.warn_list):
                if rule.id == entry or entry.startswith(f"{rule.id}["):
                    msg = f"Rule '{rule.id}' is unskippable, you cannot use it in 'skip_list' or 'warn_list'. Still, you could exclude the file."
                    raise RuntimeError(msg)
    matches = []
    checked_files: set[Lintable] = set()
    runner = Runner(
        *lintables,
        rules=rules,
        tags=frozenset(options.tags),
        skip_list=options.skip_list,
        exclude_paths=options.exclude_paths,
        verbosity=options.verbosity,
        checked_files=checked_files,
        project_dir=options.project_dir,
        _skip_ansible_syntax_check=options._skip_ansible_syntax_check,  # noqa: SLF001
    )
    matches.extend(runner.run())

    # Assure we do not print duplicates and the order is consistent
    matches = sorted(set(matches))

    # Convert reported filenames into human readable ones, so we hide the
    # fact we used temporary files when processing input from stdin.
    for match in matches:
        for lintable in lintables:
            if match.filename == lintable.filename:
                match.filename = lintable.name
                break

    return LintResult(matches=matches, files=checked_files)
