# -*- coding: utf-8; -*-
import os

from ansiblelint.cli import abspath


def test_expand_path_vars(monkeypatch, tmp_path):
    test_path = str(tmp_path / 'path')  # str(tmpdir): Issue with Py3.5
    relative_path = 'more'
    monkeypatch.setenv('TEST_PATH', test_path)

    assert abspath('~', None) == os.path.expanduser('~')
    assert abspath('$TEST_PATH', None) == test_path
    assert abspath(relative_path, test_path) == os.path.join(test_path, relative_path)
    assert abspath(os.sep.join(['$TEST_PATH', relative_path]),
                   None) == os.path.join(test_path, relative_path)


# vim: et:sw=4:syntax=python:ts=4:
