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

# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.file_utils import Lintable

from .rules import EMatcherRule, UnsetVariableMatcherRule


class TestRule(unittest.TestCase):
    def test_rule_matching(self) -> None:
        ematcher = EMatcherRule.EMatcherRule()
        lintable = Lintable('examples/playbooks/ematcher-rule.yml', kind="playbook")
        matches = ematcher.matchlines(lintable)
        assert len(matches) == 3

    def test_rule_postmatching(self) -> None:
        rule = UnsetVariableMatcherRule.UnsetVariableMatcherRule()
        lintable = Lintable('examples/playbooks/bracketsmatchtest.yml', kind="playbook")
        matches = rule.matchlines(lintable)
        assert len(matches) == 2
