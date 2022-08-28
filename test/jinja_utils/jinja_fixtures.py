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


class ExtendedAPIFixtures:
    # from jinja's tests/test_api.py TestExtendedAPI
    item_and_attribute_1 = "{{ foo.items()|list }}"
    item_and_attribute_2 = '{{ foo|attr("items")()|list }}'
    item_and_attribute_3 = '{{ foo["items"] }}'


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
    # from jinja's tests/test_filters.py TestFilter
    capitalize = '{{ "foo bar"|capitalize }}'
    center = '{{ "foo"|center(9) }}'
    default = (
        "{{ missing|default('no') }}|{{ false|default('no') }}|"
        "{{ false|default('no', true) }}|{{ given|default('no') }}"
    )
    dictsort_1 = "{{ foo|dictsort() }}"
    dictsort_2 = "{{ foo|dictsort(true) }}"
    dictsort_3 = '{{ foo|dictsort(by="value") }}'
    dictsort_4 = "{{ foo|dictsort(reverse=true) }}"
    batch = "{{ foo|batch(3)|list }}|{{ foo|batch(3, 'X')|list }}"
    slice_ = "{{ foo|slice(3)|list }}|{{ foo|slice(3, 'X')|list }}"
    escape = """{{ '<">&'|escape }}"""
    trim = "{{ foo|trim(chars) }}"
    striptags = """{{ foo|striptags }}"""
    filesizeformat = (
        "{{ 100|filesizeformat }}|"
        "{{ 1000|filesizeformat }}|"
        "{{ 1000000|filesizeformat }}|"
        "{{ 1000000000|filesizeformat }}|"
        "{{ 1000000000000|filesizeformat }}|"
        "{{ 100|filesizeformat(true) }}|"
        "{{ 1000|filesizeformat(true) }}|"
        "{{ 1000000|filesizeformat(true) }}|"
        "{{ 1000000000|filesizeformat(true) }}|"
        "{{ 1000000000000|filesizeformat(true) }}"
    )
    filesizeformat_issue59 = (
        "{{ 300|filesizeformat }}|"
        "{{ 3000|filesizeformat }}|"
        "{{ 3000000|filesizeformat }}|"
        "{{ 3000000000|filesizeformat }}|"
        "{{ 3000000000000|filesizeformat }}|"
        "{{ 300|filesizeformat(true) }}|"
        "{{ 3000|filesizeformat(true) }}|"
        "{{ 3000000|filesizeformat(true) }}"
    )
    first = "{{ foo|first }}"
    float_ = "{{ value|float }}"
    float_default = "{{ value|float(default=1.0) }}"
    format_ = "{{ '%s|%s'|format('a', 'b') }}"
    indent_1 = "{{ foo|indent(2, false, false) }}"
    indent_2 = "{{ foo|indent(2, false, true) }}"
    indent_3 = "{{ foo|indent(2, true, false) }}"
    indent_4 = "{{ foo|indent(2, true, true) }}"
    indent_5 = '{{ "jinja"|indent }}'
    indent_6 = '{{ "jinja"|indent(first=true) }}'
    indent_7 = '{{ "jinja"|indent(blank=true) }}'
    indent_width_string = "{{ 'jinja\nflask'|indent(width='>>> ', first=True) }}"
    int_ = "{{ value|int }}"
    int_base = "{{ value|int(base=base) }}"
    int_default = "{{ value|int(default=1) }}"
    join_1 = '{{ [1, 2, 3]|join("|") }}'
    join_2 = '{{ ["<foo>", "<span>foo</span>"|safe]|join }}'
    join_attribute = """{{ users|join(', ', 'username') }}"""
    last = """{{ foo|last }}"""
    length = """{{ "hello world"|length }}"""
    lower = """{{ "FOO"|lower }}"""
    items = """{{ d|items|list }}"""
    items_undefined = """{{ d|items|list }}"""
    pprint = """{{ data|pprint }}"""
    random = '{{ "1234567890"|random }}'
    reverse = "{{ 'foobar'|reverse|join }}|{{ [1, 2, 3]|reverse|list }}"
    string = """{{ obj|string }}"""
    title_1 = """{{ "foo bar"|title }}"""
    title_2 = """{{ "foo's bar"|title }}"""
    title_3 = """{{ "foo   bar"|title }}"""
    title_4 = """{{ "f bar f"|title }}"""
    title_5 = """{{ "foo-bar"|title }}"""
    title_6 = """{{ "foo\tbar"|title }}"""
    title_7 = """{{ "FOO\tBAR"|title }}"""
    title_8 = """{{ "foo (bar)"|title }}"""
    title_9 = """{{ "foo {bar}"|title }}"""
    title_10 = """{{ "foo [bar]"|title }}"""
    title_11 = """{{ "foo <bar>"|title }}"""
    title_12 = """{{ data|title }}"""
    truncate = (
        '{{ data|truncate(15, true, ">>>") }}|'
        '{{ data|truncate(15, false, ">>>") }}|'
        "{{ smalldata|truncate(15) }}"
    )
    truncate_very_short = (
        '{{ "foo bar baz"|truncate(9) }}|{{ "foo bar baz"|truncate(9, true) }}'
    )
    truncate_end_length = '{{ "Joel is a slug"|truncate(7, true) }}'
    upper = '{{ "foo"|upper }}'
    urlize_1 = '{{ "foo example.org bar"|urlize }}'
    urlize_2 = (
        'foo <a href="https://example.org" rel="noopener">' "example.org</a> bar"
    )
    urlize_3 = '{{ "foo http://www.example.com/ bar"|urlize }}'
    urlize_4 = '{{ "foo mailto:email@example.com bar"|urlize }}'
    urlize_5 = '{{ "foo email@example.com bar"|urlize }}'
    urlize_rel_policy = '{{ "foo http://www.example.com/ bar"|urlize }}'
    urlize_target_parameters = (
        '{{ "foo http://www.example.com/ bar"|urlize(target="_blank") }}'
    )
    urlize_extra_schemes_parameters = (
        '{{ "foo tel:+1-514-555-1234 ftp://localhost bar"|'
        'urlize(extra_schemes=["tel:", "ftp:"]) }}'
    )
    wordcount_1 = '{{ "foo bar baz"|wordcount }}'
    wordcount_2 = "{{ s|wordcount }}"
    block = "{% filter lower|escape %}<HEHE>{% endfilter %}"
    chaining = """{{ ['<foo>', '<bar>']|first|upper|escape }}"""
    sum_ = """{{ [1, 2, 3, 4, 5, 6]|sum }}"""
    sum_attributes = """{{ values|sum('value') }}"""
    sum_attributes_nested = """{{ values|sum('real.value') }}"""
    sum_attributes_tuple = """{{ values.items()|sum('1') }}"""
    abs_ = """{{ -1|abs }}|{{ 1|abs }}"""
    round_positive = (
        "{{ 2.7|round }}|{{ 2.1|round }}|"
        "{{ 2.1234|round(3, 'floor') }}|"
        "{{ 2.1|round(0, 'ceil') }}"
    )
    round_negative = (
        "{{ 21.3|round(-1)}}|"
        "{{ 21.3|round(-1, 'ceil')}}|"
        "{{ 21.3|round(-1, 'floor')}}"
    )
    xmlattr = (
        "{{ {'foo': 42, 'bar': 23, 'fish': none, "
        "'spam': missing, 'blub:blub': '<?>'}|xmlattr }}"
    )
    sort1 = "{{ [2, 3, 1]|sort }}|{{ [2, 3, 1]|sort(true) }}"
    sort2 = '{{ "".join(["c", "A", "b", "D"]|sort) }}'
    sort3 = """{{ ['foo', 'Bar', 'blah']|sort }}"""
    sort4 = """{{ items|sort(attribute='value')|join }}"""
    sort5 = """{{ items|sort(attribute='value.0')|join }}"""
    sort6 = """{{ items|sort(attribute='value1,value2')|join }}"""
    sort7 = """{{ items|sort(attribute='value2,value1')|join }}"""
    sort8 = (
        """{{ items|sort(attribute='value1.0,value2.0')|join }}"""
    )
    unique = '{{ "".join(["b", "A", "a", "b"]|unique) }}'
    unique_case_sensitive = '{{ "".join(["b", "A", "a", "b"]|unique(true)) }}'
    unique_attribute = "{{ items|unique(attribute='value')|join }}"
    min_1 = '{{ ["a", "B"]|min }}'
    min_2 = '{{ ["a", "B"]|min(case_sensitive=true) }}'
    min_3 = "{{ []|min }}"
    max_1 = '{{ ["a", "B"]|max }}'
    max_2 = '{{ ["a", "B"]|max(case_sensitive=true) }}'
    max_3 = "{{ []|max }}"
    min_attribute = '{{ items|min(attribute="value") }}'
    max_attribute = '{{ items|max(attribute="value") }}'
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
    groupby_multi_dot = """
        {%- for year, list in articles|groupby('date.year') -%}
            {{ year }}{% for x in list %}[{{ x.title }}]{% endfor %}|
        {%- endfor %}"""
    groupby_default = (
        "{% for city, items in users|groupby('city', default='NY') %}"
        "{{ city }}: {{ items|map(attribute='name')|join(', ') }}\n"
        "{% endfor %}"
    )
    groupby_case = (
        "{% for k, vs in data|groupby('k', case_sensitive=cs) %}"
        "{{ k }}: {{ vs|join(', ', attribute='v') }}\n"
        "{% endfor %}"
    )
    filter_tag = "{% filter upper|replace('FOO', 'foo') %}foobar{% endfilter %}"
    replace_1 = '{{ string|replace("o", 42) }}'
    replace_2 = '{{ string|replace("<", 42) }}'
    replace_3 = '{{ string|replace("o", ">x<") }}'
    forceescape = "{{ x|forceescape }}"
    safe_1 = '{{ "<div>foo</div>"|safe }}'
    safe_2 = '{{ "<div>foo</div>" }}'
    urlencode = "{{ value|urlencode }}"
    simple_map = '{{ ["1", "2", "3"]|map("int")|sum }}'
    map_sum = '{{ [[1,2], [3], [4,5,6]]|map("sum")|list }}'
    attribute_map = '{{ users|map(attribute="name")|join("|") }}'
    empty_map = '{{ none|map("upper")|list }}'
    map_default = '{{ users|map(attribute="lastname", default="smith")|join(", ") }}'
    map_default_list = '{{ users|map(attribute="lastname", default=["smith","x"])|join(", ") }}'
    map_default_str = '{{ users|map(attribute="lastname", default="")|join(", ") }}'
    simple_select = '{{ [1, 2, 3, 4, 5]|select("odd")|join("|") }}'
    bool_select = '{{ [none, false, 0, 1, 2, 3, 4, 5]|select|join("|") }}'
    simple_reject = '{{ [1, 2, 3, 4, 5]|reject("odd")|join("|") }}')
    bool_reject = '{{ [none, false, 0, 1, 2, 3, 4, 5]|reject|join("|") }}'
    simple_select_attr = '{{ users|selectattr("is_active")|map(attribute="name")|join("|") }}'
    simple_reject_attr = '{{ users|rejectattr("is_active")|map(attribute="name")|join("|") }}'
    func_select_attr = '{{ users|selectattr("id", "odd")|map(attribute="name")|join("|") }}'
    func_reject_attr = '{{ users|rejectattr("id", "odd")|map(attribute="name")|join("|") }}'
    json_dump = "{{ x|tojson }}"
    wordwrap = "{{ s|wordwrap(20) }}"
    filter_undefined = "{{ var|f }}"
    filter_undefined_in_if = "{%- if x is defined -%}{{ x|f }}{%- else -%}x{% endif %}"
    filter_undefined_in_elif = (
        "{%- if x is defined -%}{{ x }}{%- elif y is defined -%}"
        "{{ y|f }}{%- else -%}foo{%- endif -%}"
    )
    filter_undefined_in_else = (
        "{%- if x is not defined -%}foo{%- else -%}{{ x|f }}{%- endif -%}"
    )
    filter_undefined_in_nested_if = (
        "{%- if x is not defined -%}foo{%- else -%}{%- if y "
        "is defined -%}{{ y|f }}{%- endif -%}{{ x }}{%- endif -%}"
    )
    filter_undefined_in_condexpr_1 = "{{ x|f if x is defined else 'foo' }}"
    filter_undefined_in_condexpr_2 = "{{ 'foo' if x is not defined else x|f }}"


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
    # from jinja's tests/test_imports.py
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
    import_with_globals = (
        '{% import "module" as m %}{{ m.test() }}'  # with import_globals
    )
    # with import_globals
    import_with_globals_override = (
        '{% set foo = 41 %}{% import "module" as m %}{{ m.test() }}'
    )
    from_import_with_globals = '{% from "module" import test %}{{ test() }}'


class IncludesFixtures:
    # from jinja's tests/test_imports.py
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
    include_ignoring_missing_4 = (
        '{% include "missing" ignore missing without context %}'
    )
    context_include_with_overrides_main = (
        "{% for item in [1, 2, 3] %}{% include 'item' %}{% endfor %}"
    )
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
    import_from_with_context = (
        "{% set foobar = 42 %}{% from 'a' import x with context %}{{ x() }}"
    )


class InheritanceFixtures:
    # from jinja's tests/test_inheritance.py
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
    super_b = '{% extends "a" %}{% block data %}({{ ' "super() }}){% endblock %}"
    super_c = (
        '{% extends "b" %}{% block intro %}--{{ '
        "super() }}--{% endblock %}\n{% block data "
        "%}[{{ super() }}]{% endblock %}"
    )
    reuse_blocks = "{{ self.foo() }}|{% block foo %}42{% endblock %}|{{ self.foo() }}"
    preserve_blocks_a = (
        "{% if false %}{% block x %}A{% endblock %}" "{% endif %}{{ self.x() }}"
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
        "{% for item in seq %}[{% block item scoped %}" "{% endblock %}]{% endfor %}"
    )
    scoped_block = (
        "{% extends 'default.html' %}{% block item %}{{ item }}{% endblock %}"
    )
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
        "{% extends 'default1' %}{% block item %}" "{{ item }}{% endblock %}"
    )
    # required_with_scope_2 =  # raises TemplateSyntaxError
    # duplicate_required_or_scoped =  # raises TemplateSyntaxError
    # fixed_macro_scoping_bug =  # raises TemplateRuntimeError


class ExtensionsFixtures:
    # from jinja's tests/test_ext.py TestExtensions
    extend_late = '{% autoescape true %}{{ "<test>" }}{% endautoescape %}'
    loop_controls_1 = """
        {%- for item in [1, 2, 3, 4] %}
            {%- if item % 2 == 0 %}{% continue %}{% endif -%}
            {{ item }}
        {%- endfor %}"""
    loop_controls_2 = """
        {%- for item in [1, 2, 3, 4] %}
            {%- if item > 2 %}{% break %}{% endif -%}
            {{ item }}
        {%- endfor %}"""
    do = """
        {%- set items = [] %}
        {%- for char in "foo" %}
            {%- do items.append(loop.index0 ~ char) %}
        {%- endfor %}{{ items|join(', ') }}"""
    extension_nodes = "{% test %}"
    contextreference_node_passes_context = '{% set test_var="test_content" %}{% test %}'
    contextreference_node_can_pass_locals = (
        '{% for test_var in ["test_content"] %}{% test %}{% endfor %}'
    )
    preprocessor_extension = "{[[TEST]]}"
    streamfilter_extension = "Foo _(bar) Baz"
    debug = "Hello\n{% debug %}\nGoodbye"
    scope = """\
        {%- scope a=1, b=2, c=b, d=e, e=5 -%}
            {{ a }}|{{ b }}|{{ c }}|{{ d }}|{{ e }}
        {%- endscope -%}
        """
    auto_escape_scoped_setting_1 = """
        {{ "<HelloWorld>" }}
        {% autoescape false %}
            {{ "<HelloWorld>" }}
        {% endautoescape %}
        {{ "<HelloWorld>" }}
        """
    auto_escape_scoped_setting_2 = """
        {{ "<HelloWorld>" }}
        {% autoescape true %}
            {{ "<HelloWorld>" }}
        {% endautoescape %}
        {{ "<HelloWorld>" }}
        """
    auto_escape_nonvolatile_1 = '{{ {"foo": "<test>"}|xmlattr|escape }}'
    auto_escape_nonvolatile_2 = (
        '{% autoescape false %}{{ {"foo": "<test>"}'
        "|xmlattr|escape }}{% endautoescape %}"
    )
    auto_escape_volatile = (
        '{% autoescape foo %}{{ {"foo": "<test>"}'
        "|xmlattr|escape }}{% endautoescape %}"
    )
    auto_escape_scoping = (
        '{% autoescape true %}{% set x = "<x>" %}{{ x }}'
        '{% endautoescape %}{{ x }}{{ "<y>" }}'
    )
    auto_escape_volatile_scoping = """
        {% autoescape val %}
            {% macro foo(x) %}
                [{{ x }}]
            {% endmacro %}
            {{ foo().__class__.__name__ }}
        {% endautoescape %}
        {{ '<testing>' }}
        """
    auto_escape_overlay_scopes = """
        {{- x }}|{% set z = 99 %}
        {%- overlay %}
            {{- y }}|{{ z }}|{% for item in x %}[{{ item }}]{% endfor %}
        {%- endoverlay %}|
        {{- x -}}
        """


class LexerFixtures:
    # from jinja's tests/test_lexnparse.py TestLexer
    raw1 = (
        "{% raw %}foo{% endraw %}|"
        "{%raw%}{{ bar }}|{% baz %}{%       endraw    %}"
    )
    raw2 = "1  {%- raw -%}   2   {%- endraw -%}   3"
    raw3 = "bar\n{% raw %}\n  {{baz}}2 spaces\n{% endraw %}\nfoo"
    raw4 = "bar\n{%- raw -%}\n\n  \n  2 spaces\n space{%- endraw -%}\nfoo"
    # skip some
    bytefallback = """{{ 'foo'|pprint }}|{{ 'bär'|pprint }}"""
    lineno_with_strip = """\
<html>
    <body>
    {%- block content -%}
        <hr>
        {{ item }}
    {% endblock %}
    </body>
</html>"""
    start_comment = """{# foo comment
and bar comment #}
{% macro blub() %}foo{% endmacro %}
{{ blub() }}"""


class SyntaxFixtures:
    # from jinja's tests/test_lexnparse.py TestSyntax TestParser
    slicing = "{{ [1, 2, 3][:] }}|{{ [1, 2, 3][::-1] }}"
    attr = "{{ foo.bar }}|{{ foo['bar'] }}"
    subscript = "{{ foo[0] }}|{{ foo[-1] }}"
    tuple_ = "{{ () }}|{{ (1,) }}|{{ (1, 2) }}"
    math = "{{ (1 + 1 * 2) - 3 / 2 }}|{{ 2**3 }}"
    div = "{{ 3 // 2 }}|{{ 3 / 2 }}|{{ 3 % 2 }}"
    unary = "{{ +3 }}|{{ -3 }}"
    concat = "{{ [1, 2] ~ 'foo' }}"
    compare_1 = "{{ 1 > 0 }}"
    compare_2 = "{{ 1 >= 1 }}"
    compare_3 = "{{ 2 < 3 }}"
    compare_4 = "{{ 3 <= 4 }}"
    compare_5 = "{{ 4 == 4 }}"
    compare_6 = "{{ 4 != 5 }}"
    compare_parens = "{{ i * (j < 5) }}"
    compare_compound_1 = "{{ 4 < 2 < 3 }}"
    compare_compound_2 = "{{ a < b < c }}"
    compare_compound_3 = "{{ 4 > 2 > 3 }}"
    compare_compound_4 = "{{ a > b > c }}"
    compare_compound_5 = "{{ 4 > 2 < 3 }}"
    compare_compound_6 = "{{ a > b < c }}"
    inop = "{{ 1 in [1, 2, 3] }}|{{ 1 not in [1, 2, 3] }}"
    collection_literal_1 = "{{ [] }}"
    collection_literal_2 = "{{ {} }}"
    collection_literal_3 = "{{ () }}"
    numeric_literal_1 = "{{ 1 }}"
    numeric_literal_2 = "{{ 123 }}"
    numeric_literal_3 = "{{ 12_34_56 }}"
    numeric_literal_4 = "{{ 1.2 }}"
    numeric_literal_5 = "{{ 34.56 }}"
    numeric_literal_6 = "{{ 3_4.5_6 }}"
    numeric_literal_7 = "{{ 1e0 }}"
    numeric_literal_8 = "{{ 10e1 }}"
    numeric_literal_9 = "{{ 2.5e100 }}"
    numeric_literal_10 = "{{ 2.5e+100 }}"
    numeric_literal_11 = "{{ 25.6e-10 }}"
    numeric_literal_12 = "{{ 1_2.3_4e5_6 }}"
    numeric_literal_13 = "{{ 0 }}"
    numeric_literal_14 = "{{ 0_00 }}"
    numeric_literal_15 = "{{ 0b1001_1111 }}"
    numeric_literal_16 = "{{ 0o123 }}"
    numeric_literal_17 = "{{ 0o1_23 }}"
    numeric_literal_18 = "{{ 0x123abc }}"
    numeric_literal_19 = "{{ 0x12_3abc }}"
    boolean = "{{ true and false }}|{{ false or true }}|{{ not false }}"
    grouping = "{{ (true and false) or (false and true) and not false }}"
    django_attr = "{{ [1, 2, 3].0 }}|{{ [[1]].0.0 }}"
    conditional_expression = """{{ 0 if true else 1 }}"""
    short_conditional_expression = "<{{ 1 if false }}>"
    filter_priority = '{{ "foo"|upper + "bar"|upper }}'
    function_calls_1 = "{{ foo(foo, bar) }}"
    function_calls_2 = "{{ foo(foo, bar=42) }}"
    function_calls_3 = "{{ foo(foo, bar=23, *args) }}"
    function_calls_4 = "{{ foo(foo, *args, bar=23) }}"
    function_calls_5 = "{{ foo(a, b=c, *d, **e) }}"
    function_calls_6 = "{{ foo(*foo, bar=42) }}"
    function_calls_7 = "{{ foo(*foo, **bar) }}"
    function_calls_8 = "{{ foo(*foo, bar=42, **baz) }}"
    function_calls_9 = "{{ foo(foo, *args, bar=23, **baz) }}"
    tuple_expr_1 = "{{ () }}"
    tuple_expr_2 = "{{ (1, 2) }}"
    tuple_expr_3 = "{{ (1, 2,) }}"
    tuple_expr_4 = "{{ 1, }}"
    tuple_expr_5 = "{{ 1, 2 }}"
    tuple_expr_6 = "{% for foo, bar in seq %}...{% endfor %}"
    tuple_expr_7 = "{% for x in foo, bar %}...{% endfor %}"
    tuple_expr_8 = "{% for x in foo, %}...{% endfor %}"
    trailing_comma = "{{ (1, 2,) }}|{{ [1, 2,] }}|{{ {1: 2,} }}"
    block_end_name = "{% block foo %}...{% endblock foo %}"
    constant_casing_true = "{{ True }}|{{ true }}|{{ TRUE }}"
    constant_casing_false = "{{ False }}|{{ false }}|{{ FALSE }}"
    constant_casing_none = "{{ None }}|{{ none }}|{{ NONE }}"
    chaining_tests = "{{ 42 is string or 42 is number }}"
    string_concatenation = '{{ "foo" "bar" "baz" }}'
    not_in = """{{ not 42 in bar }}"""
    operator_precedence = """{{ 2 * 3 + 4 % 2 + 1 - 2 }}"""
    raw2 = "{% raw %}{{ FOO }} and {% BAR %}{% endraw %}"
    const = (
        "{{ true }}|{{ false }}|{{ none }}|"
        "{{ none is defined }}|{{ missing is defined }}"
    )
    neg_filter_priority = "{{ -1|foo }}"
    localset = """{% set foo = 0 %}\
{% for item in [1, 2] %}{% set foo = 1 %}{% endfor %}\
{{ foo }}"""
    parse_unary_1 = '{{ -foo["bar"] }}'
    parse_unary_2 = '{{ -foo["bar"]|abs }}'


class JinjaTestsFixtures:
    # from jinja's tests/test_tests.py TestTestsCase
    defined = "{{ missing is defined }}|{{ true is defined }}"
    even = """{{ 1 is even }}|{{ 2 is even }}"""
    odd = """{{ 1 is odd }}|{{ 2 is odd }}"""
    lower = """{{ "foo" is lower }}|{{ "FOO" is lower }}"""
    types = (
        ("none is none", True),
        ("false is none", False),
        ("true is none", False),
        ("42 is none", False),
        ("none is true", False),
        ("false is true", False),
        ("true is true", True),
        ("0 is true", False),
        ("1 is true", False),
        ("42 is true", False),
        ("none is false", False),
        ("false is false", True),
        ("true is false", False),
        ("0 is false", False),
        ("1 is false", False),
        ("42 is false", False),
        ("none is boolean", False),
        ("false is boolean", True),
        ("true is boolean", True),
        ("0 is boolean", False),
        ("1 is boolean", False),
        ("42 is boolean", False),
        ("0.0 is boolean", False),
        ("1.0 is boolean", False),
        ("3.14159 is boolean", False),
        ("none is integer", False),
        ("false is integer", False),
        ("true is integer", False),
        ("42 is integer", True),
        ("3.14159 is integer", False),
        ("(10 ** 100) is integer", True),
        ("none is float", False),
        ("false is float", False),
        ("true is float", False),
        ("42 is float", False),
        ("4.2 is float", True),
        ("(10 ** 100) is float", False),
        ("none is number", False),
        ("false is number", True),
        ("true is number", True),
        ("42 is number", True),
        ("3.14159 is number", True),
        ("complex is number", True),
        ("(10 ** 100) is number", True),
        ("none is string", False),
        ("false is string", False),
        ("true is string", False),
        ("42 is string", False),
        ('"foo" is string', True),
        ("none is sequence", False),
        ("false is sequence", False),
        ("42 is sequence", False),
        ('"foo" is sequence', True),
        ("[] is sequence", True),
        ("[1, 2, 3] is sequence", True),
        ("{} is sequence", True),
        ("none is mapping", False),
        ("false is mapping", False),
        ("42 is mapping", False),
        ('"foo" is mapping', False),
        ("[] is mapping", False),
        ("{} is mapping", True),
        ("mydict is mapping", True),
        ("none is iterable", False),
        ("false is iterable", False),
        ("42 is iterable", False),
        ('"foo" is iterable', True),
        ("[] is iterable", True),
        ("{} is iterable", True),
        ("range(5) is iterable", True),
        ("none is callable", False),
        ("false is callable", False),
        ("42 is callable", False),
        ('"foo" is callable', False),
        ("[] is callable", False),
        ("{} is callable", False),
        ("range is callable", True),
    )
    upper = '{{ "FOO" is upper }}|{{ "foo" is upper }}'
    equalto = (
        "{{ foo is eq 12 }}|"
        "{{ foo is eq 0 }}|"
        "{{ foo is eq (3 * 4) }}|"
        '{{ bar is eq "baz" }}|'
        '{{ bar is eq "zab" }}|'
        '{{ bar is eq ("ba" + "z") }}|'
        "{{ bar is eq bar }}|"
        "{{ bar is eq foo }}"
    )
    compare_aliases = (
        ("2 is eq 2", True),
        ("2 is eq 3", False),
        ("2 is ne 3", True),
        ("2 is ne 2", False),
        ("2 is lt 3", True),
        ("2 is lt 2", False),
        ("2 is le 2", True),
        ("2 is le 1", False),
        ("2 is gt 1", True),
        ("2 is gt 2", False),
        ("2 is ge 2", True),
        ("2 is ge 3", False),
    )
    sameas = "{{ foo is sameas false }}|{{ 0 is sameas false }}"
    no_paren_for_arg1 = "{{ foo is sameas none }}"
    escaped = "{{ x is escaped }}|{{ y is escaped }}"
    greaterthan = "{{ 1 is greaterthan 0 }}|{{ 0 is greaterthan 1 }}"
    lessthan = "{{ 0 is lessthan 1 }}|{{ 1 is lessthan 0 }}"
    multiple_tests = (
        "{{ 'us-west-1' is matching '(us-east-1|ap-northeast-1)'"
        " or 'stage' is matching '(dev|stage)' }}"
    )
    in_ = (
        '{{ "o" is in "foo" }}|'
        '{{ "foo" is in "foo" }}|'
        '{{ "b" is in "foo" }}|'
        "{{ 1 is in ((1, 2)) }}|"
        "{{ 3 is in ((1, 2)) }}|"
        "{{ 1 is in [1, 2] }}|"
        "{{ 3 is in [1, 2] }}|"
        '{{ "foo" is in {"foo": 1}}}|'
        '{{ "baz" is in {"bar": 1}}}'
    )
    name_undefined = "{{ x is f }}"
    name_undefined_in_if = "{% if x is defined %}{{ x is f }}{% endif %}"
