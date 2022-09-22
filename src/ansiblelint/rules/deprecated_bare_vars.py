"""Implementation of deprecated-bare-vars rule."""

# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class UsingBareVariablesIsDeprecatedRule(AnsibleLintRule):
    """Using bare variables is deprecated."""

    id = "deprecated-bare-vars"
    description = (
        "Using bare variables is deprecated. Update your "
        "playbooks so that the environment value uses the full variable "
        "syntax ``{{ your_variable }}``"
    )
    severity = "VERY_HIGH"
    tags = ["deprecations"]
    version_added = "historic"

    _jinja = re.compile(r"{[{%].*[%}]}", re.DOTALL)
    _glob = re.compile("[][*?]")

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        loop_type = next((key for key in task if key.startswith("with_")), None)
        if loop_type:
            if loop_type in [
                "with_nested",
                "with_together",
                "with_flattened",
                "with_filetree",
                "with_community.general.filetree",
            ]:
                # These loops can either take a list defined directly in the task
                # or a variable that is a list itself.  When a single variable is used
                # we just need to check that one variable, and not iterate over it like
                # it's a list. Otherwise, loop through and check all items.
                items = task[loop_type]
                if not isinstance(items, (list, tuple)):
                    items = [items]
                for var in items:
                    return self._matchvar(var, task, loop_type)
            elif loop_type == "with_subelements":
                return self._matchvar(task[loop_type][0], task, loop_type)
            elif loop_type in ["with_sequence", "with_ini", "with_inventory_hostnames"]:
                pass
            else:
                return self._matchvar(task[loop_type], task, loop_type)
        return False

    def _matchvar(
        self, varstring: str, task: dict[str, Any], loop_type: str
    ) -> bool | str:
        if isinstance(varstring, str) and not self._jinja.match(varstring):
            valid = loop_type == "with_fileglob" and bool(
                self._jinja.search(varstring) or self._glob.search(varstring)
            )

            valid |= loop_type == "with_filetree" and bool(
                self._jinja.search(varstring) or varstring.endswith(os.sep)
            )
            if not valid:
                message = (
                    "Possible bare variable '{0}' used in a '{1}' loop."
                    + " You should use the full variable syntax ('{{{{ {0} }}}}') or convert it to a list if that is not really a variable."
                )
                return message.format(task[loop_type], loop_type)
        return False
