"""An ansible test module."""

DOCUMENTATION = """
module: mod_1
author:
- test
short_description: This is a test module
description:
- This is a test module
version_added: 1.0.0
options:
  foo:
    description:
    - Dummy option I(foo)
    type: str
  bar:
    description:
    - Dummy option I(bar)
    default: candidate
    type: str
    choices:
    - candidate
    - running
    aliases:
    - bam
notes:
- This is a dummy module
"""

EXAMPLES = """
# fmt: text

This is some text. Nothing to see.
"""

RETURN = """
baz:
    description: test return 1
    returned: success
    type: list
    sample: ['a','b']
"""
