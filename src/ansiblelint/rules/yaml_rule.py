"""Implementation of yaml linting rule (yamllint integration)."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from yamllint.linter import run as run_yamllint

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.yaml_utils import load_yamllint_config

if TYPE_CHECKING:
    from collections.abc import MutableMapping, MutableSequence
    from typing import Any

    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError

_logger = logging.getLogger(__name__)


class YamllintRule(AnsibleLintRule, TransformMixin):
    """Violations reported by yamllint."""

    id = "yaml"
    severity = "VERY_LOW"
    tags = ["formatting", "yaml"]
    version_changed = "5.0.0"
    config = load_yamllint_config()
    has_dynamic_tags = True
    link = "https://yamllint.readthedocs.io/en/stable/rules.html"
    # ensure this rule runs before most of other common rules
    _order = 1
    _ids = {
        "yaml[anchors]": "",
        "yaml[braces]": "",
        "yaml[brackets]": "",
        "yaml[colons]": "",
        "yaml[commas]": "",
        "yaml[comments-indentation]": "",
        "yaml[comments]": "",
        "yaml[document-end]": "",
        "yaml[document-start]": "",
        "yaml[empty-lines]": "",
        "yaml[empty-values]": "",
        "yaml[float-values]": "",
        "yaml[hyphens]": "",
        "yaml[indentation]": "",
        "yaml[key-duplicates]": "",
        "yaml[key-ordering]": "",
        "yaml[line-length]": "",
        "yaml[new-line-at-end-of-file]": "",
        "yaml[new-lines]": "",
        "yaml[octal-values]": "",
        "yaml[quoted-strings]": "",
        "yaml[trailing-spaces]": "",
        "yaml[truthy]": "",
    }

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches found for a specific YAML text."""
        matches: list[MatchError] = []
        if str(file.base_kind) != "text/yaml":
            return matches

        for problem in run_yamllint(  # type: ignore[no-untyped-call]
            file.content,
            YamllintRule.config,
            filepath=file.path,
        ):
            self.severity = "VERY_LOW"
            if problem.level == "error":
                self.severity = "MEDIUM"
            # Ignore truthy violation with github workflows ("on:" keys)
            if problem.rule == "truthy" and file.path.parent.parts[-2:] == (
                ".github",
                "workflows",
            ):
                continue
            matches.append(
                self.create_matcherror(
                    # yamllint does return lower-case sentences
                    message=problem.desc.capitalize(),
                    lineno=problem.line,
                    details="",
                    filename=file,
                    tag=f"yaml[{problem.rule}]",
                ),
            )
        return matches

    def transform(
        self: YamllintRule,
        match: MatchError,
        lintable: Lintable,
        data: MutableMapping[str, Any] | MutableSequence[Any] | str,
    ) -> None:
        """Transform yaml.

        :param match: MatchError instance
        :param lintable: Lintable instance
        :param data: data to transform
        """
        # This method does nothing because the YAML reformatting is implemented
        # in data dumper. Still presence of this method helps us with
        # documentation generation.


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected_kind", "expected"),
        (
            pytest.param(
                "examples/yamllint/invalid.yml",
                "yaml",
                [
                    'Missing document start "---"',
                    'Duplication of key "foo" in mapping',
                    "Trailing spaces",
                ],
                id="invalid",
            ),
            pytest.param("examples/yamllint/valid.yml", "yaml", [], id="valid"),
            pytest.param(
                "examples/yamllint/line-length.yml",
                "yaml",
                ["Line too long (166 > 160 characters)"],
                id="line-length",
            ),
            pytest.param(
                "examples/yamllint/multi-document.yaml",
                "yaml",
                [],
                id="multi-document",
            ),
            pytest.param(
                "examples/yamllint/skipped-rule.yml",
                "yaml",
                [],
                id="skipped-rule",
            ),
            pytest.param(
                "examples/playbooks/rule-yaml-fail.yml",
                "playbook",
                [
                    "Truthy value should be one of [false, true]",
                    "Truthy value should be one of [false, true]",
                    "Truthy value should be one of [false, true]",
                ],
                id="rule-yaml-fail",
            ),
            pytest.param(
                "examples/playbooks/rule-yaml-pass.yml",
                "playbook",
                [],
                id="rule-yaml-pass",
            ),
            pytest.param(
                "examples/yamllint/.github/workflows/ci.yml",
                "yaml",
                [],
                id="rule-yaml-github-workflow",
            ),
        ),
    )
    @pytest.mark.filterwarnings("ignore::ansible_compat.runtime.AnsibleWarning")
    def test_yamllint(
        file: str,
        expected_kind: str,
        expected: list[str],
        config_options: Options,
    ) -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(file)
        assert lintable.kind == expected_kind

        rules = RulesCollection(options=config_options)
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
        for rule in default_rules_collection:
            if rule.id == "yaml":
                assert rule.help is not None
                assert len(rule.help) > 100
                break
        else:  # pragma: no cover
            pytest.fail("No yaml rule found")
