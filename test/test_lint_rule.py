"""Tests for lintable."""
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

from test.rules.fixtures import ematcher, raw_task

import pytest

from ansiblelint.file_utils import Lintable


@pytest.fixture(name="lintable")
def fixture_lintable() -> Lintable:
    """Return a playbook Lintable for use in this file's tests."""
    return Lintable("examples/playbooks/ematcher-rule.yml", kind="playbook")


def test_rule_matching(lintable: Lintable) -> None:
    """Test rule.matchlines() on a playbook."""
    rule = ematcher.EMatcherRule()
    matches = rule.matchlines(lintable)
    assert len(matches) == 3


def test_raw_rule_matching(lintable: Lintable) -> None:
    """Test rule.matchlines() on a playbook."""
    rule = raw_task.RawTaskRule()
    matches = rule.matchtasks(lintable)
    assert len(matches) == 1
