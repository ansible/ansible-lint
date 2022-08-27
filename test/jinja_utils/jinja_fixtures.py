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


class ImportsFixtures:
    context_imports_1 = '{% import "module" as m %}{{ m.test() }}'
    context_imports_2 = '{% import "module" as m without context %}{{ m.test() }}'
    context_imports_3 = '{% import "module" as m with context %}{{ m.test() }}'
    context_imports_4 = '{% from "module" import test %}{{ test() }}'
    context_imports_5 = '{% from "module" import test without context %}{{ test() }}'
    context_imports_6 = '{% from "module" import test with context %}{{ test() }}'
    import_needs_name_1 = '{% from "foo" import bar %}'
    import_needs_name_2 = '{% from "foo" import bar, baz %}'
    # import_needs_name_3 =  # raises TemplateSyntaxError
    # no_trailing_comma =  # raises TemplateSyntaxError
    trailing_comma_with_context_1 = '{% from "foo" import bar, baz with context %}'
    trailing_comma_with_context_2 = '{% from "foo" import bar, baz, with context %}'
    trailing_comma_with_context_3 = '{% from "foo" import bar, with context %}'
    trailing_comma_with_context_4 = '{% from "foo" import bar, with, context %}'
    trailing_comma_with_context_5 = '{% from "foo" import bar, with with context %}'
    # trailing_comma_with_context_6 =  # raises TemplateSyntaxError
    # trailing_comma_with_context_7 =  # raises TemplateSyntaxError
    exports = """
        {% macro toplevel() %}...{% endmacro %}
        {% macro __private() %}...{% endmacro %}
        {% set variable = 42 %}
        {% for item in [1] %}
            {% macro notthere() %}{% endmacro %}
        {% endfor %}
        """
    # not_exported = "{% from 'module' import nothing %}{{ nothing() }}"  # raises UndefinedError
    import_globals = {"foo": 42}
    import_with_globals = '{% import "module" as m %}{{ m.test() }}'  # with import_globals
    # with import_globals
    import_with_globals_override = '{% set foo = 41 %}{% import "module" as m %}{{ m.test() }}'
    from_import_with_globals = '{% from "module" import test %}{{ test() }}'


class IncludesFixtures:
    context_include_1 = '{% include "header" %}'
    context_include_2 = '{% include "header" with context %}'
    context_include_3 = '{% include "header" without context %}'
    choice_includes_1 = '{% include ["missing", "header"] %}'
    choice_includes_2 = '{% include ["missing", "missing2"] ignore missing %}'
    # choice_includes_3 = '{% include ["missing", "missing2"] %}'  # raises Template(s)NotFound
    choice_includes_4 = '{% include ["missing", "header"] %}'
    choice_includes_5 = "{% include x %}"
    choice_includes_6 = '{% include [x, "header"] %}'
    choice_includes_7 = "{% include x %}"
    choice_includes_8 = "{% include [x] %}"
    # include_ignoring_missing_1 = '{% include "missing" %}'  # raises TemplateNotFound
    include_ignoring_missing_2 = '{% include "missing" ignore missing %}'
    include_ignoring_missing_3 = '{% include "missing" ignore missing with context %}'
    include_ignoring_missing_4 = '{% include "missing" ignore missing without context %}'
    context_include_with_overrides_main = "{% for item in [1, 2, 3] %}{% include 'item' %}{% endfor %}"
    context_include_with_overrides_item = "{{ item }}"
    unoptimized_scopes = """
        {% macro outer(o) %}
        {% macro inner() %}
        {% include "o_printer" %}
        {% endmacro %}
        {{ inner() }}
        {% endmacro %}
        {{ outer("FOO") }}
        """
    import_from_with_context_a = "{% macro x() %}{{ foobar }}{% endmacro %}"
    import_from_with_context = "{% set foobar = 42 %}{% from 'a' import x with context %}{{ x() }}"


class InheritanceFixtures:
    layout = """\
|{% block block1 %}block 1 from layout{% endblock %}
|{% block block2 %}block 2 from layout{% endblock %}
|{% block block3 %}
{% block block4 %}nested block 4 from layout{% endblock %}
{% endblock %}|"""
    level1 = """\
{% extends "layout" %}
{% block block1 %}block 1 from level1{% endblock %}"""
    level2 = """\
{% extends "level1" %}
{% block block2 %}{% block block5 %}nested block 5 from level2{%
endblock %}{% endblock %}"""
    level3 = """\
{% extends "level2" %}
{% block block5 %}block 5 from level3{% endblock %}
{% block block4 %}block 4 from level3{% endblock %}
"""
    level4 = """\
{% extends "level3" %}
{% block block3 %}block 3 from level4{% endblock %}
"""
    working = """\
{% extends "layout" %}
{% block block1 %}
  {% if false %}
    {% block block2 %}
      this should work
    {% endblock %}
  {% endif %}
{% endblock %}
"""
    double_e = """\
{% extends "layout" %}
{% extends "layout" %}
{% block block1 %}
  {% if false %}
    {% block block2 %}
      this should work
    {% endblock %}
  {% endif %}
{% endblock %}
"""
    super_a = (
        "{% block intro %}INTRO{% endblock %}|"
        "BEFORE|{% block data %}INNER{% endblock %}|AFTER"
    )
    super_b = (
        '{% extends "a" %}{% block data %}({{ '
        "super() }}){% endblock %}"
    )
    super_c = (
        '{% extends "b" %}{% block intro %}--{{ '
        "super() }}--{% endblock %}\n{% block data "
        "%}[{{ super() }}]{% endblock %}"
    )
    reuse_blocks = "{{ self.foo() }}|{% block foo %}42{% endblock %}|{{ self.foo() }}"
    preserve_blocks_a = (
        "{% if false %}{% block x %}A{% endblock %}"
        "{% endif %}{{ self.x() }}"
    )
    preserve_blocks_b = '{% extends "a" %}{% block x %}B{{ super() }}{% endblock %}'
    dynamic_inheritance_default1 = "DEFAULT1{% block x %}{% endblock %}"
    dynamic_inheritance_default2 = "DEFAULT2{% block x %}{% endblock %}"
    dynamic_inheritance_child = "{% extends default %}{% block x %}CHILD{% endblock %}"
    multi_inheritance_default1 = "DEFAULT1{% block x %}{% endblock %}"
    multi_inheritance_default2 = "DEFAULT2{% block x %}{% endblock %}"
    multi_inheritance_child = (
        "{% if default %}{% extends default %}{% else %}"
        "{% extends 'default1' %}{% endif %}"
        "{% block x %}CHILD{% endblock %}"
    )
    scoped_block_default_html = (
        "{% for item in seq %}[{% block item scoped %}"
        "{% endblock %}]{% endfor %}"
    )
    scoped_block = "{% extends 'default.html' %}{% block item %}{{ item }}{% endblock %}"
    super_in_scoped_block_default_html = (
        "{% for item in seq %}[{% block item scoped %}"
        "{{ item }}{% endblock %}]{% endfor %}"
    )
    super_in_scoped_block = (
        '{% extends "default.html" %}{% block item %}'
        "{{ super() }}|{{ item * 2 }}{% endblock %}"
    )
    scoped_block_after_inheritance_layout_html = """
        {% block useless %}{% endblock %}
        """
    scoped_block_after_inheritance_index_html = """
        {%- extends 'layout.html' %}
        {% from 'helpers.html' import foo with context %}
        {% block useless %}
            {% for x in [1, 2, 3] %}
                {% block testing scoped %}
                    {{ foo(x) }}
                {% endblock %}
            {% endfor %}
        {% endblock %}
        """
    scoped_block_after_inheritance_helpers_html = """
        {% macro foo(x) %}{{ the_foo + x }}{% endmacro %}
        """
    level1_required_default = "{% block x required %}{# comment #}\n {% endblock %}"
    level1_required_level1 = "{% extends 'default' %}{% block x %}[1]{% endblock %}"
    level2_required_default = "{% block x required %}{% endblock %}"
    level2_required_level1 = "{% extends 'default' %}{% block x %}[1]{% endblock %}"
    level2_required_level2 = "{% extends 'default' %}{% block x %}[2]{% endblock %}"
    level3_required_default = "{% block x required %}{% endblock %}"
    level3_required_level1 = "{% extends 'default' %}"
    level3_required_level2 = "{% extends 'level1' %}{% block x %}[2]{% endblock %}"
    level3_required_level3 = "{% extends 'level2' %}"
    # invalid_required =  # raises TemplateSyntaxError
    required_with_scope_default1 = (
        "{% for item in seq %}[{% block item scoped required %}"
        "{% endblock %}]{% endfor %}"
    )
    required_with_scope_child1 = (
        "{% extends 'default1' %}{% block item %}"
        "{{ item }}{% endblock %}"
    )
    # required_with_scope_2 =  # raises TemplateSyntaxError
    # duplicate_required_or_scoped =  # raises TemplateSyntaxError
    # fixed_macro_scoping_bug =  # raises TemplateRuntimeError

# TODO: maybe get template examples from jinja's
#       tests/test_ext.py
