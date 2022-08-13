"""This file contains copies of jinja's test suite data which is BSD (3-clause) licensed."""

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
    tmpl = nodes.Template(
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

    tmpl = nodes.Template(
        [
            nodes.Extends(nodes.Const("layout.html")),
            title_block,
            render_title_macro,
            body_block,
        ]
    )

    tmpl = nodes.Template(
        [
            nodes.If(
                nodes.Name("expression", "load"),
                [nodes.Assign(nodes.Name("variable", "store"), nodes.Const(42))],
                [],
                [],
            )
        ]
    )

    tmpl = nodes.Template(
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

    tmpl = nodes.Template(
        [nodes.Assign(nodes.Name("x", "store"), nodes.Const(23)), for_loop]
    )

