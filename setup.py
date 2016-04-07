#!/usr/bin/env python2
from __future__ import absolute_import
from setuptools import find_packages
from setuptools import setup
import codecs
import os
import re


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='ansible-lint',
    version=find_version("lib/ansiblelint", "version.py"),
    description=('checks playbooks for practices and behaviour that could potentially be improved'),
    keywords='ansible, lint',
    author='Will Thames',
    author_email='will@thames.id.au',
    url='https://github.com/willthames/ansible-lint',
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    zip_safe=False,
    install_requires=['ansible', 'pyyaml'],
    license='MIT',
    include_package_date=True,
    test_suite="test",
    entry_points={
        "console_scripts": [
            "ansible-lint=ansiblelint:main"
        ]}
)
