from ansiblelint.rules import AnsibleLintRule


def test_unjinja():
    input = "{{ a }} {% b %} {# try to confuse parsing inside a comment { {{}} } #}"
    output = "JINJA_EXPRESSION JINJA_STATEMENT JINJA_COMMENT"
    assert AnsibleLintRule.unjinja(input) == output
