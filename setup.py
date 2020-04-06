#! /usr/bin/env python3
"""Ansible-lint distribution package setuptools installer.

The presence of this file ensures the support
of pip editable mode *with setuptools only*.
"""
from setuptools import setup

__name__ == '__main__' and setup()  # pylint: disable=expression-not-assigned
