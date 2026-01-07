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
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.testing import run_ansible_lint

if TYPE_CHECKING:
    from ansiblelint.app import App
    from ansiblelint.config import Options


@pytest.fixture(name="test_rules_collection")
def fixture_test_rules_collection(app: App) -> RulesCollection:
    """Create a shared rules collection test instance."""
    return RulesCollection(app=app, rulesdirs=[Path("./test/rules/fixtures").resolve()])


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
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
) -> None:
    """Test that default rules match pre-meditated violations."""
    matches = test_rules_collection.run(ematchtestfile)
    assert len(matches) == 4  # 3 occurrences of BANNED using TEST0001 + 1 for raw-task
    assert matches[0].lineno == 3


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
        ematchtestfile,
        skip_list=["TEST0001", "raw-task"],
    )
    assert len(matches) == 0
    matches = test_rules_collection.run(
        ematchtestfile,
        skip_list=["TEST0002", "raw-task"],
    )
    assert len(matches) == 3
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=["TEST0001"])
    assert len(matches) == 2
    matches = test_rules_collection.run(bracketsmatchtestfile, skip_list=["TEST0002"])
    assert len(matches) == 0


def test_skip_non_existent_id(
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
) -> None:
    """Check that skipping invalid IDs changes nothing."""
    matches = test_rules_collection.run(ematchtestfile, skip_list=["DOESNOTEXIST"])
    assert len(matches) == 4


def test_no_duplicate_rule_ids(app: App) -> None:
    """Check that rules of the collection don't have duplicate IDs."""
    real_rules = RulesCollection(
        app=app, rulesdirs=[Path("./src/ansiblelint/rules").resolve()]
    )
    rule_ids = [rule.id for rule in real_rules]
    assert not any(y > 1 for y in collections.Counter(rule_ids).values())


def test_rule_listing(app: App) -> None:
    """Test that rich list format output is rendered as a table.

    This check also offers the contract of having rule id, short and long
    descriptions in the console output.
    """
    rules_path = Path("./test/rules/fixtures").resolve()
    result = run_ansible_lint("-r", str(rules_path), "-L")
    assert result.returncode == 0

    for rule in RulesCollection(app=app, rulesdirs=[rules_path]):
        assert rule.id in result.stdout
        assert rule.shortdesc in result.stdout


def test_rules_id_format(config_options: Options, app: App) -> None:
    """Assure all our rules have consistent format."""
    rule_id_re = re.compile(r"^[a-z-]{4,30}$")
    rules = RulesCollection(
        app=app,
        rulesdirs=[Path("./src/ansiblelint/rules").resolve()],
        options=config_options,
        conditional=False,
    )
    keys: set[str] = set()
    for rule in rules:
        assert rule_id_re.match(
            rule.id,
        ), f"Rule id {rule.id} did not match our required format."
        keys.add(rule.id)
        assert rule.help or rule.description or rule.__doc__, (
            f"Rule {rule.id} must have at least one of:  .help, .description, .__doc__"
        )
    assert "yaml" in keys, "yaml rule is missing"
    assert len(rules) == 51  # update this number when adding new rules!
    assert len(keys) == len(rules), "Duplicate rule ids?"


def test_tag_inclusion(
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
) -> None:
    """Test that bracketed sub-tags are treated surgically for inclusion."""
    all_matches = test_rules_collection.run(ematchtestfile)

    if not all_matches:
        pytest.fail("No matches found in ematchtestfile!")

    target_tag = all_matches[0].tag
    matches = test_rules_collection.run(ematchtestfile, tags={target_tag})

    assert len(matches) > 0
    for m in matches:
        assert m.tag == target_tag


def test_tag_exclusion(
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
) -> None:
    """Test that bracketed sub-tags are treated surgically for exclusion."""
    target_tag = "TEST0001[BANNED]"

    matches = test_rules_collection.run(ematchtestfile, skip_list=[target_tag])

    tag_results = [m.tag for m in matches]
    assert target_tag not in tag_results


def test_category_tag_override(
    test_rules_collection: RulesCollection,
    ematchtestfile: Lintable,
) -> None:
    """Test that specific sub-tag requests override broad category inclusion."""
    matches = test_rules_collection.run(
        ematchtestfile, tags={"test1", "TEST0001[BANNED]"}
    )

    for m in matches:
        if m.rule.id == "TEST0001":
            assert m.tag == "TEST0001[BANNED]"
