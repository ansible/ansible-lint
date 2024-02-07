"""Implementation of playbook-extension rule."""

# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError


class PlaybookExtensionRule(AnsibleLintRule):
    """Use ".yml" or ".yaml" playbook extension."""

    id = "playbook-extension"
    description = 'Playbooks should have the ".yml" or ".yaml" extension'
    severity = "MEDIUM"
    tags = ["formatting"]
    done: list[str] = []
    version_added = "v4.0.0"

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        result: list[MatchError] = []
        if file.kind != "playbook":
            return result
        path = str(file.path)
        ext = file.path.suffix
        if ext not in [".yml", ".yaml"] and path not in self.done:
            self.done.append(path)
            result.append(self.create_matcherror(filename=file))
        return result


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection

    @pytest.mark.parametrize(
        ("file", "expected"),
        (pytest.param("examples/playbooks/play-without-extension", 1, id="fail"),),
    )
    def test_playbook_extension(file: str, expected: int) -> None:
        """The ini_file module does not accept preserve mode."""
        rules = RulesCollection()
        rules.register(PlaybookExtensionRule())
        results = Runner(Lintable(file, kind="playbook"), rules=rules).run()
        assert len(results) == expected
        for result in results:
            assert result.tag == "playbook-extension"
