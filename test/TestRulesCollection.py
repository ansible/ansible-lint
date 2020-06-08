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

import collections
import os

import pytest

from ansiblelint.rules import RulesCollection


@pytest.fixture
def test_rules_collection():
    return RulesCollection([os.path.abspath('./test/rules')])


@pytest.fixture
def ematchtestfile():
    return dict(path='test/ematchtest.yml', type='playbook')


@pytest.fixture
def bracketsmatchtestfile():
    return dict(path='test/bracketsmatchtest.yml', type='playbook')


def test_load_collection_from_directory(test_rules_collection):
    assert len(test_rules_collection) == 2


def test_run_collection(test_rules_collection, ematchtestfile):
    matches = test_rules_collection.run(ematchtestfile)
    assert len(matches) == 3


def test_tags(test_rules_collection, ematchtestfile, bracketsmatchtestfile):
    matches = test_rules_collection.run(ematchtestfile, tags=['test1'])
    assert len(matches) == 3
    matches = test_rules_collection.run(ematchtestfile, tags=['test2'])
    assert len(matches) == 0
    matches = test_rules_collection.run(bracketsmatchtestfile, tags=['test1'])
    assert len(matches) == 1
    matches = test_rules_collection.run(bracketsmatchtestfile, tags=['test2'])
    assert len(matches) == 2


def test_skip_tags(test_rules_collection, ematchtestfile, bracketsmatchtestfile):
    matches = test_rules_collection.run(ematchtestfile, skip_list=['test1'])
    assert len(matches) == 0
    matches = test_rules_collection.run(ematchtestfile, skip_list=['test2'])
    assert len(matches) == 3
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=['test1'])
    assert len(matches) == 2
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=['test2'])
    assert len(matches) == 1


def test_skip_id(test_rules_collection, ematchtestfile, bracketsmatchtestfile):
    matches = test_rules_collection.run(ematchtestfile, skip_list=['TEST0001'])
    assert len(matches) == 0
    matches = test_rules_collection.run(ematchtestfile, skip_list=['TEST0002'])
    assert len(matches) == 3
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=['TEST0001'])
    assert len(matches) == 2
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=['TEST0002'])
    assert len(matches) == 1


def test_skip_non_existent_id(test_rules_collection, ematchtestfile):
    matches = test_rules_collection.run(ematchtestfile, skip_list=['DOESNOTEXIST'])
    assert len(matches) == 3


def test_no_duplicate_rule_ids(test_rules_collection):
    real_rules = RulesCollection([os.path.abspath('./lib/ansiblelint/rules')])
    rule_ids = [rule.id for rule in real_rules]
    assert not any(y > 1 for y in collections.Counter(rule_ids).values())
