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

import collections
from contextlib import contextmanager
import errno
import logging
import pathlib
import os
import sys
import tempfile
from ansiblelint import cli, default_rulesdir
from ansiblelint.generate_docs import rules_as_rst
from typing import Any, Set


_logger = logging.getLogger(__name__)

MODULE_STUB = """
# This is a fake module used to make ansible(-lint) happy
from ansible.module_utils.basic import AnsibleModule


def main():
    return AnsibleModule(
        argument_spec=dict(
            data=dict(default=None),
            path=dict(default=None, type=str),
            file=dict(default=None, type=str),
        )
    )
"""


def initialize_logger(level: int = 0) -> None:
    """Set up the global logging level based on the verbosity number."""
    VERBOSITY_MAP = {
        0: logging.NOTSET,
        1: logging.INFO,
        2: logging.DEBUG
    }

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger(__package__)
    logger.addHandler(handler)
    # Unknown logging level is treated as DEBUG
    logging_level = VERBOSITY_MAP.get(level, logging.DEBUG)
    logger.setLevel(logging_level)
    # Use module-level _logger instance to validate it
    _logger.debug("Logging initialized to level %s", logging_level)


@contextmanager
def bootstrap_ansible(options):
    """Perform Ansible boostraping steps to add custom module paths.

    * Alter ANSIBLE_LIBRARY to inject custom paths before ansible modules are
    loaded. See https://github.com/ansible/ansible/issues/69758
    """
    BootstrapContext = collections.namedtuple(
        'BootstrapContext',
        'change_module_path tmp_dir')
    changed_module_path = False
    tmp_dir = None

    lib_paths = os.environ.get(
        'ANSIBLE_LIBRARY',
        "~/.ansible/plugins/modules:/usr/share/ansible/plugins/modules").split(":")
    # add plugins/modules to module paths if it exists
    p = pathlib.Path.cwd() / "plugins" / "modules"
    if p.exists() and str(p) not in lib_paths:
        _logger.info(f"Adding {str(p)} to module path")
        lib_paths.append(str(p))
        changed_module_path = True

    if options.stub_modules:
        # creates temporary directory for stub modules (auto-cleaned)
        tmp_dir = tempfile.TemporaryDirectory()
        lib_paths.append(tmp_dir.name)
        _logger.info(f"Adding {tmp_dir.name} to module path")
        changed_module_path = True

        for m in options.stub_modules:
            with (pathlib.Path(tmp_dir.name) / f"{m}.py") as f:
                _logger.debug(f"Generating fake module stub: {f.name}")
                f.write_text(MODULE_STUB)

    if changed_module_path:
        os.environ['ANSIBLE_LIBRARY'] = ":".join(lib_paths)
        _logger.info(f"Altered module path ANSIBLE_LIBRARY={os.environ['ANSIBLE_LIBRARY']}")

    yield BootstrapContext(changed_module_path, tmp_dir)


def main():
    """Linter CLI entry point."""
    cwd = pathlib.Path.cwd()

    options = cli.get_config(sys.argv[1:])

    initialize_logger(options.verbosity)
    _logger.debug("Options: %s", options)

    # assert 'ansible' not in sys.modules
    with bootstrap_ansible(options):

        from ansiblelint.utils import normpath, get_playbooks_and_roles
        import ansiblelint.formatters as formatters
        from ansiblelint.runner import Runner
        from ansiblelint.rules import RulesCollection

        formatter_factory: Any = formatters.Formatter
        if options.quiet:
            formatter_factory = formatters.QuietFormatter

        if options.parseable:
            formatter_factory = formatters.ParseableFormatter

        if options.parseable_severity:
            formatter_factory = formatters.ParseableSeverityFormatter

        formatter = formatter_factory(cwd, options.display_relative_path)

        if options.use_default_rules:
            rulesdirs = options.rulesdir + [default_rulesdir]
        else:
            rulesdirs = options.rulesdir or [default_rulesdir]
        rules = RulesCollection(rulesdirs)

        if options.listrules:
            formatted_rules = rules if options.format == 'plain' else rules_as_rst(rules)
            print(formatted_rules)
            return 0

        if options.listtags:
            print(rules.listtags())
            return 0

        if isinstance(options.tags, str):
            options.tags = options.tags.split(',')

        skip = set()
        for s in options.skip_list:
            skip.update(str(s).split(','))
        options.skip_list = frozenset(skip)

        if not options.playbook:
            # no args triggers auto-detection mode
            playbooks = get_playbooks_and_roles(options=options)
        else:
            playbooks = sorted(set(options.playbook))

        matches = list()
        checked_files: Set[Any] = set()
        for playbook in playbooks:
            runner = Runner(rules, playbook, options.tags,
                            options.skip_list, options.exclude_paths,
                            options.verbosity, checked_files)
            matches.extend(runner.run())

        matches.sort(key=lambda x: (normpath(x.filename), x.linenumber, x.rule.id))

        for match in matches:
            print(formatter.format(match, options.colored))

        if len(matches):
            return 2
        else:
            return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except IOError as exc:
        if exc.errno != errno.EPIPE:
            raise
    except RuntimeError as e:
        raise SystemExit(str(e))
