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

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import Formatter
from ansiblelint.rules import AnsibleLintRule

rule = AnsibleLintRule()
rule.id = "TCF0001"
formatter = Formatter(pathlib.Path.cwd(), display_relative_path=True)
# These details would generate a rich rendering error if not escaped:
DETAILS = "Some [/tmp/foo] details."


def test_format_coloured_string() -> None:
    """Test formetting colored."""
    match = MatchError(
        message="message",
        linenumber=1,
        details=DETAILS,
        filename=Lintable("filename.yml"),
        rule=rule,
    )
    formatter.format(match)


def test_unicode_format_string() -> None:
    """Test formatting unicode."""
    match = MatchError(
        message="\U0001f427",
        linenumber=1,
        details=DETAILS,
        filename=Lintable("filename.yml"),
        rule=rule,
    )
    formatter.format(match)


def test_dict_format_line() -> None:
    """Test formatting dictionary details."""
    match = MatchError(
        message="xyz",
        linenumber=1,
        details={"hello": "world"},  # type: ignore
        filename=Lintable("filename.yml"),
        rule=rule,
    )
    formatter.format(match)
