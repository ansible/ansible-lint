"""Implementation of yaml linting rule (yamllint integration)."""
import logging
import sys
from typing import TYPE_CHECKING, List

from yamllint.linter import run as run_yamllint

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.yaml_utils import load_yamllint_config

if TYPE_CHECKING:
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

    def __init__(self) -> None:
        """Construct a rule instance."""
        # customize id by adding the one reported by yamllint
        self.id = self.__class__.id

    def matchyaml(self, file: Lintable) -> List["MatchError"]:
        """Return matches found for a specific YAML text."""
        matches: List["MatchError"] = []
        filtered_matches: List["MatchError"] = []
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
                    message=problem.desc,
                    linenumber=problem.line,
                    details="",
                    filename=str(file.path),
                    tag=f"yaml[{problem.rule}]",
                )
            )

        if matches:
            lines = file.content.splitlines()
            for match in matches:
                # rule.linenumber starts with 1, not zero
                skip_list = get_rule_skips_from_line(lines[match.linenumber - 1])
                # print(skip_list)
                if match.rule.id not in skip_list and match.tag not in skip_list:
                    filtered_matches.append(match)
        return filtered_matches


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
                    'missing document start "---"',
                    'duplication of key "foo" in mapping',
                    "trailing spaces",
                ],
            ),
            (
                "examples/yamllint/valid.yml",
                "yaml",
                [],
            ),
        ),
        ids=(
            "invalid",
            "valid",
        ),
    )
    def test_yamllint(file: str, expected_kind: str, expected: List[str]) -> None:
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
