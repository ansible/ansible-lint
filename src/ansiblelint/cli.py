"""CLI parser setup and helpers."""
from __future__ import annotations

import argparse
import logging
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Callable, Sequence

from ansiblelint.config import DEFAULT_KINDS, DEFAULT_WARN_LIST, PROFILES
from ansiblelint.constants import (
    CUSTOM_RULESDIR_ENVVAR,
    DEFAULT_RULESDIR,
    INVALID_CONFIG_RC,
)
from ansiblelint.file_utils import (
    abspath,
    expand_path_vars,
    guess_project_dir,
    normpath,
)
from ansiblelint.loaders import YAMLError, yaml_load_safe

_logger = logging.getLogger(__name__)
_PATH_VARS = [
    "exclude_paths",
    "rulesdir",
]


def expand_to_normalized_paths(
    config: dict[str, Any], base_dir: str | None = None
) -> None:
    """Mutate given config normalizing any path values in it."""
    # config can be None (-c /dev/null)
    if not config:
        return
    base_dir = base_dir or os.getcwd()
    for paths_var in _PATH_VARS:
        if paths_var not in config:
            continue  # Cause we don't want to add a variable not present

        normalized_paths = []
        for path in config.pop(paths_var):
            normalized_path = abspath(expand_path_vars(path), base_dir=base_dir)

            normalized_paths.append(normalized_path)

        config[paths_var] = normalized_paths


def load_config(config_file: str) -> dict[Any, Any]:
    """Load configuration from disk."""
    config_path = None
    if config_file:
        config_path = os.path.abspath(config_file)
        if not os.path.exists(config_path):
            _logger.error("Config file not found '%s'", config_path)
            sys.exit(INVALID_CONFIG_RC)
    config_path = config_path or get_config_path()
    if not config_path or not os.path.exists(config_path):
        # a missing default config file should not trigger an error
        return {}

    try:
        with open(config_path, encoding="utf-8") as stream:
            config = yaml_load_safe(stream)
            # We want to allow passing /dev/null to disable config use
            if config is None:
                return {}
            if not isinstance(config, dict):
                _logger.error("Invalid configuration file %s", config_path)
                sys.exit(INVALID_CONFIG_RC)
    except YAMLError as exc:
        _logger.error(exc)
        sys.exit(INVALID_CONFIG_RC)

    config["config_file"] = config_path
    # See https://github.com/ansible/ansible-lint/issues/1803
    if isinstance(config, list):
        _logger.error(
            "Invalid configuration '%s', expected YAML mapping in the config file.",
            config_path,
        )
        sys.exit(INVALID_CONFIG_RC)

    config_dir = os.path.dirname(config_path)
    expand_to_normalized_paths(config, config_dir)

    return config


def get_config_path(config_file: str | None = None) -> str | None:
    """Return local config file."""
    if config_file:
        project_filenames = [config_file]
    else:
        project_filenames = [".ansible-lint", ".config/ansible-lint.yml"]
    parent = tail = os.getcwd()
    while tail:
        for project_filename in project_filenames:
            filename = os.path.abspath(os.path.join(parent, project_filename))
            if os.path.exists(filename):
                return filename
        if os.path.exists(os.path.abspath(os.path.join(parent, ".git"))):
            # Avoid looking outside .git folders as we do not want end-up
            # picking config files from upper level projects if current
            # project has no config.
            return None
        (parent, tail) = os.path.split(parent)
    return None


class AbspathArgAction(argparse.Action):
    """Argparse action to convert relative paths to absolute paths."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        if isinstance(values, (str, Path)):
            values = [values]
        if values:
            normalized_values = [
                Path(expand_path_vars(str(path))).resolve() for path in values
            ]
            previous_values = getattr(namespace, self.dest, [])
            setattr(namespace, self.dest, previous_values + normalized_values)


class WriteArgAction(argparse.Action):
    """Argparse action to handle the --write flag with optional args."""

    _default = "__default__"

    # noinspection PyShadowingBuiltins
    def __init__(  # pylint: disable=too-many-arguments,redefined-builtin
        self,
        option_strings: list[str],
        dest: str,
        nargs: int | str | None = None,
        const: Any = None,
        default: Any = None,
        type: Callable[[str], Any] | None = None,
        choices: list[Any] | None = None,
        required: bool = False,
        help: str | None = None,
        metavar: str | None = None,
    ) -> None:
        """Create the argparse action with WriteArg-specific defaults."""
        if nargs is not None:
            raise ValueError("nargs for WriteArgAction must not be set.")
        if const is not None:
            raise ValueError("const for WriteArgAction must not be set.")
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs="?",  # either 0 (--write) or 1 (--write=a,b,c) argument
            const=self._default,  # --write (no option) implicitly stores this
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
        )

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        lintables = getattr(namespace, "lintables", None)
        if not lintables and isinstance(values, str):
            # args are processed in order.
            # If --write is after lintables, then that is not ambiguous.
            # But if --write comes first, then it might actually be a lintable.
            maybe_lintable = Path(values)
            if maybe_lintable.exists():
                setattr(namespace, "lintables", [values])
                values = []
        if isinstance(values, str):
            values = values.split(",")
        default = [self.const] if isinstance(self.const, str) else self.const
        previous_values = getattr(namespace, self.dest, default) or default
        if not values:
            values = previous_values
        elif previous_values != default:
            values = previous_values + values
        setattr(namespace, self.dest, values)

    @classmethod
    def merge_write_list_config(
        cls, from_file: list[str], from_cli: list[str]
    ) -> list[str]:
        """Combine the write_list from file config with --write CLI arg.

        Handles the implicit "all" when "__default__" is present and file config is empty.
        """
        if not from_file or "none" in from_cli:
            # --write is the same as --write=all
            return ["all" if value == cls._default else value for value in from_cli]
        # --write means use the config from the config file
        from_cli = [value for value in from_cli if value != cls._default]
        return from_file + from_cli


def get_cli_parser() -> argparse.ArgumentParser:
    """Initialize an argument parser."""
    parser = argparse.ArgumentParser()

    listing_group = parser.add_mutually_exclusive_group()
    listing_group.add_argument(
        "-P",
        "--list-profiles",
        dest="list_profiles",
        default=False,
        action="store_true",
        help="List all profiles, no formatting options available.",
    )
    listing_group.add_argument(
        "-L",
        "--list-rules",
        dest="list_rules",
        default=False,
        action="store_true",
        help="List all the rules. For listing rules only the following formats "
        "for argument -f are supported: {plain, rich, md}",
    )
    listing_group.add_argument(
        "-T",
        "--list-tags",
        dest="list_tags",
        action="store_true",
        help="List all the tags and the rules they cover. Increase the verbosity level "
        "with `-v` to include 'opt-in' tag and its rules.",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        default="rich",
        choices=[
            "rich",
            "plain",
            "md",
            "json",
            "codeclimate",
            "quiet",
            "pep8",
            "sarif",
            "docs",  # internally used
        ],
        help="stdout formatting, json being an alias for codeclimate. (default: %(default)s)",
    )
    parser.add_argument(
        "-q",
        dest="quiet",
        default=0,
        action="count",
        help="quieter, reduce verbosity, can be specified twice.",
    )
    parser.add_argument(
        "--profile",
        dest="profile",
        default=None,
        action="store",
        choices=PROFILES.keys(),
        help="Specify which rules profile to be used.",
    )
    parser.add_argument(
        "-p",
        "--parseable",
        dest="parseable",
        default=False,
        action="store_true",
        help="parseable output, same as '-f pep8'",
    )
    parser.add_argument(
        "--progressive",
        dest="progressive",
        default=False,
        action="store_true",
        help="Return success if number of violations compared with"
        "previous git commit has not increased. This feature works"
        "only in git repositories.",
    )
    parser.add_argument(
        "--project-dir",
        dest="project_dir",
        default=".",
        help="Location of project/repository, autodetected based on location "
        " of configuration file.",
    )
    parser.add_argument(
        "-r",
        "--rules-dir",
        action=AbspathArgAction,
        dest="rulesdir",
        default=[],
        type=Path,
        help="Specify custom rule directories. Add -R "
        f"to keep using embedded rules from {DEFAULT_RULESDIR}",
    )
    parser.add_argument(
        "-R",
        action="store_true",
        default=False,
        dest="use_default_rules",
        help="Keep default rules when using -r",
    )
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        default=False,
        dest="strict",
        help="Return non-zero exit code on warnings as well as errors",
    )
    parser.add_argument(
        "--write",
        dest="write_list",
        # this is a tri-state argument that takes an optional comma separated list:
        #   not provided, --write, --write=a,b,c
        action=WriteArgAction,
        help="Allow ansible-lint to reformat YAML files and run rule transforms "
        "(Reformatting YAML files standardizes spacing, quotes, etc. "
        "A rule transform can fix or simplify fixing issues identified by that rule). "
        "You can limit the effective rule transforms (the 'write_list') by passing a "
        "keywords 'all' or 'none' or a comma separated list of rule ids or rule tags. "
        "YAML reformatting happens whenever '--write' or '--write=' is used. "
        "'--write' and '--write=all' are equivalent: they allow all transforms to run. "
        "The effective list of transforms comes from 'write_list' in the config file, "
        "followed whatever '--write' args are provided on the commandline. "
        "'--write=none' resets the list of transforms to allow reformatting YAML "
        "without running any of the transforms (ie '--write=none,rule-id' will "
        "ignore write_list in the config file and only run the rule-id transform).",
    )
    parser.add_argument(
        "--show-relpath",
        dest="display_relative_path",
        action="store_false",
        default=True,
        help="Display path relative to CWD",
    )
    parser.add_argument(
        "-t",
        "--tags",
        dest="tags",
        action="append",
        default=[],
        help="only check rules whose id/tags match these values",
    )
    parser.add_argument(
        "-v",
        dest="verbosity",
        action="count",
        help="Increase verbosity level (-vv for more)",
        default=0,
    )
    parser.add_argument(
        "-x",
        "--skip-list",
        dest="skip_list",
        default=[],
        action="append",
        help="only check rules whose id/tags do not " "match these values",
    )
    parser.add_argument(
        "-w",
        "--warn-list",
        dest="warn_list",
        default=[],
        action="append",
        help="only warn about these rules, unless overridden in "
        f"config file. Current version default value is: {', '.join(DEFAULT_WARN_LIST)}",
    )
    parser.add_argument(
        "--enable-list",
        dest="enable_list",
        default=[],
        action="append",
        help="activate optional rules by their tag name",
    )
    # Do not use store_true/store_false because they create opposite defaults.
    parser.add_argument(
        "--nocolor",
        dest="colored",
        action="store_const",
        const=False,
        help="disable colored output, same as NO_COLOR=1",
    )
    parser.add_argument(
        "--force-color",
        dest="colored",
        action="store_const",
        const=True,
        help="Force colored output, same as FORCE_COLOR=1",
    )
    parser.add_argument(
        "--exclude",
        dest="exclude_paths",
        action=AbspathArgAction,
        type=Path,
        default=[],
        help="path to directories or files to skip. " "This option is repeatable.",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        dest="config_file",
        help="Specify configuration file to use. By default it will look for '.ansible-lint' or '.config/ansible-lint.yml'",
    )
    parser.add_argument(
        "--offline",
        dest="offline",
        action="store_const",
        const=True,
        help="Disable installation of requirements.yml",
    )
    parser.add_argument(
        "--version",
        action="store_true",
    )
    parser.add_argument(
        dest="lintables",
        nargs="*",
        action="extend",
        help="One or more files or paths. When missing it will "
        " enable auto-detection mode.",
    )

    return parser


def merge_config(file_config: dict[Any, Any], cli_config: Namespace) -> Namespace:
    """Combine the file config with the CLI args."""
    bools = (
        "display_relative_path",
        "parseable",
        "quiet",
        "strict",
        "use_default_rules",
        "progressive",
        "offline",
    )
    # maps lists to their default config values
    lists_map = {
        "exclude_paths": [".cache", ".git", ".hg", ".svn", ".tox"],
        "rulesdir": [],
        "skip_list": [],
        "tags": [],
        "warn_list": DEFAULT_WARN_LIST,
        "mock_modules": [],
        "mock_roles": [],
        "enable_list": [],
        "only_builtins_allow_collections": [],
        "only_builtins_allow_modules": [],
        # do not include "write_list" here. See special logic below.
    }

    scalar_map = {
        "loop_var_prefix": None,
        "project_dir": ".",
        "profile": None,
    }

    if not file_config:
        # use defaults if we don't have a config file and the commandline
        # parameter is not set
        for entry, default in lists_map.items():
            if not getattr(cli_config, entry, None):
                setattr(cli_config, entry, default)
        return cli_config

    for entry in bools:
        file_value = file_config.pop(entry, False)
        v = getattr(cli_config, entry) or file_value
        setattr(cli_config, entry, v)

    for entry, default in scalar_map.items():
        file_value = file_config.pop(entry, default)
        v = getattr(cli_config, entry, None) or file_value
        setattr(cli_config, entry, v)

    # if either commandline parameter or config file option is set merge
    # with the other, if neither is set use the default
    for entry, default in lists_map.items():
        if getattr(cli_config, entry, None) or entry in file_config.keys():
            value = getattr(cli_config, entry, [])
            value.extend(file_config.pop(entry, []))
        else:
            value = default
        setattr(cli_config, entry, value)

    # "write_list" config has special merge rules
    entry = "write_list"
    setattr(
        cli_config,
        entry,
        WriteArgAction.merge_write_list_config(
            from_file=file_config.pop(entry, []),
            from_cli=getattr(cli_config, entry, []) or [],
        ),
    )

    if "verbosity" in file_config:
        cli_config.verbosity = cli_config.verbosity + file_config.pop("verbosity")

    # merge options that can be set only via a file config
    for entry, value in file_config.items():
        setattr(cli_config, entry, value)

    # append default kinds to the custom list
    kinds = file_config.get("kinds", [])
    kinds.extend(DEFAULT_KINDS)
    setattr(cli_config, "kinds", kinds)

    return cli_config


def get_config(arguments: list[str]) -> Namespace:
    """Extract the config based on given args."""
    parser = get_cli_parser()
    options = parser.parse_args(arguments)

    # docs is not document, being used for internal documentation building
    if options.list_rules and options.format not in ["plain", "rich", "md", "docs"]:
        parser.error(
            f"argument -f: invalid choice: '{options.format}'. "
            f"In combination with argument -L only 'plain', "
            f"'rich' or 'md' are supported with -f."
        )

    # save info about custom config file, as options.config_file may be modified by merge_config
    has_custom_config = not options.config_file

    file_config = load_config(options.config_file)

    config = merge_config(file_config, options)

    options.rulesdirs = get_rules_dirs(options.rulesdir, options.use_default_rules)

    if has_custom_config and options.project_dir == ".":
        project_dir = guess_project_dir(options.config_file)
        options.project_dir = os.path.expanduser(normpath(project_dir))

    if not options.project_dir or not os.path.exists(options.project_dir):
        raise RuntimeError(
            f"Failed to determine a valid project_dir: {options.project_dir}"
        )

    # Compute final verbosity level by subtracting -q counter.
    options.verbosity -= options.quiet
    return config


def print_help(file: Any = sys.stdout) -> None:
    """Print help test to the given stream."""
    get_cli_parser().print_help(file=file)


def get_rules_dirs(rulesdir: list[str], use_default: bool = True) -> list[str]:
    """Return a list of rules dirs."""
    default_ruledirs = [DEFAULT_RULESDIR]
    default_custom_rulesdir = os.environ.get(
        CUSTOM_RULESDIR_ENVVAR, os.path.join(DEFAULT_RULESDIR, "custom")
    )
    custom_ruledirs = sorted(
        str(x.resolve())
        for x in Path(default_custom_rulesdir).iterdir()
        if x.is_dir() and (x / "__init__.py").exists()
    )

    if use_default:
        return rulesdir + custom_ruledirs + default_ruledirs

    return rulesdir or custom_ruledirs + default_ruledirs
