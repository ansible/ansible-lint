"""CLI parser setup and helpers."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ansiblelint.config import (
    DEFAULT_KINDS,
    DEFAULT_WARN_LIST,
    PROFILES,
    Options,
    log_entries,
)
from ansiblelint.constants import CUSTOM_RULESDIR_ENVVAR, DEFAULT_RULESDIR, EPILOG, RC
from ansiblelint.file_utils import (
    Lintable,
    abspath,
    expand_path_vars,
    find_project_root,
    normpath,
)
from ansiblelint.loaders import IGNORE_FILE
from ansiblelint.schemas.main import validate_file_schema
from ansiblelint.yaml_utils import clean_json

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


_logger = logging.getLogger(__name__)
_PATH_VARS = [
    "rulesdir",
]


def expand_to_normalized_paths(
    config: dict[str, Any],
    base_dir: str | None = None,
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


def load_config(config_file: str | None) -> tuple[dict[Any, Any], str | None]:
    """Load configuration from disk."""
    config_path = None

    if config_file == "/dev/null":
        _logger.debug("Skipping config file as it was set to /dev/null")
        return {}, config_file

    if config_file:
        config_path = os.path.abspath(config_file)
        if not os.path.exists(config_path):
            _logger.error("Config file not found '%s'", config_path)
            sys.exit(RC.INVALID_CONFIG)
    config_path = config_path or get_config_path()
    if not config_path or not os.path.exists(config_path):
        # a missing default config file should not trigger an error
        return {}, None

    config_lintable = Lintable(
        config_path,
        kind="ansible-lint-config",
        base_kind="text/yaml",
    )

    for error in validate_file_schema(config_lintable):
        _logger.error("Invalid configuration file %s. %s", config_path, error)
        sys.exit(RC.INVALID_CONFIG)

    config = clean_json(config_lintable.data)
    if not isinstance(config, dict):
        msg = "Schema failed to properly validate the config file."
        raise TypeError(msg)
    config["config_file"] = config_path
    config_dir = os.path.dirname(config_path)
    expand_to_normalized_paths(config, config_dir)

    return config, config_path


def get_config_path(config_file: str | None = None) -> str | None:
    """Return local config file."""
    if config_file:
        project_filenames = [config_file]
    else:
        project_filenames = [
            ".ansible-lint",
            ".config/ansible-lint.yml",
            ".config/ansible-lint.yaml",
        ]
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
        if isinstance(values, str | Path):
            values = [values]
        if values:
            normalized_values = [
                Path(expand_path_vars(str(path))).resolve() for path in values
            ]
            previous_values = getattr(namespace, self.dest, [])
            setattr(namespace, self.dest, previous_values + normalized_values)


class WriteArgAction(argparse.Action):
    """Argparse action to handle the --fix flag with optional args."""

    _default = "__default__"

    # noinspection PyShadowingBuiltins
    def __init__(  # pylint: disable=too-many-arguments,redefined-builtin
        self,
        option_strings: list[str],
        dest: str,
        nargs: int | str | None = None,
        const: Any = None,
        default: Any = None,
        type: Callable[[str], Any] | None = None,  # noqa: A002
        choices: list[Any] | None = None,
        *,
        required: bool = False,
        help: str | None = None,  # noqa: A002
        metavar: str | None = None,
    ) -> None:
        """Create the argparse action with WriteArg-specific defaults."""
        if nargs is not None:
            msg = "nargs for WriteArgAction must not be set."
            raise ValueError(msg)
        if const is not None:
            msg = "const for WriteArgAction must not be set."
            raise ValueError(msg)
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs="?",  # either 0 (--fix) or 1 (--fix=a,b,c) argument
            const=self._default,  # --fix (no option) implicitly stores this
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
            # If --fix is after lintables, then that is not ambiguous.
            # But if --fix comes first, then it might actually be a lintable.
            maybe_lintable = Path(values)
            if maybe_lintable.exists():
                namespace.lintables = [values]
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
    def merge_fix_list_config(
        cls,
        from_file: list[str],
        from_cli: list[str],
    ) -> list[str]:
        """Determine the write_list value based on cli vs config.

        When --fix is not passed from command line the from_cli is an empty list,
        so we use the file.

        When from_cli is not an empty list, we ignore the from_file value.
        """
        if not from_file:
            arguments = ["all"] if from_cli == [cls._default] else from_cli
        else:
            arguments = from_file
        for magic_value in ("none", "all"):
            if magic_value in arguments and len(arguments) > 1:
                msg = f"When passing '{magic_value}' to '--fix', you cannot pass other values."
                raise RuntimeError(
                    msg,
                )
        if len(arguments) == 1 and arguments[0] == "none":
            arguments = []
        return arguments


def get_cli_parser() -> argparse.ArgumentParser:
    """Initialize an argument parser."""
    parser = argparse.ArgumentParser(
        epilog=EPILOG,
        # Avoid rewrapping description and epilog
        formatter_class=argparse.RawTextHelpFormatter,
    )

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
        "for argument -f are supported: {brief, full, md} with 'brief' as default.",
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
        default=None,
        choices=[
            "brief",
            # "plain",
            "full",
            "md",
            "json",
            "codeclimate",
            "quiet",
            "pep8",
            "sarif",
        ],
        help="stdout formatting, json being an alias for codeclimate. (default: %(default)s)",
    )
    parser.add_argument(
        "--sarif-file",
        default=None,
        type=Path,
        help="SARIF output file",
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
        "--project-dir",
        dest="project_dir",
        default=None,
        help="Location of project/repository, autodetected based on location "
        "of configuration file.",
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
        "--fix",
        dest="write_list",
        # this is a tri-state argument that takes an optional comma separated list:
        action=WriteArgAction,
        help="Allow ansible-lint to perform auto-fixes, including YAML reformatting. "
        "You can limit the effective rule transforms (the 'write_list') by passing a "
        "keywords 'all' or 'none' or a comma separated list of rule ids or rule tags. "
        "YAML reformatting happens whenever '--fix' or '--fix=' is used. "
        "'--fix' and '--fix=all' are equivalent: they allow all transforms to run. "
        "Presence of --fix in command overrides config file value.",
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
        help="only check rules whose id/tags do not match these values. \
            e.g: --skip-list=name,run-once",
    )
    parser.add_argument(
        "--generate-ignore",
        dest="generate_ignore",
        action="store_true",
        default=False,
        help="Generate a text file '.ansible-lint-ignore' that ignores all found violations. Each line contains filename and rule id separated by a space.",
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
        action="extend",
        nargs="+",
        type=str,
        default=[],
        help="path to directories or files to skip. This option is repeatable.",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        dest="config_file",
        help="Specify configuration file to use. By default it will look for '.ansible-lint', '.config/ansible-lint.yml', or '.config/ansible-lint.yaml'",
    )
    parser.add_argument(
        "-i",
        "--ignore-file",
        dest="ignore_file",
        type=Path,
        default=None,
        help=f"Specify ignore file to use. By default it will look for '{IGNORE_FILE.default}' or '{IGNORE_FILE.alternative}'",
    )
    parser.add_argument(
        "--offline",
        dest="offline",
        action="store_const",
        const=True,
        help="Disable installation of requirements.yml and schema refreshing",
    )
    parser.add_argument(
        "--version",
        action="store_true",
    )
    parser.add_argument(
        dest="lintables",
        nargs="*",
        action="extend",
        help="One or more files or paths. When missing it will enable auto-detection mode.",
    )

    return parser


def merge_config(file_config: dict[Any, Any], cli_config: Options) -> Options:
    """Combine the file config with the CLI args."""
    bools = (
        "display_relative_path",
        "parseable",
        "quiet",
        "strict",
        "use_default_rules",
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
        "project_dir": None,
        "profile": None,
        "sarif_file": None,
    }

    if not file_config:
        # use defaults if we don't have a config file and the commandline
        # parameter is not set
        for entry, default in lists_map.items():
            if not getattr(cli_config, entry, None):
                setattr(cli_config, entry, default)
        if cli_config.write_list is None:
            cli_config.write_list = []
        elif cli_config.write_list == [WriteArgAction._default]:  # noqa: SLF001
            cli_config.write_list = ["all"]
        return cli_config

    for entry in bools:
        file_value = file_config.pop(entry, False)
        v = getattr(cli_config, entry) or file_value
        setattr(cli_config, entry, v)

    for entry, default_scalar in scalar_map.items():
        file_value = file_config.pop(entry, default_scalar)
        v = getattr(cli_config, entry, None) or file_value
        setattr(cli_config, entry, v)

    # if either commandline parameter or config file option is set merge
    # with the other, if neither is set use the default
    for entry, default in lists_map.items():
        if getattr(cli_config, entry, None) or entry in file_config:
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
        WriteArgAction.merge_fix_list_config(
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
    cli_config.kinds = kinds

    return cli_config


def get_config(arguments: list[str]) -> Options:
    """Extract the config based on given args."""
    parser = get_cli_parser()
    # translate deprecated options
    for i, value in enumerate(arguments):
        if arguments[i].startswith("--write"):
            arguments[i] = value.replace("--write", "--fix")
            _logger.warning(
                "Replaced deprecated '--write' option with '--fix', change you call to avoid future regressions when we remove old option.",
            )
    options = Options(**vars(parser.parse_args(arguments)))

    # docs is not document, being used for internal documentation building
    if options.list_rules and options.format not in [
        None,
        "brief",
        "full",
        "md",
    ]:
        parser.error(
            f"argument -f: invalid choice: '{options.format}'. "
            f"In combination with argument -L only 'brief', "
            f"'rich' or 'md' are supported with -f.",
        )

    # save info about custom config file, as options.config_file may be modified by merge_config
    file_config, options.config_file = load_config(options.config_file)
    config = merge_config(file_config, options)

    options.rulesdirs = get_rules_dirs(
        options.rulesdir,
        use_default=options.use_default_rules,
    )

    if not options.project_dir:
        project_dir, method = find_project_root(
            srcs=options.lintables,
            config_file=options.config_file,
        )
        options.project_dir = os.path.expanduser(normpath(project_dir))
        log_entries.append(
            (
                logging.INFO,
                f"Identified [filename]{project_dir}[/] as project root due [bold]{method}[/].",
            ),
        )

    if not options.project_dir or not os.path.exists(options.project_dir):
        msg = f"Failed to determine a valid project_dir: {options.project_dir}"
        raise RuntimeError(msg)

    # expand user home dir in exclude_paths
    options.exclude_paths = [
        os.path.expandvars(os.path.expanduser(p)) for p in options.exclude_paths
    ]

    # Compute final verbosity level by subtracting -q counter.
    options.verbosity -= options.quiet
    return config


def print_help(file: Any = sys.stdout) -> None:
    """Print help test to the given stream."""
    get_cli_parser().print_help(file=file)


def get_rules_dirs(rulesdir: list[Path], *, use_default: bool = True) -> list[Path]:
    """Return a list of rules dirs."""
    default_ruledirs = [DEFAULT_RULESDIR]
    default_custom_rulesdir = os.environ.get(
        CUSTOM_RULESDIR_ENVVAR,
        os.path.join(DEFAULT_RULESDIR, "custom"),
    )
    custom_ruledirs = sorted(
        str(x.resolve())
        for x in Path(default_custom_rulesdir).iterdir()
        if x.is_dir() and (x / "__init__.py").exists()
    )

    result: list[Any] = []
    if use_default:
        result = rulesdir + custom_ruledirs + default_ruledirs
    elif rulesdir:
        result = rulesdir
    else:
        result = custom_ruledirs + default_ruledirs
    return [Path(p) for p in result]
