# -*- coding: utf-8; -*-
from pathlib import Path
from unittest import mock

import pytest

from ansiblelint import default_rulesdir
from ansiblelint.cli import get_config
from ansiblelint.utils import get_playbooks_and_roles


@pytest.mark.parametrize('cli_args', (
    pytest.param([], id='no_arguments'),
    pytest.param(['-R'], id='use_default_rules'),
    pytest.param(['-r', default_rulesdir], id='default_rulesdir'),
    # Py3.5 needs -r argument to be an existing directory.
    pytest.param(['-r', 'test/fixtures/', '-R'], id='random_rulesdir+use_default_rules')
))
def test_get_config_expands_vars(cli_args):
    options = get_config(cli_args)

    assert Path(default_rulesdir) in options.rulesdir


@pytest.mark.parametrize(('cli_args', 'expected'), (
    pytest.param([], True, id='calls_get_playbooks_and_roles'),
    pytest.param(['test/norole.yml'], False, id='skips_get_playbooks_and_roles'),
))
def test_get_config_searches_for_playbook_and_roles_when_no_given(monkeypatch, cli_args, expected):
    mock_get_playbooks_and_roles = mock.Mock(spec=get_playbooks_and_roles)
    monkeypatch.setattr('ansiblelint.cli.get_playbooks_and_roles', mock_get_playbooks_and_roles)

    get_config(cli_args)

    assert mock_get_playbooks_and_roles.called == expected


# vim: et:sw=4:syntax=python:ts=4:
