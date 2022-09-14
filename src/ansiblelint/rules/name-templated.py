"""Implementation of name-templated rule."""
from __future__ import annotations
from math import fabs

import re
from typing import TYPE_CHECKING, Any

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.constants import odict
    from ansiblelint.file_utils import Lintable

class NameTemplatedRule(AnsibleLintRule):
    """Rule for checking named template and ends template with {{ }}."""

    id = "name-templated"
    description = (
        "If {{ }} is found in a task name, require it's presence at the end after a sentence explaining the task"
    )
    severity = "MEDIUM"
    tags = ["idiom"]
    # version_added = "v6.5.0 (last update)"

    def matchplay(self, file: Lintable, data: odict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific play (entry in playbook)."""
        if file.kind != "playbook":
            return []
        if "name" not in data:
            return [
                self.create_matcherror(
                    message="All plays should be named.",
                    linenumber=data[LINE_NUMBER_KEY],
                    tag="name[play]",
                    filename=file,
                )
            ]
        match = self._check_name(
            data["name"], lintable=file, linenumber=data[LINE_NUMBER_KEY]
        )
        if match:
            return [match]
        return []

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str | MatchError:
        name = task.get("name")
        if not name:
            return self.create_matcherror(
                message="All tasks should be named.",
                linenumber=task[LINE_NUMBER_KEY],
                tag="name[missing]",
                filename=file,
            )
        return (
            self._check_name(name, lintable=file, linenumber=task[LINE_NUMBER_KEY])
            or False
        )

    def _check_name(
        self, name: str, lintable: Lintable | None, linenumber: int
    ) -> MatchError | None:
        # This rule will check the name and finds if it has {{ }} pattern at
        # the end of the sentence and also the named template should have the meaningful name
        if name.count("}}") == 1 and name.count("{{") == 1:
            if re.search('{{ .* }}$', name) == None:
                return self.create_matcherror(
                    message="If names has {{ }} it should be at the end of sentence.",
                    linenumber=linenumber,
                    tag="name[formatting]",
                    filename=lintable,
                )
        if name.count("}}") == 1 and name.count("{{") == 1:
            if re.search('{{ .* }}$', name):
                name_word = name.split(" ")[-2]
                print(name_word)
                if re.search(r'item.\d', name_word) or re.search(r'item', name_word):
                    return self.create_matcherror(
                    message="The named template should be meaningful in {{ }}",
                    linenumber=linenumber,
                    tag="name[formatting]",
                    filename=lintable,
                )
        if name.count("}}") > 1 or name.count("{{") > 1:
            if name.endswith("}}") == True:
                return self.create_matcherror(
                    message="If names has {{ }} it should be at the end of sentence.",
                    linenumber=linenumber,
                    tag="name[formatting]",
                    filename=lintable,
                )
        return None
    
        
