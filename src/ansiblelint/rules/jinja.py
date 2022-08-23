"""Rule for checking content of jinja template strings."""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

import jinja2
from ansible.parsing.yaml.objects import AnsibleUnicode

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import LINE_NUMBER_KEY, parse_yaml_from_file
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError


_logger = logging.getLogger(__package__)


class JinjaRule(AnsibleLintRule):
    """Rule that looks inside jinja2 templates."""

    id = "jinja"
    severity = "LOW"
    tags = ["formatting"]
    version_added = "v6.5.0"

    env = jinja2.Environment()
    _tag2msg = {
        "invalid": "Syntax error in jinja2 template: {value}",
        "spacing": "Jinja2 spacing could be improved: {value} -> {reformatted}",
    }

    def _msg(self, tag: str, value: str, reformatted: str) -> str:
        """Generate error message."""
        return self._tag2msg[tag].format(value=value, reformatted=reformatted)

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str | MatchError:
        for _, v, _ in nested_items_path(task):
            if isinstance(v, str):
                reformatted, details, tag = self.check_whitespace(v)
                if reformatted != v:
                    return self.create_matcherror(
                        message=self._msg(tag=tag, value=v, reformatted=reformatted),
                        linenumber=task[LINE_NUMBER_KEY],
                        details=details,
                        filename=file,
                        tag=f"{self.id}[{tag}]",
                    )
        return False

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches for variables defined in vars files."""
        data: dict[str, Any] = {}
        raw_results: list[MatchError] = []
        results: list[MatchError] = []

        if str(file.kind) == "vars":
            data = parse_yaml_from_file(str(file.path))
            # pylint: disable=unused-variable
            for k, v, path in nested_items_path(data):
                if isinstance(v, AnsibleUnicode):
                    reformatted, details, tag = self.check_whitespace(v)
                    if reformatted != v:
                        results.append(
                            self.create_matcherror(
                                message=self._msg(
                                    tag=tag, value=v, reformatted=reformatted
                                ),
                                linenumber=v.ansible_pos[1],
                                details=details,
                                filename=file,
                                tag=f"{self.id}[{tag}]",
                            )
                        )
            if raw_results:
                lines = file.content.splitlines()
                for match in raw_results:
                    # linenumber starts with 1, not zero
                    skip_list = get_rule_skips_from_line(lines[match.linenumber - 1])
                    if match.rule.id not in skip_list and match.tag not in skip_list:
                        results.append(match)
        else:
            results.extend(super().matchyaml(file))
        return results

    def lex(self, text: str) -> list[tuple[int, str, str]]:
        """Parse jinja template."""
        # https://github.com/pallets/jinja/issues/1711
        self.env.keep_trailing_newline = True

        self.env.lstrip_blocks = False
        self.env.trim_blocks = False
        tokens = list(self.env.lex(text))
        new_text = self.unlex(tokens)
        if text != new_text:
            _logger.debug(
                "Unable to perform full roundrip lex-unlex on jinja template (expected when '-' modifier is used): {text} -> {new_text}"
            )
        return tokens

    def unlex(self, tokens: list[Any]) -> str:
        """Return original text by compiling the lex output."""
        result = ""
        last_lineno = 1
        last_value = ""
        for lineno, _, value in tokens:
            if lineno > last_lineno and "\n" not in last_value:
                result += "\n"
            result += value
            last_lineno = lineno
            last_value = value
        return result

    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def check_whitespace(  # noqa: max-complexity: 13
        self, text: str
    ) -> tuple[str, str, str]:
        """Check spacing inside given jinja2 template string.

        We aim to match Python Black formatting rules.

        :returns: (string, string, string)  reformatted text, detailed error, error tag
        """
        prev_token_type: str = ""
        prev_value: str = ""
        tokens = []
        details = ""
        begin_types = ("variable_begin", "comment_begin", "block_begin")
        end_types = ("variable_end", "comment_end", "block_end")

        spaced_operators = {
            "+",
            "-",
            "/",
            "//",
            "*",
            "%",
            "**",
            "~",
            "==",
            "!=",
            ">",
            ">=",
            "<",
            "<=",
            "=",
            "|",
        }
        unspaced_operators = {"[", "]", "(", ")", "{", "}", "."}
        space_folowed_operators = {",", ";", ":"}
        pre_spaced_operators = spaced_operators
        post_spaced_operators = spaced_operators | space_folowed_operators

        def in_expression(tokens: list[Any]) -> str:
            """Check if tokens represent an unfinished expression.

            Returns last unclosed {[( or empty string.
            """
            opened: list[str] = []
            pairs = {
                ")": "(",
                "]": "[",
                "}": "{",
            }
            for _, token_type, value in tokens:  # reverse order
                if token_type == "operator":
                    if value in ("(", "[", "{"):
                        opened.append(value)
                    elif value in (")", "]", "}"):
                        opened.remove(pairs[value])
            if opened:
                return opened[0]
            return ""

        try:
            previous_tokens = self.lex(text)
        except jinja2.exceptions.TemplateSyntaxError as exc:
            return "", str(exc.message), "invalid"

        tokens = previous_tokens

        # phase 1 : add missing whitespace
        prev_token_type = ""
        prev_value = ""
        prev_lineno = 1
        tokens = []
        for lineno, token_type, value in previous_tokens:

            if (
                token_type in begin_types
                and "-" in value
                and prev_token_type == "data"
                and not prev_value.endswith(" ")
                and lineno == prev_lineno
            ):
                # "foo{%-" -> "foo {%-"
                tokens[-1] = (tokens[-1][0], tokens[-1][1], tokens[-1][2] + " ")

            if token_type in end_types and prev_token_type not in (
                "whitespace",
                "comment",
            ):
                tokens.append((lineno, "whitespace", " "))
            elif prev_token_type in begin_types and token_type not in (
                "whitespace",
                "comment",
            ):
                tokens.append((lineno, "whitespace", " "))
            if token_type in ("comment", "whitespace") and "\n" not in value:
                # ensure comments/whitespace do not have more than one leading
                # or trailing space in them, while not touching \n \r
                stripped = " " + value.strip(" \t") + " "
                if stripped == "  ":
                    stripped = " "
                if stripped != value:
                    value = stripped
            if (
                token_type != "whitespace"
                and token_type == "operator"
                and value in pre_spaced_operators
                and prev_token_type != "whitespace"
            ):
                tokens.append((lineno, "whitespace", " "))
            if (
                prev_token_type == "operator"
                and prev_value in post_spaced_operators
                and token_type != "whitespace"
            ):
                if not (
                    prev_value == ":"
                    and prev_token_type == "operator"
                    and in_expression(tokens) == "["
                ):
                    avoid_spacing = False
                    for token in tokens[:-1][::-1]:
                        if token[1] in begin_types:
                            avoid_spacing = True
                            break
                        if token[1] == "operator" and token[2] in (":", "", "["):
                            avoid_spacing = True
                            break
                        if token[1] in ("operator", "integer", "string", "name"):
                            avoid_spacing = False
                            break
                    if not avoid_spacing:
                        tokens.append((lineno, "whitespace", " "))

            tokens.append((lineno, token_type, value))
            prev_token_type = token_type
            prev_value = value
            prev_lineno = lineno

        # phase 2 : remove undesirable whitespace
        prev_token_type = ""
        prev_value = ""
        previous_tokens = tokens
        tokens = []
        # pylint: disable=too-many-nested-blocks
        for lineno, token_type, value in previous_tokens:

            if prev_token_type == "whitespace" and "\n" not in prev_value:

                if (
                    token_type == "operator"
                    and value == ":"
                    and tokens[-2][1] == "operator"
                    and tokens[-2][2] == "["
                ):
                    tokens.pop()
                elif token_type == "operator" and value in {
                    *unspaced_operators,
                    "=",
                    ":",
                }:
                    # effective removal of whitespace
                    if value in ("=", "]", ")", "}") and in_expression(tokens):
                        tokens.pop()
                    elif tokens[-2][1] == "operator" and tokens[-2][2] in {
                        *unspaced_operators,
                        "=",
                    }:
                        if tokens[-2][2] not in ("=", ",") or (
                            tokens[-2][2] in ("=", ":") and in_expression(tokens)
                        ):
                            tokens.pop()
                elif in_expression(tokens):
                    if tokens[-2][1] == "operator":
                        if tokens[-2][2] in (
                            "=",
                            "[",
                            "{",
                            "(",
                        ):
                            tokens.pop()
                        elif tokens[-2][2] != "," and in_expression(tokens) == "[":
                            tokens.pop()
                else:
                    if tokens[-2][1] == "operator" and tokens[-2][2] in ("-", "+"):
                        avoid_spacing = False
                        for token in tokens[:-2][::-1]:
                            if token[1] in begin_types:
                                avoid_spacing = True
                                break
                            if token[1] in ("operator", "integer", "string", "name"):
                                avoid_spacing = False
                                break
                        if avoid_spacing:
                            tokens.pop()

            tokens.append((lineno, token_type, value))
            prev_token_type = token_type
            prev_value = value

        # finalize
        reformatted = self.unlex(tokens)
        failed = reformatted != text
        details = (
            f"Jinja2 template rewrite recommendation: `{reformatted}`."
            if failed
            else ""
        )
        return reformatted, details, "spacing"


if "pytest" in sys.modules:  # noqa: C901

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.fixture(name="error_expected_lines")
    def fixture_error_expected_lines() -> list[int]:
        """Return list of expected error lines."""
        return [31, 34, 37, 40, 43, 46, 72, 83]

    # 21 68
    @pytest.fixture(name="lint_error_lines")
    def fixture_lint_error_lines() -> list[int]:
        """Get VarHasSpacesRules linting results on test_playbook."""
        collection = RulesCollection()
        collection.register(JinjaRule())
        lintable = Lintable("examples/playbooks/jinja-spacing.yml")
        results = Runner(lintable, rules=collection).run()
        return list(map(lambda item: item.linenumber, results))

    def test_jinja_spacing_playbook(
        error_expected_lines: list[int], lint_error_lines: list[int]
    ) -> None:
        """Ensure that expected error lines are matching found linting error lines."""
        # list unexpected error lines or non-matching error lines
        error_lines_difference = list(
            set(error_expected_lines).symmetric_difference(set(lint_error_lines))
        )
        assert len(error_lines_difference) == 0

    def test_jinja_spacing_vars() -> None:
        """Ensure that expected error details are matching found linting error details."""
        collection = RulesCollection()
        collection.register(JinjaRule())
        lintable = Lintable("examples/playbooks/vars/jinja-spacing.yml")
        results = Runner(lintable, rules=collection).run()

        error_expected_lineno = [14, 15, 16, 17, 18, 19, 32, 38]
        assert len(results) == len(error_expected_lineno)
        for idx, err in enumerate(results):
            assert err.linenumber == error_expected_lineno[idx]

    @pytest.mark.parametrize(
        ("text", "expected", "tag"),
        (
            pytest.param(
                "{{-x}}{#a#}{%1%}",
                "{{- x }}{# a #}{% 1 %}",
                "spacing",
                id="add-missing-space",
            ),
            pytest.param("", "", "spacing", id="1"),
            pytest.param("foo", "foo", "spacing", id="2"),
            pytest.param("{##}", "{# #}", "spacing", id="3"),
            pytest.param("{#  #}", "{# #}", "spacing", id="4"),
            pytest.param(
                "{{-aaa|xx   }}foo\nbar{#some#}\n{%%}",
                "{{- aaa | xx }}foo\nbar{# some #}\n{% %}",
                "spacing",
                id="5",
            ),
            pytest.param(
                "Shell with jinja filter", "Shell with jinja filter", "spacing", id="6"
            ),
            pytest.param(
                "{{{'dummy_2':1}|true}}",
                "{{ {'dummy_2': 1} | true }}",
                "spacing",
                id="7",
            ),
            pytest.param("{{{foo:{}}}}", "{{ {foo: {}} }}", "spacing", id="8"),
            pytest.param(
                "{{ {'test': {'subtest': variable}} }}",
                "{{ {'test': {'subtest': variable}} }}",
                "spacing",
                id="9",
            ),
            pytest.param(
                "http://foo.com/{{\n  case1 }}",
                "http://foo.com/{{\n  case1 }}",
                "spacing",
                id="10",
            ),
            pytest.param("{{foo(123)}}", "{{ foo(123) }}", "spacing", id="11"),
            pytest.param("{{ foo(a.b.c) }}", "{{ foo(a.b.c) }}", "spacing", id="12"),
            pytest.param(
                "{{ foo | bool else [ ] }}",
                "{{ foo | bool else [] }}",
                "spacing",
                id="13",
            ),
            pytest.param(
                "{{foo(x =['server_options'])}}",
                "{{ foo(x=['server_options']) }}",
                "spacing",
                id="14",
            ),
            pytest.param(
                '{{ [ "host", "NA"] }}', '{{ ["host", "NA"] }}', "spacing", id="15"
            ),
            pytest.param(
                "{{ {'dummy_2': {'nested_dummy_1': value_1,\n    'nested_dummy_2': value_2}} |\ncombine(dummy_1) }}",
                "{{ {'dummy_2': {'nested_dummy_1': value_1,\n    'nested_dummy_2': value_2}} |\ncombine(dummy_1) }}",
                "spacing",
                id="17",
            ),
            pytest.param("{{ & }}", "", "invalid", id="18"),
            pytest.param(
                "{{ good_format }}/\n{{- good_format }}\n{{- good_format -}}\n",
                "{{ good_format }}/\n{{- good_format }}\n{{- good_format -}}\n",
                "spacing",
                id="19",
            ),
            pytest.param(
                "{{ {'a': {'b': 'x', 'c': y}} }}",
                "{{ {'a': {'b': 'x', 'c': y}} }}",
                "spacing",
                id="20",
            ),
            pytest.param(
                "2*(1+(3-1)) is {{ 2 * {{ 1 + {{ 3 - 1 }}}} }}",
                "2*(1+(3-1)) is {{ 2 * {{1 + {{3 - 1}}}} }}",
                "spacing",
                id="21",
            ),
            pytest.param(
                '{{ "absent"\nif (v is version("2.8.0", ">=")\nelse "present" }}',
                "",
                "invalid",
                id="22",
            ),
            pytest.param(
                '{{lookup("x",y+"/foo/"+z+".txt")}}',
                '{{ lookup("x", y + "/foo/" + z + ".txt") }}',
                "spacing",
                id="23",
            ),
            pytest.param(
                "{{ x | map(attribute='value') }}",
                "{{ x | map(attribute='value') }}",
                "spacing",
                id="24",
            ),
            pytest.param(
                "{{ r(a= 1,b= True,c= 0.0,d= '') }}",
                "{{ r(a=1, b=True, c=0.0, d='') }}",
                "spacing",
                id="25",
            ),
            pytest.param("{{ r(1,[]) }}", "{{ r(1, []) }}", "spacing", id="26"),
            pytest.param(
                "{{ lookup([ddd ]) }}", "{{ lookup([ddd]) }}", "spacing", id="27"
            ),
            pytest.param(
                "{{ [ x ] if x is string else x }}",
                "{{ [x] if x is string else x }}",
                "spacing",
                id="28",
            ),
            pytest.param(
                # "{% if a|int <= 8 -%} iptables {%- else -%} iptables-nft {%- endif %}",
                "{% if a|int <= 8 -%} iptables {%- else -%} iptables-nft {%- endif %}",
                "{% if a | int <= 8 -%} iptables {%- else -%} iptables-nft {%- endif %}",
                "spacing",
                id="29",
            ),
            pytest.param(
                # "- 2" -> "-2", minus does not get separated when there is no left side
                "{{ - 2 }}",
                "{{ -2 }}",
                "spacing",
                id="30",
            ),
            pytest.param(
                # "-2" -> "-2", minus does get an undesired spacing
                "{{ -2 }}",
                "{{ -2 }}",
                "spacing",
                id="31",
            ),
            pytest.param(
                # array ranges do not have space added
                "{{ foo[2:4] }}",
                "{{ foo[2:4] }}",
                "spacing",
                id="32",
            ),
            pytest.param(
                # array ranges have the extra space removed
                "{{ foo[2: 4] }}",
                "{{ foo[2:4] }}",
                "spacing",
                id="33",
            ),
            pytest.param(
                # negative array index
                "{{ foo[-1] }}",
                "{{ foo[-1] }}",
                "spacing",
                id="34",
            ),
            pytest.param(
                # negative array index, repair
                "{{ foo[- 1] }}",
                "{{ foo[-1] }}",
                "spacing",
                id="35",
            ),
        ),
    )
    def test_jinja(text: str, expected: str, tag: str) -> None:
        """Tests our ability to spot spacing errors inside jinja2 templates."""
        rule = JinjaRule()
        reformatted, details, returned_tag = rule.check_whitespace(text)
        assert tag == returned_tag, details
        assert expected == reformatted
