"""Implementation of meta-unsupported-ansible rule."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule

# Copyright (c) 2018, Ansible Project


if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable

META_TAG_VALID = """
galaxy_info:
    galaxy_tags: ['database', 'my s q l', 'MYTAG']
    categories: 'my_category_not_in_a_list'
"""


class CheckRequiresAnsibleVersion(AnsibleLintRule):
    """Required ansible version in meta/runtime.yml must be a supported version."""

    id = "meta-unsupported-ansible"
    description = (
        "The ``requires_ansible`` key in runtime.yml must specify "
        "a supported platform version of ansible-core."
    )
    severity = "VERY_HIGH"
    tags = ["metadata"]
    version_added = "v6.11.0 (last update)"

    supported_ansible = ["2.9.10", "2.11", "2.12", "2.13", "2.14"]

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Find violations inside meta files."""
        if file.kind != "meta-runtime":
            return []

        version_required = file.data.get("requires_ansible", None)

        if version_required:
            if not any(
                version in version_required for version in self.supported_ansible
            ):
                return [
                    self.create_matcherror(
                        message="requires_ansible key must be set to a supported version.",
                        filename=file,
                    )
                ]

        return []


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                "examples/meta_runtime_version_checks/pass/meta/runtime.yml",
                0,
                id="pass",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_0/meta/runtime.yml",
                1,
                id="fail0",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_1/meta/runtime.yml",
                1,
                id="fail1",
            ),
        ),
    )
    def test_loop_var_prefix(
        default_rules_collection: RulesCollection, test_file: str, failures: int
    ) -> None:
        """Test rule matches."""
        default_rules_collection.register(CheckRequiresAnsibleVersion())
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == CheckRequiresAnsibleVersion().id
        assert len(results) == failures
