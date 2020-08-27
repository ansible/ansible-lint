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
"""Main ansible-lint package."""

import builtins
from typing import Any

# NOTE: Importing builtins as _builtins does not allow to redefine the
# NOTE: type required to trick mypy into thinking that we can set the
# NOTE: "pytest" attribute:
_builtins: Any = builtins
del builtins

try:
    import pytest as _pytest  # noqa: PT013
except ImportError:
    from unittest.mock import MagicMock as _MagicMock
    _builtins.pytest = _MagicMock()
else:
    _builtins.pytest = _pytest

# NOTE: flake8 isn't satisfied with the import positions but we have to
# NOTE: do the builtin patching before anything else gets into play.
from .rules import AnsibleLintRule  # noqa: E402
from .version import __version__  # noqa: E402

__all__ = (
    "__version__",
    "AnsibleLintRule"  # deprecated, import it directly from rules
)
