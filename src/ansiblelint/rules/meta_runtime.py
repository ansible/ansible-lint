"""Implementation of meta-runtime rule."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from packaging.specifiers import SpecifierSet

from ansiblelint.rules import AnsibleLintRule

# Copyright (c) 2018, Ansible Project


if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class CheckRequiresAnsibleVersion(AnsibleLintRule):
    """Required ansible version in meta/runtime.yml must be a supported version."""

    id = "meta-runtime"
    description = (
        "The ``requires_ansible`` key in runtime.yml must specify "
        "a supported platform version of ansible-core and be a valid version."
    )
    severity = "VERY_HIGH"
    tags = ["metadata"]
    version_added = "v6.11.0 (last update)"

    # Refer to https://access.redhat.com/support/policy/updates/ansible-automation-platform
    # Also add devel to this list
    supported_ansible = ["2.9.10", "2.11.", "2.12.", "2.13.", "2.14.", "2.15."]

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Find violations inside meta files.

        :param file: Input lintable file that is a match for `meta-runtime`
        :returns: List of errors matched to the input file
        """
        results = []

        if file.kind != "meta-runtime":
            return []

        version_required = file.data.get("requires_ansible", None)

        if version_required:
            if not any(
                version in version_required for version in self.supported_ansible
            ):
                results.append(
                    self.create_matcherror(
                        message="requires_ansible key must be set to a supported version.",
                        tag="meta-runtime[unsupported-version]",
                        filename=file,
                    )
                )

            try:
                SpecifierSet(version_required)
            except ValueError:
                results.append(
                    self.create_matcherror(
                        message="'requires_ansible' is not a valid requirement specification",
                        tag="meta-runtime[invalid-version]",
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
                "examples/meta_runtime_version_checks/pass/meta/runtime.yml",
                0,
                "meta-runtime[unsupported-version]",
                id="pass",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_0/meta/runtime.yml",
                1,
                "meta-runtime[unsupported-version]",
                id="fail0",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_1/meta/runtime.yml",
                1,
                "meta-runtime[unsupported-version]",
                id="fail1",
            ),
            pytest.param(
                "examples/meta_runtime_version_checks/fail_2/meta/runtime.yml",
                1,
                "meta-runtime[invalid-version]",
                id="fail2",
            ),
        ),
    )
    def test_meta_supported_version(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
        tags: str,
    ) -> None:
        """Test rule matches."""
        default_rules_collection.register(CheckRequiresAnsibleVersion())
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == CheckRequiresAnsibleVersion().id
            assert result.tag == tags
        assert len(results) == failures
