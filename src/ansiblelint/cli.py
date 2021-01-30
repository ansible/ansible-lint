# -*- coding: utf-8 -*-
"""CLI parser setup and helpers."""
import argparse
import logging
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ansiblelint.constants import CUSTOM_RULESDIR_ENVVAR, DEFAULT_RULESDIR, INVALID_CONFIG_RC
from ansiblelint.file_utils import expand_path_vars

_logger = logging.getLogger(__name__)
_PATH_VARS = ['exclude_paths', 'rulesdir', ]


def abspath(path: str, base_dir: str) -> str:
    """Make relative path absolute relative to given directory.

    Args:
       path (str): the path to make absolute
       base_dir (str): the directory from which make relative paths
           absolute
       default_drive: Windows drive to use to make the path
           absolute if none is given.
    """
    if not os.path.isabs(path):
        # Don't use abspath as it assumes path is relative to cwd.
        # We want it relative to base_dir.
        path = os.path.join(base_dir, path)

    return os.path.normpath(path)


def expand_to_normalized_paths(config: dict, base_dir: str = None) -> None:
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


def load_config(config_file: str) -> Dict[Any, Any]:
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
        with open(config_path, "r") as stream:
            config = yaml.safe_load(stream)
            if not isinstance(config, dict):
                _logger.error("Invalid configuration file %s", config_path)
                sys.exit(INVALID_CONFIG_RC)
    except yaml.YAMLError as e:
        _logger.error(e)
        sys.exit(INVALID_CONFIG_RC)
    # TODO(ssbarnea): implement schema validation for config file
    if isinstance(config, list):
        _logger.error(
            "Invalid configuration '%s', expected YAML mapping in the config file.",
            config_path)
        sys.exit(INVALID_CONFIG_RC)

    config_dir = os.path.dirname(config_path)
    expand_to_normalized_paths(config, config_dir)
    return config


def get_config_path(config_file: str = '.ansible-lint') -> Optional[str]:
    """Return local config file."""
    project_filenames = [config_file]
    parent = tail = os.getcwd()
    while tail:
        for project_filename in project_filenames:
            filename = os.path.abspath(
                os.path.join(parent, project_filename)
            )
            if os.path.exists(filename):
                return filename
        (parent, tail) = os.path.split(parent)
    return None


class AbspathArgAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, (str, Path)):
            values = [values]
        normalized_values = [Path(expand_path_vars(path)).resolve() for path in values]
        previous_values = getattr(namespace, self.dest, [])
        setattr(namespace, self.dest, previous_values + normalized_values)


def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument('-L', dest='listrules', default=False,
                        action='store_true', help="list all the rules")
    parser.add_argument('-f', dest='format', default='rich',
                        choices=['rich', 'plain', 'rst'],
                        help="Format used rules output, (default: %(default)s)")
    parser.add_argument('-q', dest='quiet',
                        default=False,
                        action='store_true',
                        help="quieter, although not silent output")
    parser.add_argument('-p', dest='parseable',
                        default=False,
                        action='store_true',
                        help="parseable output in the format of pep8")
    parser.add_argument('--parseable-severity', dest='parseable_severity',
                        default=False,
                        action='store_true',
                        help="parseable output including severity of rule")
    parser.add_argument('--progressive', dest='progressive',
                        default=False,
                        action='store_true',
                        help="Return success if it detects a reduction in number"
                        " of violations compared with previous git commit. This "
                        "feature works only in git repositories.")
    parser.add_argument('-r', action=AbspathArgAction, dest='rulesdir',
                        default=[], type=Path,
                        help="Specify custom rule directories. Add -R "
                             f"to keep using embedded rules from {DEFAULT_RULESDIR}")
    parser.add_argument('-R', action='store_true',
                        default=False,
                        dest='use_default_rules',
                        help="Keep default rules when using -r")
    parser.add_argument('--show-relpath', dest='display_relative_path', action='store_false',
                        default=True,
                        help="Display path relative to CWD")
    parser.add_argument('-t', dest='tags',
                        action='append',
                        default=[],
                        help="only check rules whose id/tags match these values")
    parser.add_argument('-T', dest='listtags', action='store_true',
                        help="list all the tags")
    parser.add_argument('-v', dest='verbosity', action='count',
                        help="Increase verbosity level",
                        default=0)
    parser.add_argument('-x', dest='skip_list', default=[], action='append',
                        help="only check rules whose id/tags do not "
                        "match these values")
    parser.add_argument('-w', dest='warn_list', default=[], action='append',
                        help="only warn about these rules, unless overridden in "
                             "config file defaults to 'experimental'")
    # Do not use store_true/store_false because they create opposite defaults.
    parser.add_argument('--nocolor', dest='colored',
                        action='store_const',
                        const=False,
                        help="disable colored output, same as NO_COLOR=1")
    parser.add_argument('--force-color', dest='colored',
                        action='store_const',
                        const=True,
                        help="Force colored output, same as FORCE_COLOR=1")
    parser.add_argument('--exclude', dest='exclude_paths',
                        action=AbspathArgAction,
                        type=Path, default=[],
                        help='path to directories or files to skip. '
                             'This option is repeatable.',
                        )
    parser.add_argument('-c', dest='config_file',
                        help='Specify configuration file to use.  '
                             'Defaults to ".ansible-lint"')
    parser.add_argument('--version',
                        action='store_true',
                        )
    parser.add_argument(dest='lintables', nargs='*',
                        help="One or more files or paths. When missing it will "
                        " enable auto-detection mode.")

    return parser


def merge_config(file_config, cli_config: Namespace) -> Namespace:
    bools = (
        'display_relative_path',
        'parseable',
        'parseable_severity',
        'quiet',
        'use_default_rules',
        'progressive',
    )
    # maps lists to their default config values
    lists_map = {
        'exclude_paths': [],
        'rulesdir': [],
        'skip_list': [],
        'tags': [],
        'warn_list': ['experimental'],
        'mock_modules': []
    }

    if not file_config:
        # use defaults if we don't have a config file and the commandline
        # parameter is not set
        for entry, default in lists_map.items():
            if not getattr(cli_config, entry, None):
                setattr(cli_config, entry, default)
        return cli_config

    for entry in bools:
        x = getattr(cli_config, entry) or file_config.get(entry, False)
        setattr(cli_config, entry, x)

    # if either commandline parameter or config file option is set merge
    # with the other, if neither is set use the default
    for entry, default in lists_map.items():
        if getattr(cli_config, entry, None) or entry in file_config.keys():
            value = getattr(cli_config, entry, [])
            value.extend(file_config.get(entry, []))
        else:
            value = default
        setattr(cli_config, entry, value)

    if 'verbosity' in file_config:
        cli_config.verbosity = (cli_config.verbosity +
                                file_config['verbosity'])

    return cli_config


def get_config(arguments: List[str]) -> Namespace:
    parser = get_cli_parser()
    options = parser.parse_args(arguments)

    file_config = load_config(options.config_file)

    config = merge_config(file_config, options)

    options.rulesdirs = get_rules_dirs(
        options.rulesdir,
        options.use_default_rules)

    return config


def print_help(file=sys.stdout):
    get_cli_parser().print_help(file=file)


def get_rules_dirs(rulesdir: List[str], use_default: bool = True) -> List[str]:
    """Return a list of rules dirs."""
    default_ruledirs = [DEFAULT_RULESDIR]
    default_custom_rulesdir = os.environ.get(
        CUSTOM_RULESDIR_ENVVAR, os.path.join(DEFAULT_RULESDIR, "custom")
    )
    custom_ruledirs = sorted(
        str(rdir.resolve())
        for rdir in Path(default_custom_rulesdir).iterdir()
        if rdir.is_dir() and (rdir / "__init__.py").exists()
    )

    if use_default:
        return rulesdir + custom_ruledirs + default_ruledirs

    return rulesdir or custom_ruledirs + default_ruledirs
