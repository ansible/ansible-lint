"""Tests for rule collection class."""
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

import collections
import os
import re

import pytest

from ansiblelint.config import options
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.testing import run_ansible_lint


@pytest.fixture(name="test_rules_collection")
def fixture_test_rules_collection() -> RulesCollection:
    """Create a shared rules collection test instance."""
    return RulesCollection([os.path.abspath("./test/rules/fixtures")])


@pytest.fixture(name="ematchtestfile")
def fixture_ematchtestfile() -> Lintable:
    """Produce a test lintable with an id violation."""
    return Lintable("examples/playbooks/ematcher-rule.yml", kind="playbook")


@pytest.fixture(name="bracketsmatchtestfile")
def fixture_bracketsmatchtestfile() -> Lintable:
    """Produce a test lintable with matching brackets."""
    return Lintable("examples/playbooks/bracketsmatchtest.yml", kind="playbook")


def test_load_collection_from_directory(test_rules_collection: RulesCollection) -> None:
    """Test that custom rules extend the default ones."""
    # two detected rules plus the internal ones
    assert len(test_rules_collection) == 7


def test_run_collection(
    test_rules_collection: RulesCollection, ematchtestfile: Lintable
) -> None:
    """Test that default rules match pre-meditated violations."""
    matches = test_rules_collection.run(ematchtestfile)
    assert len(matches) == 4  # 3 occurrences of BANNED using TEST0001 + 1 for raw-task
    assert matches[0].linenumber == 3


def test_tags(
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
    bracketsmatchtestfile: Lintable,
) -> None:
    """Test that tags are treated as skip markers."""
    matches = test_rules_collection.run(ematchtestfile, tags={"test1"})
    assert len(matches) == 3
    matches = test_rules_collection.run(ematchtestfile, tags={"test2"})
    assert len(matches) == 0
    matches = test_rules_collection.run(bracketsmatchtestfile, tags={"test1"})
    assert len(matches) == 0
    matches = test_rules_collection.run(bracketsmatchtestfile, tags={"test2"})
    assert len(matches) == 2


def test_skip_tags(
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
    bracketsmatchtestfile: Lintable,
) -> None:
    """Test that tags can be skipped."""
    matches = test_rules_collection.run(ematchtestfile, skip_list=["test1", "test3"])
    assert len(matches) == 0
    matches = test_rules_collection.run(ematchtestfile, skip_list=["test2", "test3"])
    assert len(matches) == 3
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=["test1"])
    assert len(matches) == 2
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=["test2"])
    assert len(matches) == 0


def test_skip_id(
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
    bracketsmatchtestfile: Lintable,
) -> None:
    """Check that skipping valid IDs excludes their violations."""
    matches = test_rules_collection.run(
        ematchtestfile, skip_list=["TEST0001", "raw-task"]
    )
    assert len(matches) == 0
    matches = test_rules_collection.run(
        ematchtestfile, skip_list=["TEST0002", "raw-task"]
    )
    assert len(matches) == 3
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=["TEST0001"])
    assert len(matches) == 2
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=["TEST0002"])
    assert len(matches) == 0


def test_skip_non_existent_id(
    test_rules_collection: RulesCollection, ematchtestfile: Lintable
) -> None:
    """Check that skipping invalid IDs changes nothing."""
    matches = test_rules_collection.run(ematchtestfile, skip_list=["DOESNOTEXIST"])
    assert len(matches) == 4


def test_no_duplicate_rule_ids() -> None:
    """Check that rules of the collection don't have duplicate IDs."""
    real_rules = RulesCollection([os.path.abspath("./src/ansiblelint/rules")])
    rule_ids = [rule.id for rule in real_rules]
    assert not any(y > 1 for y in collections.Counter(rule_ids).values())


def test_rich_rule_listing() -> None:
    """Test that rich list format output is rendered as a table.

    This check also offers the contract of having rule id, short and long
    descriptions in the console output.
    """
    rules_path = os.path.abspath("./test/rules/fixtures")
    result = run_ansible_lint("-r", rules_path, "-f", "rich", "-L")
    assert result.returncode == 0

    for rule in RulesCollection([rules_path]):
        assert rule.id in result.stdout
        assert rule.shortdesc in result.stdout
        # description could wrap inside table, so we do not check full length
        assert rule.description[:30] in result.stdout


def test_rules_id_format() -> None:
    """Assure all our rules have consistent format."""
    rule_id_re = re.compile("^[a-z-]{4,30}$")
    # options.enable_list = ["no-same-owner", "no-log-password", "no-same-owner"]
    rules = RulesCollection(
        [os.path.abspath("./src/ansiblelint/rules")], options=options, conditional=False
    )
    keys: set[str] = set()
    for rule in rules:
        assert rule_id_re.match(
            rule.id
        ), f"Rule id {rule.id} did not match our required format."
        keys.add(rule.id)
        assert (
            rule.help != "" or rule.description or rule.__doc__
        ), f"Rule {rule.id} must have at least one of:  .help, .description, .__doc__"
    assert "yaml" in keys, "yaml rule is missing"
    assert len(rules) == 48  # update this number when adding new rules!
    assert len(keys) == len(rules), "Duplicate rule ids?"
