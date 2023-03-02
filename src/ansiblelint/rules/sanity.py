"""Implementation of sanity rule."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule

# Copyright (c) 2018, Ansible Project


if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class CheckSanityIgnoreFiles(AnsibleLintRule):
    """Ignore entries in sanity ignore files must match an allow list."""

    id = "sanity"
    description = (
        "Identifies non-allowed entries in the `tests/sanity/ignore*.txt files."
    )
    severity = "MEDIUM"
    tags = ["experimental"]
    version_added = "v6.14.0"

    # Partner Engineering defines this list. Please contact PE for changes.

    allowed_ignores_v2_9 = [
        "validate-modules:deprecation-mismatch",  # Note: 2.9 expects a deprecated key in the METADATA. It was removed in later versions.
        "validate-modules:invalid-documentation",  # Note: The removed_at_date key in the deprecated section is invalid for 2.9.
    ]

    allowed_ignores_all = [
        "validate-modules:missing-gplv3-license",
        "action-plugin-docs",  # Added for Networking Collections
        "import-2.6",
        "import-2.6!skip",
        "import-2.7",
        "import-2.7!skip",
        "import-3.5",
        "import-3.5!skip",
        "compile-2.6",
        "compile-2.6!skip",
        "compile-2.7",
        "compile-2.7!skip",
        "compile-3.5",
        "compile-3.5!skip",
    ]

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Evaluate sanity ignore lists for disallowed ignores.

        :param file: Input lintable file that is a match for `sanity-ignore-file`
        :returns: List of errors matched to the input file
        """
        results: list[MatchError] = []
        test = ""

        if file.kind != "sanity-ignore-file":
            return []

        with open(file.abspath, encoding="utf-8") as ignore_file:
            entries = ignore_file.read().splitlines()

            ignores = self.allowed_ignores_all

            # If there is a ignore-2.9.txt file, add the v2_9 list of allowed ignores
            if "ignore-2.9.txt" in str(file.abspath):
                ignores = self.allowed_ignores_all + self.allowed_ignores_v2_9

            for line_num, entry in enumerate(entries, 1):
                if entry and entry[0] != "#":
                    try:
                        if "#" in entry:
                            entry, _ = entry.split("#")
                        (_, test) = entry.split()
                        if test not in ignores:
                            results.append(
                                self.create_matcherror(
                                    message=f"Ignore file contains {test} at line {line_num}, which is not a permitted ignore.",
                                    tag="sanity[cannot-ignore]",
                                    linenumber=line_num,
                                    filename=file,
                                )
                            )

                    except ValueError:
                        results.append(
                            self.create_matcherror(
                                message=f"Ignore file entry at {line_num} is formatted incorrectly. Please review.",
                                tag="sanity[bad-ignore]",
                                linenumber=line_num,
                                filename=file,
                            )
                        )

        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("test_file", "failures", "tags"),
        (
            pytest.param(
                "examples/sanity_ignores/tests/sanity/ignore-2.9.txt",
                0,
                "sanity[cannot-ignore]",
                id="pass",
            ),
            pytest.param(
                "examples/sanity_ignores/tests/sanity/ignore-2.15.txt",
                1,
                "sanity[bad-ignore]",
                id="fail0",
            ),
            pytest.param(
                "examples/sanity_ignores/tests/sanity/ignore-2.13.txt",
                1,
                "sanity[cannot-ignore]",
                id="fail1",
            ),
        ),
    )
    def test_sanity_ignore_files(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
        tags: str,
    ) -> None:
        """Test rule matches."""
        default_rules_collection.register(CheckSanityIgnoreFiles())
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == CheckSanityIgnoreFiles().id
            assert result.tag == tags
        assert len(results) == failures
