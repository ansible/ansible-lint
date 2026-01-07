"""Test for output formatter."""

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
import pathlib

import pytest

from ansiblelint.app import App
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import Formatter
from ansiblelint.rules import AnsibleLintRule, RulesCollection

# pylint: disable=redefined-outer-name

# These details would generate a rich rendering error if not escaped:
DETAILS = "Some [/tmp/foo] details."


@pytest.fixture
def formatter_rule() -> AnsibleLintRule:
    """Create a test rule for formatter tests."""
    rule = AnsibleLintRule()
    rule.id = "TCF0001"
    return rule


@pytest.fixture(scope="session")
def formatter_collection(
    formatter_rule: AnsibleLintRule,
    app: App,
) -> RulesCollection:
    """Create a rules collection with the test rule."""
    collection = RulesCollection(app=app)
    collection.register(formatter_rule)
    return collection


@pytest.fixture
def formatter() -> Formatter:
    """Create a Formatter instance."""
    return Formatter(pathlib.Path.cwd(), display_relative_path=True)


def test_format_coloured_string(
    formatter: Formatter,
    formatter_rule: AnsibleLintRule,
) -> None:
    """Test colored formatting."""
    match = MatchError(
        message="message",
        lineno=1,
        details=DETAILS,
        lintable=Lintable("filename.yml", content=""),
        rule=formatter_rule,
    )
    formatter.apply(match)


def test_unicode_format_string(
    formatter: Formatter,
    formatter_rule: AnsibleLintRule,
) -> None:
    """Test formatting unicode."""
    match = MatchError(
        message="\U0001f427",
        lineno=1,
        details=DETAILS,
        lintable=Lintable("filename.yml", content=""),
        rule=formatter_rule,
    )
    formatter.apply(match)


def test_dict_format_line(
    formatter: Formatter,
    formatter_rule: AnsibleLintRule,
) -> None:
    """Test formatting dictionary details."""
    match = MatchError(
        message="xyz",
        lineno=1,
        details={"hello": "world"},  # type: ignore[arg-type]
        lintable=Lintable("filename.yml", content=""),
        rule=formatter_rule,
    )
    formatter.apply(match)
