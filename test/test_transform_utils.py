"""Tests for utils that dump Jinja expressions."""

import pytest
from jinja2.environment import Environment

# from ansiblelint.transform_utils import TemplateDumper, dump
from ansiblelint.transform_utils import dump


@pytest.mark.parametrize(
    ("in_template", "expected_template"),
    (
        pytest.param("", "", id="EmptyTemplate"),
        pytest.param("{{item}}", "{{ item }}", id="VarStmtWithoutSpacing"),
        pytest.param(
            "{% set ns = [1, 1, 2] %}",
            "{% set ns = [1, 1, 2] %}",
            id="SimpleSetBlockStmt",
        ),
        # TODO: how to handle whitespace and chomping?
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
def test_dump(in_template, expected_template):
    """Test the jinja template dumping function."""
    environment = Environment()
    in_ast = environment.parse(in_template)
    out_template = dump(
        node=in_ast,
        environment=environment,
        stream=None,
    )
    out_ast = environment.parse(out_template)
    assert in_ast == out_ast
    # expected_template may have spacing changes vs out_template
    assert out_template == expected_template
