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

import os
import re
from typing import Any, Dict, Optional, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin


class UsingBareVariablesIsDeprecatedRule(AnsibleLintRule, TransformMixin):
    id = 'deprecated-bare-vars'
    shortdesc = 'Using bare variables is deprecated'
    description = (
        'Using bare variables is deprecated. Update your '
        'playbooks so that the environment value uses the full variable '
        'syntax ``{{ your_variable }}``'
    )
    severity = 'VERY_HIGH'
    tags = ['deprecations']
    version_added = 'historic'

    _jinja = re.compile(r"{[{%].*[%}]}", re.DOTALL)
    _glob = re.compile('[][*?]')

    @staticmethod
    def _get_loop_type(task: Dict[str, Any]) -> Optional[str]:
        return next((key for key in task if key.startswith("with_")), None)

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        loop_type = self._get_loop_type(task)
        if loop_type:
            if loop_type in [
                "with_nested",
                "with_together",
                "with_flattened",
                "with_filetree",
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
        self, varstring: str, task: Dict[str, Any], loop_type: str
    ) -> Union[bool, str]:
        if isinstance(varstring, str) and not self._jinja.match(varstring):
            valid = loop_type == 'with_fileglob' and bool(
                self._jinja.search(varstring) or self._glob.search(varstring)
            )

            valid |= loop_type == 'with_filetree' and bool(
                self._jinja.search(varstring) or varstring.endswith(os.sep)
            )
            if not valid:
                message = (
                    "Found a bare variable '{0}' used in a '{1}' loop."
                    + " You should use the full variable syntax ('{{{{ {0} }}}}')"
                )
                return message.format(task[loop_type], loop_type)
        return False

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to fix the MatchError."""
        target_task = self._seek(match.yaml_path, data)
        loop_type = self._get_loop_type(target_task)
        if not loop_type:
            # We should not get here because the transform only gets tasks that matched.
            # A task without a loop_type would not have matched.
            return
        loop = target_task[loop_type]

        fixed = False
        if isinstance(loop, (list, tuple)):
            for loop_index, loop_item in enumerate(loop):
                if loop_type == "with_subelements" and loop_index > 0:
                    break
                if self._needs_wrap(loop_item, loop_type):
                    target_task[loop_type][loop_index] = self._wrap(loop_item)
                    fixed = True
        elif self._needs_wrap(loop, loop_type):
            target_task[loop_type] = self._wrap(loop)
            fixed = True
        # call self._fixed(match) when data has been transformed to fix the error.
        if fixed:
            self._fixed(match)

    @staticmethod
    def _wrap(expression: str) -> str:
        return "{{ " + expression + " }}"

    def _needs_wrap(self, loop_item: Any, loop_type: str) -> bool:
        if not isinstance(loop_item, str):
            return False
        if loop_type in ["with_sequence", "with_ini", "with_inventory_hostnames"]:
            return False
        if self._jinja.match(loop_item):
            return False
        if loop_type == "with_fileglob":
            return not bool(
                self._jinja.search(loop_item) or self._glob.search(loop_item)
            )
        if loop_type == 'with_filetree':
            return not bool(self._jinja.search(loop_item) or loop_item.endswith(os.sep))
        return True
