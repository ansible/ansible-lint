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

from ansiblelint import AnsibleLintRule


class MismatchedBracketRule(AnsibleLintRule):
    id = 'ANSIBLE0003'
    shortdesc = 'Mismatched { and }'
    description = 'If lines contain more { than } or vice ' + \
                  'versa then templating can fail nastily'
    tags = ['templating']

    def _check_value(self, v):
        results = []

        if isinstance(v, dict):
            # Transform into a list to simplify processing
            # since we do not care about the keys
            v = v.values()

        if isinstance(v, list):
            for i in v:
                output = self._check_value(i)
                if output:
                    results += output
        elif isinstance(v, (str, unicode)):
            if v.count("{") != v.count("}"):
                results.append((v, "mismatched braces"))
        else:
            # not a type we care about
            pass

        return results

    def matchplay(self, file, play):
        return self._check_value(play)
