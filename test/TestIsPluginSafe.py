# -*- coding: utf-8; -*-
from pathlib import Path
import sys
from unittest import mock

import pytest

from ansiblelint.utils import _is_plugin_safe, _is_path_safe_posix, _is_path_safe_windows


RULES_DIR = 'rules'
SYMLINK = 'via-symlink'
GROUP_WRITABLE = 'group-writable.py'
PARENT_WRITABLE = 'parent-writable.py'
WORLD_WRITABLE = 'world-writable.py'


@pytest.fixture
def safe_path(tmp_path):
    """Create the filesystem tree depicted below.

    ::

        <tmp_path>
        └── parent                         drwxr-xr-x
            └── ok                         drwxr-xr-x
                ├── rules                  drwxr-xr-x
                │   └── somerule.py        -rwxr--r--
                └── via-symlink -> rules   lrwxrwxrwx

    """
    safe_dir = tmp_path / 'parent' / 'safe'
    safe_dir.mkdir(parents=True)
    safe_dir.chmod(0o755)
    safe_dir.parent.chmod(0o755)
    rules_dir = safe_dir / 'rules'
    rules_dir.mkdir()
    rules_dir.chmod(0o755)
    (safe_dir / 'link').symlink_to(rules_dir, target_is_directory=True)
    (rules_dir / 'module.py').touch(0o644)

    return safe_dir


@pytest.fixture
def unsafe_path(tmp_path):
    """Create the filesystem tree depicted below.

    ::

        <tmp_path>
        └── too-broad
            ├── rules
            │   ├── group-writable.py    -rwxrw-r--
            │   ├── parent-writable.py   -rwxr--r--
            │   └── world-writable.py    -rwxr--rw-
            └── via-symlink -> rules     lrwxrwxrwx

    """
    unsafe_dir = tmp_path / 'parent' / 'unsafe'
    unsafe_dir.mkdir(parents=True)
    unsafe_dir.chmod(0o757)
    unsafe_dir.parent.chmod(0o755)
    rules_dir = unsafe_dir / 'rules'
    rules_dir.mkdir()
    (unsafe_dir / SYMLINK).symlink_to(rules_dir, target_is_directory=True)
    group = (rules_dir / GROUP_WRITABLE)
    group.touch()  # Don't use mode=0oXXX: is impacted by user umask
    group.chmod(0o664)
    parent = (rules_dir / PARENT_WRITABLE)
    parent.touch()
    parent.chmod(0o644)
    world = (rules_dir / WORLD_WRITABLE)
    world.touch()
    world.chmod(0o646)
    return unsafe_dir


@pytest.mark.skipif(sys.platform == 'window', reason='Only applies to Posix filesystems')
@pytest.mark.parametrize('rules_dir', ('link', 'rules'))
@pytest.mark.parametrize('module', (
    pytest.param('module.py', id='module'),
    pytest.param('', id='directory'),
))
def test_is_path_safe_posix(safe_path, rules_dir, module):
    assert _is_path_safe_posix(safe_path / rules_dir / module)


@pytest.mark.skipif(sys.platform == 'window', reason='Only applies to Posix filesystems')
@pytest.mark.parametrize(('rules_dir'), ('via-symlink', 'rules'))
@pytest.mark.parametrize(('module', 'issue'), (
    pytest.param(GROUP_WRITABLE,
                 '{}: 0664.$'.format(GROUP_WRITABLE),
                 id='group-writable'),
    pytest.param(PARENT_WRITABLE, r'unsafe: 0757.$', id='parent-writable'),
    pytest.param(WORLD_WRITABLE, r'{}: 0646.$'.format(WORLD_WRITABLE), id='world-writable'),
))
def test_is_path_safe_posix_when_unsafe(unsafe_path, rules_dir, module, issue):
    with pytest.raises(RuntimeError, match=issue):
        _is_path_safe_posix(unsafe_path / rules_dir / module)


@pytest.mark.parametrize('path', ('rules', Path('rules')))
@pytest.mark.parametrize('impl', (
    pytest.param(_is_path_safe_posix,
                 id='POSIX',
                 marks=pytest.mark.skipif(sys.platform == 'window',
                                          reason='Only applies to Posix platforms')),
    pytest.param(_is_path_safe_windows,
                 id='Windows',
                 marks=pytest.mark.skipif(sys.platform != 'window',
                                          reason='Only applies to the Windows platform')),
))
def test__is_plugin_safe(monkeypatch, path, impl):
    # Given
    mock_impl = mock.Mock(spec=impl)
    monkeypatch.setattr('ansiblelint.utils.{}'.format(impl.__name__), mock_impl)

    # When
    _is_plugin_safe(path)

    # Then
    mock_impl.assert_called_once_with(Path(path))


# vim: et:sw=4:syntax=python:ts=4:
