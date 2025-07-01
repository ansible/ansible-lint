"""Implementation of PatternRule."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

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
    _ids = {
        "pattern[missing-meta]": "Missing meta sub-directory in pattern directory.",
        "pattern[missing-playbook]": "Missing playbooks sub-directory in pattern directory.",
        "pattern[missing-readme]": "Missing README.md file in pattern directory.",
        "pattern[name-mismatch]": "Pattern directory name does not match the name value in pattern.json file.",
    }

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches found for a specific file."""
        if file.kind != "pattern":
            return []
        results = []

        pattern_dir = file.path.parent.parent.resolve()
        meta_dir = pattern_dir / "meta"

        # Check the presence of required meta sub-dir inside a pattern directory
        if not meta_dir.is_dir():
            results.append(
                self.create_matcherror(
                    message=(
                        f"Pattern directory '{pattern_dir}' contains pattern.json but is missing the required 'meta' directory."
                    ),
                    tag=f"{self.id}[missing-meta]",
                    filename=file,
                ),
            )

        # Check the presence of required README.md file in a pattern directory
        readme_file = pattern_dir / "README.md"
        if not readme_file.exists():
            results.append(
                self.create_matcherror(
                    message=(
                        f"Pattern directory '{pattern_dir}' is missing required README.md file"
                    ),
                    tag=f"{self.id}[missing-readme]",
                    filename=file,
                ),
            )

        # Validate that pattern name matches with the name key in pattern.json file
        values = values_from_pattern_json(file.path)
        pattern_name_from_json_file = values[1]
        pattern_name_from_dir = pattern_dir.name
        if pattern_name_from_json_file != pattern_name_from_dir:
            results.append(
                self.create_matcherror(
                    message=(
                        f"Pattern directory name '{pattern_name_from_dir}' does not match the name key in pattern.json file: '{pattern_name_from_json_file}'."
                    ),
                    tag=f"{self.id}[name-mismatch]",
                    filename=file,
                ),
            )

        # Check the presence of playbooks directory and file matching entries in the pattern.json file
        playbooks_dir = pattern_dir / "playbooks"
        missing_playbook_items = []

        if not playbooks_dir.is_dir():
            missing_playbook_items.append("playbooks directory")
        else:
            values = values_from_pattern_json(file.path)
            playbook = values[0]
            playbook_file = playbooks_dir / playbook
            if not playbook_file.exists():
                missing_playbook_items.append("playbook file")

        if missing_playbook_items:
            results.append(
                self.create_matcherror(
                    message=(
                        f"Pattern directory '{pattern_dir}' is missing required: {', '.join(missing_playbook_items)}"
                    ),
                    tag=f"{self.id}[missing-playbook]",
                    filename=file,
                ),
            )

        return results


def values_from_pattern_json(file: Path) -> list[str]:
    """Extract playbook name and pattern name values from pattern.json file."""
    playbook_name: str = ""
    pattern_name: str = ""
    try:
        with Path(file).open(encoding="utf-8") as f:
            data = json.load(f)
        try:
            playbook_name = data["aap_resources"]["controller_job_templates"][0][
                "playbook"
            ]
            pattern_name = data["name"]
        except KeyError as exc:
            msg = "Could not extract playbook name"
            raise KeyError(msg) from exc
    except FileNotFoundError as exc:
        msg = "Pattern file not found."
        raise FileNotFoundError(msg) from exc
    return [playbook_name, pattern_name]


if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected"),
        (
            pytest.param(
                "examples/collections/extensions/patterns/valid_pattern/meta/pattern.json",
                [],
                id="valid-pattern",
            ),
            pytest.param(
                "examples/collections/extensions/patterns/invalid_pattern/pattern.json",
                [
                    "pattern[missing-meta]",
                    "pattern[missing-readme]",
                    "pattern[missing-playbook]",
                    "pattern[name-mismatch]",
                ],
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
            assert result.rule.id == PatternRule.id, result
            assert result.tag == expected[index]
