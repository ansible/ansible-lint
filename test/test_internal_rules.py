from ansiblelint._internal.rules import BaseRule


def test_baserule_url():
    rule = BaseRule()
    assert rule.url == "https://ansible-lint.readthedocs.io/rules/"
