"""Implementation of meta-runtime rule."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from packaging.specifiers import SpecifierSet

from ansiblelint.rules import AnsibleLintRule

# Copyright (c) 2018, Ansible Project


if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class CheckRequiresAnsibleVersion(AnsibleLintRule):
    """Required ansible version in meta/runtime.yml must be a supported version."""

    id = "meta-runtime"
    description = (
        "The ``requires_ansible`` key in runtime.yml must specify "
        "a supported platform version of ansible-core and be a valid version value "
        "in x.y.z format."
    )
    severity = "VERY_HIGH"
    tags = ["metadata"]
    version_added = "v6.11.0 (last update)"

    _ids = {
        "meta-runtime[unsupported-version]": "'requires_ansible' key must refer to a currently supported version",
        "meta-runtime[invalid-version]": "'requires_ansible' is not a valid requirement specification",
    }

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Find violations inside meta files.

        :param file: Input lintable file that is a match for `meta-runtime`
        :returns: List of errors matched to the input file
        """
        results = []

        if file.kind != "meta-runtime":
            return []

        requires_ansible = file.data.get("requires_ansible", None)

        if requires_ansible:
            if self.options and not any(
                version in requires_ansible
                for version in self.options.supported_ansible
            ):
                supported_ansible = [f">={x}0" for x in self.options.supported_ansible]
                msg = f"'requires_ansible' key must refer to a currently supported version such as: {', '.join(supported_ansible)}"

                results.append(
                    self.create_matcherror(
                        message=msg,
                        tag="meta-runtime[unsupported-version]",
                        filename=file,
                    ),
                )

            try:
                SpecifierSet(requires_ansible)
            except ValueError:
                results.append(
                    self.create_matcherror(
                        message="'requires_ansible' is not a valid requirement specification",
                        tag="meta-runtime[invalid-version]",
                        filename=file,
                    ),
                )

        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failures", "tags"),
        (
            pytest.param(
                "examples/meta_runtime_version_checks/pass_0/meta/runtime.yml",
                0,
                "meta-runtime[unsupported-version]",
                id="pass0",
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
    def test_default_meta_supported_version(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
        tags: str,
    ) -> None:
        """Test for default supported ansible versions."""
        default_rules_collection.register(CheckRequiresAnsibleVersion())
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.rule.id == CheckRequiresAnsibleVersion().id
            assert result.tag == tags
        assert len(results) == failures

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                "examples/meta_runtime_version_checks/pass_1/meta/runtime.yml",
                0,
                id="pass1",
            ),
        ),
    )
    def test_added_meta_supported_version(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
    ) -> None:
        """Test for added supported ansible versions in the config."""
        default_rules_collection.register(CheckRequiresAnsibleVersion())
        default_rules_collection.options.supported_ansible_also = ["2.9"]
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
