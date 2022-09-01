"""Implementation of playbook-extension rule."""
# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import os

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule


class PlaybookExtension(AnsibleLintRule):
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
        ext = os.path.splitext(path)
        if ext[1] not in [".yml", ".yaml"] and path not in self.done:
            self.done.append(path)
            result.append(self.create_matcherror(filename=file))
        return result
