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
# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import pathlib
import unittest

from ansiblelint.errors import MatchError
from ansiblelint.formatters import Formatter
from ansiblelint.rules import AnsibleLintRule


class TestFormatter(unittest.TestCase):
    def setUp(self) -> None:
        self.rule = AnsibleLintRule()
        self.rule.id = "TCF0001"
        self.formatter = Formatter(pathlib.Path.cwd(), display_relative_path=True)

    def test_format_coloured_string(self) -> None:
        match = MatchError(
            message="message",
            linenumber=1,
            details="hello",
            filename="filename.yml",
            rule=self.rule,
        )
        self.formatter.format(match)

    def test_unicode_format_string(self) -> None:
        match = MatchError(
            message="\U0001f427",
            linenumber=1,
            details="hello",
            filename="filename.yml",
            rule=self.rule,
        )
        self.formatter.format(match)

    def test_dict_format_line(self) -> None:
        match = MatchError(
            message="xyz",
            linenumber=1,
            details={"hello": "world"},  # type: ignore
            filename="filename.yml",
            rule=self.rule,
        )
        self.formatter.format(match)
