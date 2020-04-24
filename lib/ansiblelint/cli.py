# -*- coding: utf-8 -*-
import argparse
import os
from pathlib import Path
import sys

import yaml

import ansiblelint
from ansiblelint.version import __version__


_PATH_VARS = ['exclude_paths', 'rulesdir', ]
INVALID_CONFIG_RC = 2


def abspath(path, base_dir):
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


def expand_to_normalized_paths(config, base_dir=None):
    base_dir = base_dir or os.getcwd()
    for paths_var in _PATH_VARS:
        if paths_var not in config:
            continue  # Cause we don't want to add a variable not present

        normalized_paths = []
        for path in config.pop(paths_var):
            normalized_path = abspath(path, base_dir=base_dir)

            normalized_paths.append(normalized_path)

        config[paths_var] = normalized_paths


def load_config(config_file):
    config_path = os.path.abspath(config_file or '.ansible-lint')

    if config_file:
        if not os.path.exists(config_path):
            print(
                "Config file not found '{cfg!s}'.".format(cfg=config_path),
                file=sys.stderr,
            )
            sys.exit(INVALID_CONFIG_RC)
    elif not os.path.exists(config_path):
        # a missing default config file should not trigger an error
        return

    try:
        with open(config_path, "r") as stream:
            config = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        print(e, file=sys.stderr)
        sys.exit(INVALID_CONFIG_RC)
    # TODO(ssbarnea): implement schema validation for config file
    if isinstance(config, list):
        print(
            "Invalid configuration '{cfg!s}', expected YAML mapping in the config file.".
            format(cfg=config_path),
            file=sys.stderr,
        )
        sys.exit(INVALID_CONFIG_RC)

    config_dir = os.path.dirname(config_path)
    expand_to_normalized_paths(config, config_dir)
    return config


class AbspathArgAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, (str, Path)):
            values = [values]
        normalized_values = [Path(path).resolve() for path in values]
        previous_values = getattr(namespace, self.dest, [])
        setattr(namespace, self.dest, previous_values + normalized_values)


def get_cli_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-L', dest='listrules', default=False,
                        action='store_true', help="list all the rules")
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
    parser.add_argument('-r', action=AbspathArgAction, dest='rulesdir',
                        default=[], type=Path,
                        help="specify one or more rules directories using "
                             "one or more -r arguments. Any -r flags override "
                             "the default rules in %s, unless -R is also used."
                             % ansiblelint.default_rulesdir)
    parser.add_argument('-R', action='store_true',
                        default=False,
                        dest='use_default_rules',
                        help="Use default rules in %s in addition to any extra "
                             "rules directories specified with -r. There is "
                             "no need to specify this if no -r flags are used"
                             % ansiblelint.default_rulesdir)
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
    parser.add_argument('--nocolor', dest='colored',
                        default=hasattr(sys.stdout, 'isatty') and sys.stdout.isatty(),
                        action='store_false',
                        help="disable colored output")
    parser.add_argument('--force-color', dest='colored',
                        action='store_true',
                        help="Try force colored output (relying on ansible's code)")
    parser.add_argument('--exclude', dest='exclude_paths',
                        action=AbspathArgAction,
                        type=Path, default=[],
                        help='path to directories or files to skip. '
                             'This option is repeatable.',
                        )
    parser.add_argument('-c', dest='config_file',
                        help='Specify configuration file to use.  '
                             'Defaults to ".ansible-lint"')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {ver!s}'.format(ver=__version__),
                        )
    parser.add_argument('playbook', nargs='*')

    return parser


def merge_config(file_config, cli_config):
    if not file_config:
        return cli_config

    if 'quiet' in file_config:
        cli_config.quiet = cli_config.quiet or file_config['quiet']

    if 'parseable' in file_config:
        cli_config.parseable = (cli_config.parseable or
                                file_config['parseable'])

    if 'parseable_severity' in file_config:
        cli_config.parseable_severity = (cli_config.parseable_severity or
                                         file_config['parseable_severity'])

    if 'display_relative_path' in file_config:
        cli_config.display_relative_path = (cli_config.display_relative_path or
                                            file_config['display_relative_path'])

    if 'use_default_rules' in file_config:
        cli_config.use_default_rules = (cli_config.use_default_rules or
                                        file_config['use_default_rules'])

    if 'verbosity' in file_config:
        cli_config.verbosity = (cli_config.verbosity +
                                file_config['verbosity'])

    cli_config.exclude_paths.extend(file_config.get('exclude_paths', []))

    cli_config.rulesdir.extend(file_config.get('rulesdir', []))

    if 'skip_list' in file_config:
        cli_config.skip_list = cli_config.skip_list + file_config['skip_list']

    if 'tags' in file_config:
        cli_config.tags = cli_config.tags + file_config['tags']

    return cli_config


def get_config(arguments):
    parser = get_cli_parser()
    options = parser.parse_args(arguments)

    config = load_config(options.config_file)

    return merge_config(config, options)


def print_help(file=sys.stdout):
    get_cli_parser().print_help(file=file)


# vim: et:sw=4:syntax=python:ts=4:
