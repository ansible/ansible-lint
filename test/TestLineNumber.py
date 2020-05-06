# Copyright (c) 2020 Albin Vass <albin.vass@gmail.com>
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

import ansiblelint.utils

from ansiblelint import AnsibleLintRule


MAGIC_NUMBER = 7007


class LinenumberRule(AnsibleLintRule):
    id = 'TEST0003'
    shortdesc = 'Linenumber is returned'
    description = 'This is a rule that return a linenumber'

    tags = {'fake', 'dummy', 'test3'}

    def matchplay(self, file, play):
        return [('Linenumber returned', self.shortdesc, MAGIC_NUMBER)]


def test_rule_linenumber(monkeypatch):

    def mock_response(*args, **kwargs):
        return [{'skipped_rules': []}]

    monkeypatch.setattr(ansiblelint.utils,
                        "append_skipped_rules",
                        mock_response)

    text = "- debug:\n    msg: a"
    rule = LinenumberRule()
    matches = rule.matchyaml(dict(path="", type='tasklist'), text)
    assert matches[0].linenumber == MAGIC_NUMBER
