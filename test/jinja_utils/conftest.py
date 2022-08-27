import pytest

from ansible.template import Templar
from jinja2.environment import Environment
from jinja2.lexer import Lexer

from ansiblelint.utils import ansible_templar


@pytest.fixture
def templar() -> Templar:
    basedir = "/base/dir"
    templatevars = {"playbook_dir": "/a/b/c"}
    return ansible_templar(basedir, templatevars)


@pytest.fixture
def jinja_env(templar: Templar) -> Environment:
    return templar.environment


@pytest.fixture
def lexer(jinja_env: Environment) -> Lexer:
    return jinja_env.lexer
