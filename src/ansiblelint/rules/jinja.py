"""Rule for checking content of jinja template strings."""
from __future__ import annotations

import logging
import re
import sys
from collections import namedtuple
from typing import TYPE_CHECKING, Any

import black
import jinja2
from ansible.errors import AnsibleError, AnsibleFilterError, AnsibleParserError
from ansible.parsing.yaml.objects import AnsibleUnicode
from jinja2.exceptions import TemplateSyntaxError

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import parse_yaml_from_file, template
from ansiblelint.yaml_utils import deannotate, nested_items_path

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError


_logger = logging.getLogger(__package__)
KEYWORDS_WITH_IMPLICIT_TEMPLATE = ("changed_when", "failed_when", "until", "when")

Token = namedtuple("Token", "lineno token_type value")


class JinjaRule(AnsibleLintRule):
    """Rule that looks inside jinja2 templates."""

    id = "jinja"
    severity = "LOW"
    tags = ["formatting"]
    version_added = "v6.5.0"
    _ansible_error_re = re.compile(
        r"^(?P<error>.*): (?P<detail>.*)\. String: (?P<string>.*)$", flags=re.MULTILINE
    )

    env = jinja2.Environment(trim_blocks=False)
    _tag2msg = {
        "invalid": "Syntax error in jinja2 template: {value}",
        "spacing": "Jinja2 spacing could be improved: {value} -> {reformatted}",
    }

    def _msg(self, tag: str, value: str, reformatted: str) -> str:
        """Generate error message."""
        return self._tag2msg[tag].format(value=value, reformatted=reformatted)

    # pylint: disable=too-many-branches
    def matchtask(  # noqa: C901
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str | MatchError:
        for key, v, _ in nested_items_path(task):
            if isinstance(v, str):

                try:
                    template(
                        basedir=file.dir if file else ".",
                        value=v,
                        variables=deannotate(task.get("vars", {})),
                        fail_on_error=True,  # we later decide which ones to ignore or not
                    )
                # ValueError RepresenterError
                except AnsibleError as exc:
                    bypass = False
                    orig_exc = exc.orig_exc if getattr(exc, "orig_exc", None) else exc
                    match = self._ansible_error_re.match(
                        getattr(orig_exc, "message", str(orig_exc))
                    )
                    if (
                        isinstance(exc, AnsibleFilterError)
                        or "unable to locate collection" in orig_exc.message
                    ):
                        bypass = True
                    elif re.match(
                        r"^the template file (.*) could not be found for the lookup$",
                        orig_exc.message,
                    ) or re.match(r"could not locate file in lookup", orig_exc.message):
                        bypass = True
                    elif isinstance(orig_exc, AnsibleParserError):
                        # "An unhandled exception occurred while running the lookup plugin '...'. Error was a <class 'ansible.errors.AnsibleParserError'>, original message: Invalid filename: 'None'. Invalid filename: 'None'"

                        # An unhandled exception occurred while running the lookup plugin 'template'. Error was a <class 'ansible.errors.AnsibleError'>, original message: the template file ... could not be found for the lookup. the template file ... could not be found for the lookup

                        # ansible@devel (2.14) new behavior:
                        # AnsibleError(TemplateSyntaxError): template error while templating string: Could not load "ipwrap": 'Invalid plugin FQCN (ansible.netcommon.ipwrap): unable to locate collection ansible.netcommon'. String: Foo {{ buildset_registry.host | ipwrap }}. Could not load "ipwrap": 'Invalid plugin FQCN (ansible.netcommon.ipwrap): unable to locate collection ansible.netcommon'
                        bypass = True
                    elif (
                        isinstance(orig_exc, (AnsibleError, TemplateSyntaxError))
                        and match
                    ):
                        error = match.group("error")
                        detail = match.group("detail")
                        # string = match.group("string")
                        if error.startswith("template error while templating string"):
                            bypass = False
                        elif detail.startswith("unable to locate collection"):
                            _logger.debug("Ignored AnsibleError: %s", exc)
                            bypass = True
                        else:
                            bypass = False
                    elif re.match(r"^lookup plugin (.*) not found$", exc.message):
                        # lookup plugin 'template' not found
                        bypass = True

                    # AnsibleFilterError: 'obj must be a list of dicts or a nested dict'
                    # AnsibleError: template error while templating string: expected token ':', got '}'. String: {{ {{ '1' }} }}
                    # AnsibleError: template error while templating string: unable to locate collection ansible.netcommon. String: Foo {{ buildset_registry.host | ipwrap }}
                    if not bypass:
                        return self.create_matcherror(
                            message=str(exc),
                            linenumber=task[LINE_NUMBER_KEY],
                            filename=file,
                            tag=f"{self.id}[invalid]",
                        )

                reformatted, details, tag = self.check_whitespace(
                    v, key=key, lintable=file
                )
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
            for key, v, path in nested_items_path(data):
                if isinstance(v, AnsibleUnicode):
                    reformatted, details, tag = self.check_whitespace(
                        v, key=key, lintable=file
                    )
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

    def lex(self, text: str) -> list[Token]:
        """Parse jinja template."""
        # https://github.com/pallets/jinja/issues/1711
        self.env.keep_trailing_newline = True

        self.env.lstrip_blocks = False
        self.env.trim_blocks = False
        tokens = [
            Token(lineno=t[0], token_type=t[1], value=t[2]) for t in self.env.lex(text)
        ]
        new_text = self.unlex(tokens)
        if text != new_text:
            _logger.debug(
                "Unable to perform full roundtrip lex-unlex on jinja template (expected when '-' modifier is used): {text} -> {new_text}"
            )
        return tokens

    def unlex(self, tokens: list[Token]) -> str:
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
        self, text: str, key: str, lintable: Lintable | None = None
    ) -> tuple[str, str, str]:
        """Check spacing inside given jinja2 template string.

        We aim to match Python Black formatting rules.
        :raises NotImplementedError: On few cases where valid jinja is not valid Python.

        :returns: (string, string, string)  reformatted text, detailed error, error tag
        """

        def cook(value: str, implicit: bool = False) -> str:
            """Prepare an implicit string for jinja parsing when needed."""
            if not implicit:
                return value
            if value.startswith("{{") and value.endswith("}}"):
                # maybe we should make this an error?
                return value
            return f"{{{{ {value} }}}}"

        def uncook(value: str, implicit: bool = False) -> str:
            """Restore an string to original form when it was an implicit one."""
            if not implicit:
                return value
            return value[3:-3]

        tokens = []
        details = ""
        begin_types = ("variable_begin", "comment_begin", "block_begin")
        end_types = ("variable_end", "comment_end", "block_end")
        implicit = False

        # implicit templates do not have the {{ }} wrapping
        if (
            key in KEYWORDS_WITH_IMPLICIT_TEMPLATE
            and lintable
            and lintable.kind
            in (
                "playbook",
                "task",
            )
        ):
            implicit = True
            text = cook(text, implicit=implicit)

        expr_str = None
        expr_type = None
        verb_skipped = True
        lineno = 1
        try:
            for token in self.lex(text):

                if (
                    expr_type
                    and expr_type.startswith("{%")
                    and token.token_type in ("name", "whitespace")
                    and not verb_skipped
                ):
                    # on {% blocks we do not take first word as part of the expression
                    tokens.append(token)
                    if token.token_type != "whitespace":
                        verb_skipped = True
                elif token.token_type in begin_types:
                    tokens.append(token)
                    expr_type = token.value  # such {#, {{, {%
                    expr_str = ""
                    verb_skipped = False
                elif token.token_type in end_types and expr_str is not None:
                    # process expression
                    # pylint: disable=unsupported-membership-test
                    if isinstance(expr_str, str) and "\n" in expr_str:
                        raise NotImplementedError()
                    expr_str = blacken(expr_str)
                    if tokens[
                        -1
                    ].token_type != "whitespace" and not expr_str.startswith(" "):
                        expr_str = " " + expr_str
                    if not expr_str.endswith(" "):
                        expr_str += " "
                    tokens.append(Token(lineno, "data", expr_str))
                    tokens.append(token)
                    expr_str = None
                    expr_type = None
                elif expr_str is not None:
                    expr_str += token.value
                else:
                    tokens.append(token)
                lineno = token.lineno

        except jinja2.exceptions.TemplateSyntaxError as exc:
            return "", str(exc.message), "invalid"
        # https://github.com/PyCQA/pylint/issues/7433 - py311 only
        # pylint: disable=c-extension-no-member
        except (NotImplementedError, black.parsing.InvalidInput) as exc:
            # black is not able to recognize all valid jinja2 templates, so we
            # just ignore InvalidInput errors.
            # NotImplementedError is raised internally for expressions with
            # newlines, as we decided to not touch them yet.
            # These both are documented as known limitations.
            _logger.debug("Ignored jinja internal error %s", exc)
            return uncook(text, implicit), "", "spacing"

        # finalize
        reformatted = self.unlex(tokens)
        failed = reformatted != text
        reformatted = uncook(reformatted, implicit)
        details = (
            f"Jinja2 template rewrite recommendation: `{reformatted}`."
            if failed
            else ""
        )
        return reformatted, details, "spacing"


def blacken(text: str) -> str:
    """Format Jinja2 template using black."""
    return black.format_str(
        text, mode=black.FileMode(line_length=sys.maxsize, string_normalization=False)
    ).rstrip("\n")


if "pytest" in sys.modules:  # noqa: C901

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.fixture(name="error_expected_lines")
    def fixture_error_expected_lines() -> list[int]:
        """Return list of expected error lines."""
        return [31, 34, 37, 40, 43, 46, 72]

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

        error_expected_lineno = [14, 15, 16, 17, 18, 19, 32]
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
            # pytest.param(
            #     "{{ foo | bool else [ ] }}",
            #     "{{ foo | bool else [] }}",
            #     "spacing",
            #     id="13",
            # ),
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
                "{% if a | int <= 8 -%} iptables{%- else -%} iptables-nft{%- endif %}",
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
            pytest.param("{{ a +~'b' }}", "{{ a + ~'b' }}", "spacing", id="36"),
            pytest.param(
                "{{ (a[: -4] *~ b) }}", "{{ (a[:-4] * ~b) }}", "spacing", id="37"
            ),
            pytest.param("{{ [a,~ b] }}", "{{ [a, ~b] }}", "spacing", id="38"),
            # Not supported yet due to being accepted by black:
            pytest.param("{{ item.0.user }}", "{{ item.0.user }}", "spacing", id="39"),
            # Not supported by back, while jinja allows ~ to be binary operator:
            pytest.param("{{ a ~ b }}", "{{ a ~ b }}", "spacing", id="40"),
            pytest.param(
                "--format='{{'{{'}}.Size{{'}}'}}'",
                "--format='{{ '{{' }}.Size{{ '}}' }}'",
                "spacing",
                id="41",
            ),
            pytest.param(
                "{{ list_one + {{ list_two | max }} }}",
                "{{ list_one + {{list_two | max}} }}",
                "spacing",
                id="42",
            ),
        ),
    )
    def test_jinja(text: str, expected: str, tag: str) -> None:
        """Tests our ability to spot spacing errors inside jinja2 templates."""
        rule = JinjaRule()

        reformatted, details, returned_tag = rule.check_whitespace(
            text, key="name", lintable=Lintable("playbook.yml")
        )
        assert tag == returned_tag, details
        assert expected == reformatted

    @pytest.mark.parametrize(
        ("text", "expected", "tag"),
        (
            pytest.param(
                "1+2",
                "1 + 2",
                "spacing",
                id="0",
            ),
            pytest.param(
                "- 1",
                "-1",
                "spacing",
                id="1",
            ),
            # Ensure that we do not choke with double templating on implicit
            # and instead we remove them braces.
            pytest.param("{{ o | bool }}", "o | bool", "spacing", id="2"),
        ),
    )
    def test_jinja_implicit(text: str, expected: str, tag: str) -> None:
        """Tests our ability to spot spacing errors implicit jinja2 templates."""
        rule = JinjaRule()
        # implicit jinja2 are working only inside playbooks and tasks
        lintable = Lintable(name="playbook.yml", kind="playbook")
        reformatted, details, returned_tag = rule.check_whitespace(
            text, key="when", lintable=lintable
        )
        assert tag == returned_tag, details
        assert expected == reformatted

    @pytest.mark.parametrize(
        ("lintable", "matches"),
        (pytest.param("examples/playbooks/vars/rule_jinja_vars.yml", 0, id="0"),),
    )
    def test_jinja_file(lintable: str, matches: int) -> None:
        """Tests our ability to process var filesspot spacing errors."""
        collection = RulesCollection()
        collection.register(JinjaRule())
        errs = Runner(lintable, rules=collection).run()
        assert len(errs) == matches
        for err in errs:
            assert isinstance(err, JinjaRule)
            assert errs[0].tag == "jinja[invalid]"
            assert errs[0].rule.id == "jinja"

    def test_jinja_invalid() -> None:
        """Tests our ability to spot spacing errors inside jinja2 templates."""
        collection = RulesCollection()
        collection.register(JinjaRule())
        success = "examples/playbooks/rule-jinja-invalid.yml"
        errs = Runner(success, rules=collection).run()
        assert len(errs) == 1
        assert errs[0].tag == "jinja[invalid]"
        assert errs[0].rule.id == "jinja"

    def test_jinja_valid() -> None:
        """Tests our ability to parse jinja, even when variables may not be defined."""
        collection = RulesCollection()
        collection.register(JinjaRule())
        success = "examples/playbooks/rule-jinja-valid.yml"
        errs = Runner(success, rules=collection).run()
        assert len(errs) == 0
