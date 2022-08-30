"""PyTest fixtures for testing jinja_utils."""
from __future__ import annotations

from typing import cast

import pytest
from ansible.template import Templar
from jinja2.environment import Environment
from jinja2.lexer import Lexer

from ansiblelint.utils import ansible_templar


@pytest.fixture(name="templar")
def fixture_templar() -> Templar:
    """Initialize an Ansible Templar for each test with dummy info."""
    basedir = "/base/dir"
    templatevars = {"playbook_dir": "/a/b/c"}
    return ansible_templar(basedir, templatevars)


@pytest.fixture(name="jinja_env")
def fixture_jinja_env(templar: Templar) -> Environment:
    """Initialize a Jinja2 Environment for each test."""
    # this is AnsibleEnvironment | AnsibleNativeEnvironment
    return cast(Environment, templar.environment)


@pytest.fixture(name="lexer")
def fixture_lexer(jinja_env: Environment) -> Lexer:
    """Initialize a Jinja2 Lexer for each test."""
    return jinja_env.lexer
