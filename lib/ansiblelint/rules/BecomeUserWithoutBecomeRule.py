# Copyright (c) 2016 Will Thames <will@thames.id.au>
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

from functools import reduce

from ansiblelint.rules import AnsibleLintRule


def _get_subtasks(data):
    result = []
    block_names = [
            'tasks',
            'pre_tasks',
            'post_tasks',
            'handlers',
            'block',
            'always',
            'rescue']
    for name in block_names:
        if name in data:
            result += (data[name] or [])
    return result


def _nested_search(term, data):
    return ((term in data) or
            reduce((lambda x, y: x or _nested_search(term, y)), _get_subtasks(data), False))


def _become_user_without_become(becomeuserabove, data):
    if 'become' in data:
        # If become is in lineage of tree then correct
        return False
    if ('become_user' in data and _nested_search('become', data)):
        # If 'become_user' on tree and become somewhere below
        # we must check for a case of a second 'become_user' without a
        # 'become' in its lineage
        subtasks = _get_subtasks(data)
        return reduce((lambda x, y: x or _become_user_without_become(False, y)), subtasks, False)
    if _nested_search('become_user', data):
        # Keep searching down if 'become_user' exists in the tree below current task
        subtasks = _get_subtasks(data)
        return (len(subtasks) == 0 or
                reduce((lambda x, y: x or
                        _become_user_without_become(
                            becomeuserabove or 'become_user' in data, y)), subtasks, False))
    # If at bottom of tree, flag up if 'become_user' existed in the lineage of the tree and
    # 'become' was not. This is an error if any lineage has a 'become_user' but no become
    return becomeuserabove


class BecomeUserWithoutBecomeRule(AnsibleLintRule):
    id = '501'
    shortdesc = 'become_user requires become to work as expected'
    description = '``become_user`` without ``become`` will not actually change user'
    severity = 'VERY_HIGH'
    tags = ['task', 'oddity', 'ANSIBLE0017']
    version_added = 'historic'

    def matchplay(self, file, data):
        if file['type'] == 'playbook' and _become_user_without_become(False, data):
            return ({'become_user': data}, self.shortdesc)
