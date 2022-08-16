"""This file contains copies of jinja's test suite data which is BSD (3-clause) licensed."""

from jinja2 import nodes


# use classes to group the fixtures
class AST:
    # from jinja's tests/idtracking.py
    for_loop = nodes.For(
        nodes.Name("foo", "store"),
        nodes.Name("seq", "load"),
        [nodes.Output([nodes.Name("foo", "load")])],
        [],
        None,
        False,
    )
    basics_tmpl = nodes.Template(
        [nodes.Assign(nodes.Name("foo", "store"), nodes.Name("bar", "load")), for_loop]
    )

    title_block = nodes.Block(
        "title", [nodes.Output([nodes.TemplateData("Page Title")])], False, False
    )

    render_title_macro = nodes.Macro(
        "render_title",
        [nodes.Name("title", "param")],
        [],
        [
            nodes.Output(
                [
                    nodes.TemplateData('\n  <div class="title">\n    <h1>'),
                    nodes.Name("title", "load"),
                    nodes.TemplateData("</h1>\n    <p>"),
                    nodes.Name("subtitle", "load"),
                    nodes.TemplateData("</p>\n    "),
                ]
            ),
            nodes.Assign(
                nodes.Name("subtitle", "store"), nodes.Const("something else")
            ),
            nodes.Output(
                [
                    nodes.TemplateData("\n    <p>"),
                    nodes.Name("subtitle", "load"),
                    nodes.TemplateData("</p>\n  </div>\n"),
                    nodes.If(
                        nodes.Name("something", "load"),
                        [
                            nodes.Assign(
                                nodes.Name("title_upper", "store"),
                                nodes.Filter(
                                    nodes.Name("title", "load"),
                                    "upper",
                                    [],
                                    [],
                                    None,
                                    None,
                                ),
                            ),
                            nodes.Output(
                                [
                                    nodes.Name("title_upper", "load"),
                                    nodes.Call(
                                        nodes.Name("render_title", "load"),
                                        [nodes.Const("Aha")],
                                        [],
                                        None,
                                        None,
                                    ),
                                ]
                            ),
                        ],
                        [],
                        [],
                    ),
                ]
            ),
        ],
    )

    for_loop = nodes.For(
        nodes.Name("item", "store"),
        nodes.Name("seq", "load"),
        [
            nodes.Output(
                [
                    nodes.TemplateData("\n    <li>"),
                    nodes.Name("item", "load"),
                    nodes.TemplateData("</li>\n    <span>"),
                ]
            ),
            nodes.Include(nodes.Const("helper.html"), True, False),
            nodes.Output([nodes.TemplateData("</span>\n  ")]),
        ],
        [],
        None,
        False,
    )

    body_block = nodes.Block(
        "body",
        [
            nodes.Output(
                [
                    nodes.TemplateData("\n  "),
                    nodes.Call(
                        nodes.Name("render_title", "load"),
                        [nodes.Name("item", "load")],
                        [],
                        None,
                        None,
                    ),
                    nodes.TemplateData("\n  <ul>\n  "),
                ]
            ),
            for_loop,
            nodes.Output([nodes.TemplateData("\n  </ul>\n")]),
        ],
        False,
        False,
    )

    complex_tmpl = nodes.Template(
        [
            nodes.Extends(nodes.Const("layout.html")),
            title_block,
            render_title_macro,
            body_block,
        ]
    )

    if_branching_stores_tmpl = nodes.Template(
        [
            nodes.If(
                nodes.Name("expression", "load"),
                [nodes.Assign(nodes.Name("variable", "store"), nodes.Const(42))],
                [],
                [],
            )
        ]
    )

    if_branching_stores_undefined_tmpl = nodes.Template(
        [
            nodes.Assign(nodes.Name("variable", "store"), nodes.Const(23)),
            nodes.If(
                nodes.Name("expression", "load"),
                [nodes.Assign(nodes.Name("variable", "store"), nodes.Const(42))],
                [],
                [],
            ),
        ]
    )

    for_loop = nodes.For(
        nodes.Name("item", "store"),
        nodes.Name("seq", "load"),
        [
            nodes.If(
                nodes.Name("expression", "load"),
                [nodes.Assign(nodes.Name("x", "store"), nodes.Const(42))],
                [],
                [],
            ),
            nodes.Include(nodes.Const("helper.html"), True, False),
        ],
        [],
        None,
        False,
    )

    if_branching_multi_scope_tmpl = nodes.Template(
        [nodes.Assign(nodes.Name("x", "store"), nodes.Const(23)), for_loop]
    )


class CoreTagsFixtures:
    # from jinja's tests/test_core_tags.py TestForLoop
    simple_for = "{% for item in seq %}{{ item }}{% endfor %}"
    for_else = "{% for item in seq %}XXX{% else %}...{% endfor %}"
    for_else_scoping_item = "{% for item in [] %}{% else %}{{ item }}{% endfor %}"
    for_empty_blocks = "<{% for item in seq %}{% else %}{% endfor %}>"
    for_context_vars = """{% for item in seq -%}
        {{ loop.index }}|{{ loop.index0 }}|{{ loop.revindex }}|{{
            loop.revindex0 }}|{{ loop.first }}|{{ loop.last }}|{{
           loop.length }}###{% endfor %}"""
    for_cycling = """{% for item in seq %}{{
        loop.cycle('<1>', '<2>') }}{% endfor %}{%
        for item in seq %}{{ loop.cycle(*through) }}{% endfor %}"""
    for_lookaround = """{% for item in seq -%}
            {{ loop.previtem|default('x') }}-{{ item }}-{{
            loop.nextitem|default('x') }}|
        {%- endfor %}"""
    for_changed = """{% for item in seq -%}
            {{ loop.changed(item) }},
        {%- endfor %}"""
    for_scope = "{% for item in seq %}{% endfor %}{{ item }}"
    for_varlen = "{% for item in iter %}{{ item }}{% endfor %}"
    # for_noniter =  # raises TypeError
    for_recursive = """{% for item in seq recursive -%}
            [{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
        {%- endfor %}"""
    for_recursive_lookaround = """{% for item in seq recursive -%}
            [{{ loop.previtem.a if loop.previtem is defined else 'x' }}.{{
            item.a }}.{{ loop.nextitem.a if loop.nextitem is defined else 'x'
            }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
        {%- endfor %}"""
    for_recursive_depth0 = """{% for item in seq recursive -%}
        [{{ loop.depth0 }}:{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
        {%- endfor %}"""
    for_recursive_depth = """{% for item in seq recursive -%}
        [{{ loop.depth }}:{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
        {%- endfor %}"""
    for_looploop = """{% for row in table %}
            {%- set rowloop = loop -%}
            {% for cell in row -%}
                [{{ rowloop.index }}|{{ loop.index }}]
            {%- endfor %}
        {%- endfor %}"""
    for_reversed_bug = (
        "{% for i in items %}{{ i }}"
        "{% if not loop.last %}"
        ",{% endif %}{% endfor %}"
    )
    # for_loop_errors_1 =  # raises UndefinedError
    for_loop_errors = """{% for item in [] %}...{% else
        %}{{ loop }}{% endfor %}"""
    for_loop_filter_1 = (
        "{% for item in range(10) if item is even %}[{{ item }}]{% endfor %}"
    )
    for_loop_filter_2 = """
        {%- for item in range(10) if item is even %}[{{
            loop.index }}:{{ item }}]{% endfor %}"""
    # for_loop_unassignable =  # raises TemplateSyntaxError
    for_scoped_special_var = (
        "{% for s in seq %}[{{ loop.first }}{% for c in s %}"
        "|{{ loop.first }}{% endfor %}]{% endfor %}"
    )
    for_scoped_loop_var_1 = (
        "{% for x in seq %}{{ loop.first }}"
        "{% for y in seq %}{% endfor %}{% endfor %}"
    )
    for_scoped_loop_var_2 = (
        "{% for x in seq %}{% for y in seq %}"
        "{{ loop.first }}{% endfor %}{% endfor %}"
    )
    for_recursive_empty_loop_iter = """
        {%- for item in foo recursive -%}{%- endfor -%}
        """
    for_call_in_loop = """
        {%- macro do_something() -%}
            [{{ caller() }}]
        {%- endmacro %}

        {%- for i in [1, 2, 3] %}
            {%- call do_something() -%}
                {{ i }}
            {%- endcall %}
        {%- endfor -%}
        """
    for_scoping_bug = """
        {%- for item in foo %}...{{ item }}...{% endfor %}
        {%- macro item(a) %}...{{ a }}...{% endmacro %}
        {{- item(2) -}}
        """
    for_unpacking = (
        "{% for a, b, c in [[1, 2, 3]] %}{{ a }}|{{ b }}|{{ c }}{% endfor %}"
    )
    for_intended_scoping_with_set_1 = (
        "{% for item in seq %}{{ x }}{% set x = item %}{{ x }}{% endfor %}"
    )
    for_intended_scoping_with_set_2 = (
        "{% set x = 9 %}{% for item in seq %}{{ x }}"
        "{% set x = item %}{{ x }}{% endfor %}"
    )

    # from jinja's tests/test_core_tags.py TestIfCondition
    simple_if = """{% if true %}...{% endif %}"""
    if_elif = """{% if false %}XXX{% elif true
        %}...{% else %}XXX{% endif %}"""
    elifs = "\n".join(f"{{% elif a == {i} %}}{i}" for i in range(1, 1000))
    if_elif_deep = f"{{% if a == 0 %}}0{elifs}{{% else %}}x{{% endif %}}"
    if_else = "{% if false %}XXX{% else %}...{% endif %}"
    if_empty = "[{% if true %}{% else %}{% endif %}]"
    if_complete = "{% if a %}A{% elif b %}B{% elif c == d %}C{% else %}D{% endif %}"
    if_no_scope_1 = "{% if a %}{% set foo = 1 %}{% endif %}{{ foo }}"
    if_no_scope_2 = "{% if true %}{% set foo = 1 %}{% endif %}{{ foo }}"

    # from jinja's tests/test_core_tags.py TestMacros
    simple_macros = """\
{% macro say_hello(name) %}Hello {{ name }}!{% endmacro %}
{{ say_hello('Peter') }}"""
    macros_scoping = """\
{% macro level1(data1) %}
{% macro level2(data2) %}{{ data1 }}|{{ data2 }}{% endmacro %}
{{ level2('bar') }}{% endmacro %}
{{ level1('foo') }}"""
    macros_arguments = """\
{% macro m(a, b, c='c', d='d') %}{{ a }}|{{ b }}|{{ c }}|{{ d }}{% endmacro %}
{{ m() }}|{{ m('a') }}|{{ m('a', 'b') }}|{{ m(1, 2, 3) }}"""
    # macros_arguments_defaults_nonsense =  # raises TemplateSyntaxError
    # macros_caller_defaults_nonsense =  # raises TemplateSyntaxError
    macros_varargs = """\
{% macro test() %}{{ varargs|join('|') }}{% endmacro %}\
{{ test(1, 2, 3) }}"""
    macros_simple_call = """\
{% macro test() %}[[{{ caller() }}]]{% endmacro %}\
{% call test() %}data{% endcall %}"""
    macros_complex_call = """\
{% macro test() %}[[{{ caller('data') }}]]{% endmacro %}\
{% call(data) test() %}{{ data }}{% endcall %}"""
    macros_caller_undefined = """\
{% set caller = 42 %}\
{% macro test() %}{{ caller is not defined }}{% endmacro %}\
{{ test() }}"""
    macros_include_env_dict = {
        "include": "{% macro test(foo) %}[{{ foo }}]{% endmacro %}"
    }
    macros_include = '{% from "include" import test %}{{ test("foo") }}'
    macros_macro_api = (
        "{% macro foo(a, b) %}{% endmacro %}"
        "{% macro bar() %}{{ varargs }}{{ kwargs }}{% endmacro %}"
        "{% macro baz() %}{{ caller() }}{% endmacro %}"
    )
    macros_callself = (
        "{% macro foo(x) %}{{ x }}{% if x > 1 %}|"
        "{{ foo(x - 1) }}{% endif %}{% endmacro %}"
        "{{ foo(5) }}"
    )
    macros_macro_defaults_self_ref = """
        {%- set x = 42 %}
        {%- macro m(a, b=x, x=23) %}{{ a }}|{{ b }}|{{ x }}{% endmacro -%}
    """

    # from jinja's tests/test_core_tags.py TestSet
    set_normal = "{% set foo = 1 %}{{ foo }}"
    set_block = "{% set foo %}42{% endset %}{{ foo }}"
    set_block_escaping = "{% set foo %}<em>{{ test }}</em>{% endset %}foo: {{ foo }}"
    # set_set_invalid =  # raises TemplateSyntaxError, TemplateRuntimeError
    # set_namespace_redefined =  # raises TemplateRuntimeError
    set_namespace = "{% set ns = namespace() %}{% set ns.bar = '42' %}{{ ns.bar }}"
    set_namespace_block = (
        "{% set ns = namespace() %}{% set ns.bar %}42{% endset %}{{ ns.bar }}"
    )
    set_init_namespace = (
        "{% set ns = namespace(d, self=37) %}"
        "{% set ns.b = 42 %}"
        "{{ ns.a }}|{{ ns.self }}|{{ ns.b }}"
    )
    set_namespace_loop = (
        "{% set ns = namespace(found=false) %}"
        "{% for x in range(4) %}"
        "{% if x == v %}"
        "{% set ns.found = true %}"
        "{% endif %}"
        "{% endfor %}"
        "{{ ns.found }}"
    )
    set_namespace_macro = (
        "{% set ns = namespace() %}"
        "{% set ns.a = 13 %}"
        "{% macro magic(x) %}"
        "{% set x.b = 37 %}"
        "{% endmacro %}"
        "{{ magic(ns) }}"
        "{{ ns.a }}|{{ ns.b }}"
    )
    set_block_escaping_filtered = (
        "{% set foo | trim %}<em>{{ test }}</em>    {% endset %}foo: {{ foo }}"
    )
    set_block_filtered = (
        "{% set foo | trim | length | string %} 42    {% endset %}{{ foo }}"
    )
    # set_block_filtered_set =  # uses custom filter: _myfilter

    # from jinja's tests/test_core_tags.py TestWith
    with_with = """\
        {% with a=42, b=23 -%}
            {{ a }} = {{ b }}
        {% endwith -%}
            {{ a }} = {{ b }}\
        """
    with_with_argument_scoping = """\
        {%- with a=1, b=2, c=b, d=e, e=5 -%}
            {{ a }}|{{ b }}|{{ c }}|{{ d }}|{{ e }}
        {%- endwith -%}
        """


class FilterFixtures:
    # from jinja's tests/test_idtracking.py TestFilter
    # this only has some fixtures
    groupby = """
        {%- for grouper, list in [{'foo': 1, 'bar': 2},
                                  {'foo': 2, 'bar': 3},
                                  {'foo': 1, 'bar': 1},
                                  {'foo': 3, 'bar': 4}]|groupby('foo') -%}
            {{ grouper }}{% for x in list %}: {{ x.foo }}, {{ x.bar }}{% endfor %}|
        {%- endfor %}"""
    groupby_tuple_index = """
        {%- for grouper, list in [('a', 1), ('a', 2), ('b', 1)]|groupby(0) -%}
            {{ grouper }}{% for x in list %}:{{ x.1 }}{% endfor %}|
        {%- endfor %}"""


class TrimBlocksFixtures:
    # from jinja's tests/test_lexnparse.py TestTrimBlocks
    trim = "    {% if True %}\n    {% endif %}"
    no_trim = "    {% if True +%}\n    {% endif %}"
    no_trim_outer = "{% if True %}X{% endif +%}\nmore things"
    lstrip_no_trim = "    {% if True +%}\n    {% endif %}"
    trim_blocks_false_with_no_trim_block1 = "    {% if True %}\n    {% endif %}"
    trim_blocks_false_with_no_trim_block2 = "    {% if True +%}\n    {% endif %}"
    trim_blocks_false_with_no_trim_comment1 = "    {# comment #}\n    "
    trim_blocks_false_with_no_trim_comment2 = "    {# comment +#}\n    "
    trim_blocks_false_with_no_trim_raw1 = "    {% raw %}{% endraw %}\n    "
    trim_blocks_false_with_no_trim_raw2 = "    {% raw %}{% endraw +%}\n    "
    trim_nested = "    {% if True %}\na {% if True %}\nb {% endif %}\nc {% endif %}"
    no_trim_nested = (
        "    {% if True +%}\na {% if True +%}\nb {% endif +%}\nc {% endif %}"
    )
    comment_trim = """    {# comment #}\n\n  """
    comment_no_trim = """    {# comment +#}\n\n  """
    multiple_comment_trim_lstrip = (
        "   {# comment #}\n\n{# comment2 #}\n   \n{# comment3 #}\n\n "
    )
    multiple_comment_no_trim_lstrip = (
        "   {# comment +#}\n\n{# comment2 +#}\n   \n{# comment3 +#}\n\n "
    )
    raw_trim_lstrip = "{{x}}{% raw %}\n\n    {% endraw %}\n\n{{ y }}"
    raw_no_trim_lstrip = "{{x}}{% raw %}\n\n      {% endraw +%}\n\n{{ y }}"


# TODO: maybe get template examples from jinja's
#       tests/test_ext.py
#       tests/test_imports.py TestImports, TestIncludes
#       tests/test_inheritance.py TestInheritance
