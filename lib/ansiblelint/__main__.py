from __future__ import absolute_import

import os
import sys

# If we are running from a wheel, add the wheel to sys.path
# This allows the usage python ansiblelint-*.whl/pip install ansiblelint-*.whl
if __package__ == '':
    # __file__ is ansiblelint-*.whl/ansiblelint/__main__.py
    # first dirname call strips of '/__main__.py', second strips off '/ansiblelint'
    # Resulting path is the name of the wheel itself
    # Add that to sys.path so we can import pip
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

import ansiblelint  # noqa

if __name__ == '__main__':
    sys.exit(ansiblelint.main())
