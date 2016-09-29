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

import re
from ansiblelint import AnsibleLintRule


class UsingBareVariablesIsDeprecatedRule(AnsibleLintRule):
    id = 'ANSIBLE0015'
    shortdesc = 'Using bare variables is deprecated'
    description = 'Using bare variables is deprecated. Update your' + \
        'playbooks so that the environment value uses the full variable' + \
        'syntax ("{{your_variable}}").'
    tags = ['formatting']

    _jinja = re.compile("\{\{.*\}\}")

    def matchtask(self, file, task):
        loop_type = next((key for key in task
                          if key.startswith("with_")), None)
        if loop_type:
            if loop_type in ["with_nested", "with_together", "with_flattened"]:
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
            elif loop_type in ["with_sequence", "with_ini",
                               "with_inventory_hostnames"]:
                pass
            else:
                return self._matchvar(task[loop_type], task, loop_type)

    def _matchvar(self, varstring, task, loop_type):
        if (isinstance(varstring, basestring) and
                not self._jinja.match(varstring)):
            message = "Found a bare variable '{0}' used in a '{1}' loop." + \
                      " You should use the full variable syntax ('{{{{{0}}}}}')"
            return message.format(task[loop_type], loop_type)
