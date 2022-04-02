"""Rule for checking whitespace around variables."""
# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import re
import sys
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ansible.parsing.yaml.objects import AnsibleUnicode

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import parse_yaml_from_file
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError


class VariableHasSpacesRule(AnsibleLintRule):
    """Variables should have spaces before and after: {{ var_name }}."""

    id = "var-spacing"
    description = "Variables should have spaces before and after: ``{{ var_name }}``"
    severity = "LOW"
    tags = ["formatting"]
    version_added = "v4.0.0"

    bracket_regex = re.compile(r"{{[^{\n' -]|[^ '\n}-]}}", re.MULTILINE | re.DOTALL)
    exclude_json_re = re.compile(r"[^{]{'\w+': ?[^{]{.*?}}", re.MULTILINE | re.DOTALL)

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        for _, v, _ in nested_items_path(task):
            if isinstance(v, str):
                cleaned = self.exclude_json_re.sub("", v)
                if bool(self.bracket_regex.search(cleaned)):
                    return self.shortdesc.format(var_name=v)
        return False

    def matchyaml(self, file: Lintable) -> List["MatchError"]:
        """Return matches for variables defined in vars files."""
        data: Dict[str, Any] = {}
        raw_results: List["MatchError"] = []
        results: List["MatchError"] = []

        if str(file.kind) == "vars":
            data = parse_yaml_from_file(str(file.path))
            for k, v, path in nested_items_path(data):
                if isinstance(v, AnsibleUnicode):
                    cleaned = self.exclude_json_re.sub("", v)
                    if bool(self.bracket_regex.search(cleaned)):
                        path_elem = [
                            f"[{i}]" if isinstance(i, int) else i for i in path + [k]
                        ]
                        raw_results.append(
                            self.create_matcherror(
                                filename=file,
                                linenumber=v.ansible_pos[1],
                                message=self.shortdesc.format(var_name=v),
                                details=f".{'.'.join(path_elem)}",
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


if "pytest" in sys.modules:  # noqa: C901

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.fixture(name="error_expected_lines")
    def fixture_error_expected_lines() -> List[int]:
        """Return list of expected error lines."""
        return [24, 27, 30, 56, 67]

    @pytest.fixture(name="test_playbook")
    def fixture_test_playbook() -> str:
        """Return test cases playbook path."""
        return "examples/playbooks/var-spacing.yml"

    @pytest.fixture(name="lint_error_lines")
    def fixture_lint_error_lines(test_playbook: str) -> List[int]:
        """Get VarHasSpacesRules linting results on test_playbook."""
        collection = RulesCollection()
        collection.register(VariableHasSpacesRule())
        lintable = Lintable(test_playbook)
        results = Runner(lintable, rules=collection).run()
        return list(map(lambda item: item.linenumber, results))

    def test_var_spacing(
        error_expected_lines: List[int], lint_error_lines: List[int]
    ) -> None:
        """Ensure that expected error lines are matching found linting error lines."""
        # list unexpected error lines or non-matching error lines
        error_lines_difference = list(
            set(error_expected_lines).symmetric_difference(set(lint_error_lines))
        )
        assert len(error_lines_difference) == 0

    # Test for vars file
    @pytest.fixture(name="error_expected_details_varsfile")
    def fixture_error_expected_details_varsfile() -> List[str]:
        """Return list of expected error details."""
        return [
            ".bad_var_1",
            ".bad_var_2",
            ".bad_var_3",
            ".invalid_multiline_nested_json",
            ".invalid_nested_json",
        ]

    @pytest.fixture(name="error_expected_lines_varsfile")
    def fixture_error_expected_lines_varsfile() -> List[int]:
        """Return list of expected error lines."""
        return [12, 13, 14, 27, 33]

    @pytest.fixture(name="test_varsfile_path")
    def fixture_test_varsfile_path() -> str:
        """Return test cases vars file path."""
        return "examples/playbooks/vars/var-spacing.yml"

    @pytest.fixture(name="lint_error_results_varsfile")
    def fixture_lint_error_results_varsfile(
        test_varsfile_path: str,
    ) -> List["MatchError"]:
        """Get VarHasSpacesRules linting results on test_vars."""
        collection = RulesCollection()
        collection.register(VariableHasSpacesRule())
        lintable = Lintable(test_varsfile_path)
        results = Runner(lintable, rules=collection).run()
        return results

    def test_var_spacing_vars(
        error_expected_details_varsfile: List[str],
        error_expected_lines_varsfile: List[int],
        lint_error_results_varsfile: List["MatchError"],
    ) -> None:
        """Ensure that expected error details are matching found linting error details."""
        details = list(map(lambda item: item.details, lint_error_results_varsfile))
        # list unexpected error details or non-matching error details
        error_details_difference = list(
            set(error_expected_details_varsfile).symmetric_difference(set(details))
        )
        assert len(error_details_difference) == 0

        lines = list(map(lambda item: item.linenumber, lint_error_results_varsfile))
        # list unexpected error lines or non-matching error lines
        error_lines_difference = list(
            set(error_expected_lines_varsfile).symmetric_difference(set(lines))
        )
        assert len(error_lines_difference) == 0
