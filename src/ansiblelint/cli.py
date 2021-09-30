# -*- coding: utf-8 -*-
"""CLI parser setup and helpers."""
import argparse
import logging
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import yaml

from ansiblelint.config import DEFAULT_KINDS
from ansiblelint.constants import (
    CUSTOM_RULESDIR_ENVVAR,
    DEFAULT_RULESDIR,
    INVALID_CONFIG_RC,
)
from ansiblelint.file_utils import expand_path_vars, guess_project_dir, normpath

_logger = logging.getLogger(__name__)
_PATH_VARS = [
    'exclude_paths',
    'rulesdir',
]


def abspath(path: str, base_dir: str) -> str:
    """Make relative path absolute relative to given directory.

    Args:
       path (str): the path to make absolute
       base_dir (str): the directory from which make \
                       relative paths absolute
    """
    if not os.path.isabs(path):
        # Don't use abspath as it assumes path is relative to cwd.
        # We want it relative to base_dir.
        path = os.path.join(base_dir, path)

    return os.path.normpath(path)


def expand_to_normalized_paths(
    config: Dict[str, Any], base_dir: Optional[str] = None
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

    config['config_file'] = config_path
    # TODO(ssbarnea): implement schema validation for config file
    if isinstance(config, list):
        _logger.error(
            "Invalid configuration '%s', expected YAML mapping in the config file.",
            config_path,
        )
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
            filename = os.path.abspath(os.path.join(parent, project_filename))
            if os.path.exists(filename):
                return filename
            if os.path.exists(os.path.abspath(os.path.join(parent, '.git'))):
                # Avoid looking outside .git folders as we do not want endup
                # picking config files from upper level projects if current
                # project has no config.
                return None
        (parent, tail) = os.path.split(parent)
    return None


class AbspathArgAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        if isinstance(values, (str, Path)):
            values = [values]
        if values:
            normalized_values = [
                Path(expand_path_vars(str(path))).resolve() for path in values
            ]
            previous_values = getattr(namespace, self.dest, [])
            setattr(namespace, self.dest, previous_values + normalized_values)


def get_cli_parser() -> argparse.ArgumentParser:
    """Initialize an argument parser."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-L',
        dest='listrules',
        default=False,
        action='store_true',
        help="list all the rules",
    )
    parser.add_argument(
        '-f',
        dest='format',
        default='rich',
        choices=['rich', 'plain', 'rst', 'codeclimate', 'quiet', 'pep8'],
        help="Format used rules output, (default: %(default)s)",
    )
    parser.add_argument(
        '-q',
        dest='quiet',
        default=0,
        action='count',
        help="quieter, reduce verbosity, can be specified twice.",
    )
    parser.add_argument(
        '-p',
        dest='parseable',
        default=False,
        action='store_true',
        help="parseable output, same as '-f pep8'",
    )
    parser.add_argument(
        '--parseable-severity',
        dest='parseable_severity',
        default=False,
        action='store_true',
        help="parseable output including severity of rule",
    )
    parser.add_argument(
        '--progressive',
        dest='progressive',
        default=False,
        action='store_true',
        help="Return success if it detects a reduction in number"
        " of violations compared with previous git commit. This "
        "feature works only in git repositories.",
    )
    parser.add_argument(
        '--project-dir',
        dest='project_dir',
        default=".",
        help="Location of project/repository, autodetected based on location "
        " of configuration file.",
    )
    parser.add_argument(
        '-r',
        action=AbspathArgAction,
        dest='rulesdir',
        default=[],
        type=Path,
        help="Specify custom rule directories. Add -R "
        f"to keep using embedded rules from {DEFAULT_RULESDIR}",
    )
    parser.add_argument(
        '-R',
        action='store_true',
        default=False,
        dest='use_default_rules',
        help="Keep default rules when using -r",
    )
    parser.add_argument(
        '--show-relpath',
        dest='display_relative_path',
        action='store_false',
        default=True,
        help="Display path relative to CWD",
    )
    parser.add_argument(
        '-t',
        dest='tags',
        action='append',
        default=[],
        help="only check rules whose id/tags match these values",
    )
    parser.add_argument(
        '-T', dest='listtags', action='store_true', help="list all the tags"
    )
    parser.add_argument(
        '-v',
        dest='verbosity',
        action='count',
        help="Increase verbosity level (-vv for more)",
        default=0,
    )
    parser.add_argument(
        '-x',
        dest='skip_list',
        default=[],
        action='append',
        help="only check rules whose id/tags do not " "match these values",
    )
    parser.add_argument(
        '-w',
        dest='warn_list',
        default=[],
        action='append',
        help="only warn about these rules, unless overridden in "
        "config file defaults to 'experimental'",
    )
    parser.add_argument(
        '--enable-list',
        dest='enable_list',
        default=[],
        action='append',
        help="activate optional rules by their tag name",
    )
    # Do not use store_true/store_false because they create opposite defaults.
    parser.add_argument(
        '--nocolor',
        dest='colored',
        action='store_const',
        const=False,
        help="disable colored output, same as NO_COLOR=1",
    )
    parser.add_argument(
        '--force-color',
        dest='colored',
        action='store_const',
        const=True,
        help="Force colored output, same as FORCE_COLOR=1",
    )
    parser.add_argument(
        '--exclude',
        dest='exclude_paths',
        action=AbspathArgAction,
        type=Path,
        default=[],
        help='path to directories or files to skip. ' 'This option is repeatable.',
    )
    parser.add_argument(
        '-c',
        dest='config_file',
        help='Specify configuration file to use.  ' 'Defaults to ".ansible-lint"',
    )
    parser.add_argument(
        '--offline',
        dest='offline',
        action='store_const',
        const=True,
        help='Disable installation of requirements.yml',
    )
    parser.add_argument(
        '--version',
        action='store_true',
    )
    parser.add_argument(
        dest='lintables',
        nargs='*',
        help="One or more files or paths. When missing it will "
        " enable auto-detection mode.",
    )

    return parser


def merge_config(file_config: Dict[Any, Any], cli_config: Namespace) -> Namespace:
    """Combine the file config with the CLI args."""
    bools = (
        'display_relative_path',
        'parseable',
        'parseable_severity',
        'quiet',
        'use_default_rules',
        'progressive',
        'offline',
    )
    # maps lists to their default config values
    lists_map = {
        'exclude_paths': [".cache", ".git", ".hg", ".svn", ".tox"],
        'rulesdir': [],
        'skip_list': [],
        'tags': [],
        'warn_list': ['experimental', 'role-name'],
        'mock_modules': [],
        'mock_roles': [],
        'enable_list': [],
    }

    scalar_map = {
        "loop_var_prefix": None,
        "project_dir": ".",
    }

    if not file_config:
        # use defaults if we don't have a config file and the commandline
        # parameter is not set
        for entry, default in lists_map.items():
            if not getattr(cli_config, entry, None):
                setattr(cli_config, entry, default)
        return cli_config

    for entry in bools:
        x = getattr(cli_config, entry) or file_config.pop(entry, False)
        setattr(cli_config, entry, x)

    for entry, default in scalar_map.items():
        x = getattr(cli_config, entry, None) or file_config.pop(entry, default)
        setattr(cli_config, entry, x)

    # if either commandline parameter or config file option is set merge
    # with the other, if neither is set use the default
    for entry, default in lists_map.items():
        if getattr(cli_config, entry, None) or entry in file_config.keys():
            value = getattr(cli_config, entry, [])
            value.extend(file_config.pop(entry, []))
        else:
            value = default
        setattr(cli_config, entry, value)

    if 'verbosity' in file_config:
        cli_config.verbosity = cli_config.verbosity + file_config.pop('verbosity')

    # merge options that can be set only via a file config
    for entry, value in file_config.items():
        setattr(cli_config, entry, value)

    # append default kinds to the custom list
    kinds = file_config.get('kinds', [])
    kinds.extend(DEFAULT_KINDS)
    setattr(cli_config, 'kinds', kinds)

    return cli_config


def get_config(arguments: List[str]) -> Namespace:
    """Extract the config based on given args."""
    parser = get_cli_parser()
    options = parser.parse_args(arguments)

    file_config = load_config(options.config_file)

    config = merge_config(file_config, options)

    options.rulesdirs = get_rules_dirs(options.rulesdir, options.use_default_rules)

    if options.project_dir == ".":
        project_dir = guess_project_dir(options.config_file)
        options.project_dir = normpath(project_dir)
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
