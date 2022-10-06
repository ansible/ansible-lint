"""Implementation of yaml linting rule (yamllint integration)."""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Iterable

from yamllint.linter import run as run_yamllint

from ansiblelint.constants import LINE_NUMBER_KEY, SKIPPED_RULES_KEY
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.yaml_utils import load_yamllint_config

if TYPE_CHECKING:
    from typing import Any, Generator

    from ansiblelint.errors import MatchError

_logger = logging.getLogger(__name__)


class YamllintRule(AnsibleLintRule):
    """Violations reported by yamllint."""

    id = "yaml"
    severity = "VERY_LOW"
    tags = ["formatting", "yaml"]
    version_added = "v5.0.0"
    config = load_yamllint_config()
    has_dynamic_tags = True
    link = "https://yamllint.readthedocs.io/en/stable/rules.html"
    # ensure this rule runs before most of other common rules
    _order = 1

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches found for a specific YAML text."""
        matches: list[MatchError] = []
        filtered_matches: list[MatchError] = []
        if str(file.base_kind) != "text/yaml":
            return matches

        for problem in run_yamllint(
            file.content, YamllintRule.config, filepath=file.path
        ):
            self.severity = "VERY_LOW"
            if problem.level == "error":
                self.severity = "MEDIUM"
            if problem.desc.endswith("(syntax)"):
                self.severity = "VERY_HIGH"
            matches.append(
                self.create_matcherror(
                    # yamllint does return lower-case sentences
                    message=problem.desc.capitalize(),
                    linenumber=problem.line,
                    details="",
                    filename=file,
                    tag=f"yaml[{problem.rule}]",
                )
            )

        # Now we save inside the file the skips, so they can be removed later,
        # especially as these skips can be about other rules than yaml one.
        _fetch_skips(file.data, file.line_skips)

        for match in matches:
            last_skips = set()

            for line, skips in file.line_skips.items():
                if line > match.linenumber:
                    break
                last_skips = skips
            if last_skips.intersection({"skip_ansible_lint", match.rule.id, match.tag}):
                continue
            filtered_matches.append(match)

        return filtered_matches


def _combine_skip_rules(data: Any) -> set[str]:
    """Return a consolidated list of skipped rules."""
    result = set(data.get(SKIPPED_RULES_KEY, []))
    tags = data.get("tags", [])
    if tags and (
        isinstance(tags, Iterable)
        and "skip_ansible_lint" in tags
        or tags == "skip_ansible_lint"
    ):
        result.add("skip_ansible_lint")
    return result


def _fetch_skips(data: Any, collector: dict[int, set[str]]) -> dict[int, set[str]]:
    """Retrieve a dictionary with line: skips by looking recursively in given JSON structure."""
    if hasattr(data, "get") and data.get(LINE_NUMBER_KEY):
        rules = _combine_skip_rules(data)
        if rules:
            collector[data.get(LINE_NUMBER_KEY)].update(rules)
    if isinstance(data, Iterable) and not isinstance(data, str):
        if isinstance(data, dict):
            for entry, value in data.items():
                _fetch_skips(value, collector)
        else:  # must be some kind of list
            for entry in data:
                if (
                    entry
                    and hasattr(data, "get")
                    and LINE_NUMBER_KEY in entry
                    and SKIPPED_RULES_KEY in entry
                    and entry[SKIPPED_RULES_KEY]
                ):
                    collector[entry[LINE_NUMBER_KEY]].update(entry[SKIPPED_RULES_KEY])
                _fetch_skips(entry, collector)
    return collector


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.config import options
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected_kind", "expected"),
        (
            (
                "examples/yamllint/invalid.yml",
                "yaml",
                [
                    'Missing document start "---"',
                    'Duplication of key "foo" in mapping',
                    "Trailing spaces",
                ],
            ),
            (
                "examples/yamllint/valid.yml",
                "yaml",
                [],
            ),
            (
                "examples/yamllint/multi-document.yaml",
                "yaml",
                [],
            ),
        ),
        ids=(
            "invalid",
            "valid",
            "multi-document",
        ),
    )
    def test_yamllint(file: str, expected_kind: str, expected: list[str]) -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(file)
        assert lintable.kind == expected_kind

        rules = RulesCollection(options=options)
        rules.register(YamllintRule())
        results = Runner(lintable, rules=rules).run()

        assert len(results) == len(expected), results
        for idx, result in enumerate(results):
            assert result.filename.endswith(file)
            assert expected[idx] in result.message
            assert isinstance(result.tag, str)
            assert result.tag.startswith("yaml[")

    def test_yamllint_has_help(default_rules_collection: RulesCollection) -> None:
        """Asserts that we loaded markdown documentation in help property."""
        for collection in default_rules_collection:
            if collection.id == "yaml":
                print(collection.id)
                assert collection.help is not None
                assert len(collection.help) > 100
                break
        else:
            pytest.fail("No yaml collection found")
