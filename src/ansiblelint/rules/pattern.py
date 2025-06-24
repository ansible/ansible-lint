"""Implementation of PatternRule."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class PatternRule(AnsibleLintRule):
    """Rule for checking pattern directory."""

    id = "pattern"
    description = "Confirm that pattern has valid directory structure."
    severity = "MEDIUM"
    tags = ["metadata"]
    version_changed = "25.7.0"

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "pattern":
            return []

        results = []

        pattern_dir = file.path.parent.parent.resolve()
        meta_dir = pattern_dir / "meta"

        # Check if meta directory exists
        if not meta_dir.is_dir():
            results.append(
                self.create_matcherror(
                    message=(
                        f"Pattern directory '{pattern_dir}' contains pattern.json but is missing the required 'meta' directory."
                    ),
                    tag=self.id,
                    filename=file,
                ),
            )
            return results

        # Define required files relative to the pattern dir
        required_paths = [
            pattern_dir / "README.md",
            pattern_dir / "playbooks" / "site.yml",
        ]
        missing = [
            str(p.relative_to(pattern_dir)) for p in required_paths if not p.exists()
        ]

        # Check execution_environments directory if it exists
        ee_dir = pattern_dir / "execution_environments"
        if ee_dir.exists():
            expected_file = ee_dir / "execution_environment.yml"
            # Must contain only execution_environment.yml
            files = list(ee_dir.iterdir())
            if not expected_file.exists():
                missing.append("execution_environments/execution_environment.yml")
            if len(files) != 1 or files[0].name != "execution_environment.yml":
                results.append(
                    self.create_matcherror(
                        message=(
                            f"'execution_environments' directory in '{pattern_dir}' must contain only 'execution_environment.yml' file."
                        ),
                        tag=self.id,
                        filename=file,
                    ),
                )

        if missing:
            results.append(
                self.create_matcherror(
                    message=(
                        f"Pattern directory '{pattern_dir}' is missing required files: {', '.join(missing)}"
                    ),
                    tag=self.id,
                    filename=file,
                ),
            )

        return results


if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/collections/extensions/patterns/valid_pattern/meta/pattern.json",
                ["pattern"],
                id="valid-pattern",
            ),
            pytest.param(
                "examples/collections/extensions/patterns/invalid_pattern/pattern.json",
                ["pattern"],
                id="invalid-pattern",
            ),
        ),
    )
    def test_pattern(
        default_rules_collection: RulesCollection,
        file: str,
        expected: list[str],
    ) -> None:
        """Validate that rule works as intended."""
        results = Runner(file, rules=default_rules_collection).run()

        assert len(results) == len(expected)
        for index, result in enumerate(results):
            assert result.tag == expected[index]
