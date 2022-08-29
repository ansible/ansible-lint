"""Tests for utils that dump Jinja expressions."""
from __future__ import annotations

import pytest
from jinja2.environment import Environment

# from ansiblelint.jinja_utils.dumper import TemplateDumper, dump
from ansiblelint.jinja_utils.dumper import dump


@pytest.mark.parametrize(
    ("in_template", "expected_template"),
    (
        pytest.param("", "", id="EmptyTemplate"),
        pytest.param("{{item}}", "{{ item }}", id="VarStmtWithoutSpacing"),
        pytest.param(
            "{% set ns = [1, 1, 2] %}",
            "{% set ns = [1, 1, 2] %}\n",
            id="SimpleSetBlockStmt",
        ),
        # This automatically adds newlines after most block tags (like 'set')
        # any other whitespace, including chomped whitespace, is discarded
        # by Jinja2's lexer + parser. Preserving that would require significant
        # changes to Jinja2. So, the best we can do is find decent heuristics
        # for when to add new lines.
        # TODO: We might need to make 'multiline' a setting that gets passed
        #       into TemplatDumper.__init__ to disable these newlines when a
        #       single expression is expected.
        pytest.param(
            "{{ good_format }}\n{{- good_format }}\n{{- good_format -}}",
            # expect the same as input, but actually get:
            "{{ good_format }}{{ good_format }}{{ good_format }}",
            id="MultipleVarStmts",
        ),
        pytest.param(
            "{{ file }}.tar.bz2",
            "{{ file }}.tar.bz2",
            id="SimpleTemplateData",
        ),
        pytest.param(
            """docker info --format '{{ '{{' }}json .Swarm.LocalNodeState{{ '}}' }}' | tr -d '"'""",
            """docker info --format '{{ '{{' }}json .Swarm.LocalNodeState{{ '}}' }}' | tr -d '"'""",
            id="ComplexTemplateData",
        ),
        pytest.param(
            # Extra spaces get cleaned up too
            "{{ {'test': { 'subtest': variable }} }}",
            "{{ {'test': {'subtest': variable}} }}",
            id="DictLiteralVarStmt",
        ),
        pytest.param(
            "{{ {'dummy_2': {'nested_dummy_1': 'value_1', 'nested_dummy_2': value_2}} | combine(dummy_1) }}",
            "{{ {'dummy_2': {'nested_dummy_1': 'value_1', 'nested_dummy_2': value_2}} | combine(dummy_1) }}",
            id="DictLiteralWithFilter",
        ),
        pytest.param(
            "{{ {'dummy_2': {'nested_dummy_1': 'value_1',\n'nested_dummy_2': value_2}} |\ncombine(dummy_1)}}",
            "{{ {'dummy_2': {'nested_dummy_1': 'value_1', 'nested_dummy_2': value_2}} | combine(dummy_1) }}",
            id="DictLiteralWithFilterAndNewlines",
        ),
        pytest.param(
            '{{ lookup("file", "a_file") }}',
            # Const gets repr()'d and python uses '' by default to wrap strings.
            "{{ lookup('file', 'a_file') }}",
            id="LookupFuncArgQuotes",
        ),
        pytest.param(
            "{{ true and (false or true) }}",
            # repr() on bools...
            "{{ True and (False or True) }}",
            id="OrderedOperations",
        ),
        pytest.param(
            "{{ '1' == '1' }}",
            "{{ '1' == '1' }}",
            id="SimpleComparison",
        ),
        pytest.param(
            "{{ 1 == 1 and (1 > 2 or 2 != 3) }}",
            "{{ 1 == 1 and (1 > 2 or 2 != 3) }}",
            id="ComplexComparison",
        ),
        pytest.param(
            "{{ not foobar }}",
            "{{ not foobar }}",
            id="NotExpr",
        ),
        pytest.param(
            "{{ not (foobar and baz) }}",
            "{{ not (foobar and baz) }}",
            id="ComplexNotExpr",
        ),
        pytest.param(
            "{{ 4 not in [1, 2, 3] }}",
            "{{ 4 not in [1, 2, 3] }}",
            id="NotInComparison",
        ),
        pytest.param(
            "{{ (4 or 3) in ([] or [1, 2, 3]) }}",
            "{{ (4 or 3) in ([] or [1, 2, 3]) }}",
            id="InOrComparison",
        ),
    ),
)
def test_dump(in_template: str, expected_template: str) -> None:
    """Test the jinja template dumping function."""
    environment = Environment()
    in_ast = environment.parse(in_template)
    out_template = dump(
        node=in_ast,
        environment=environment,
        stream=None,
    )
    assert out_template is not None
    out_ast = environment.parse(out_template)
    assert in_ast == out_ast
    # expected_template may have spacing changes vs out_template
    assert out_template == expected_template
