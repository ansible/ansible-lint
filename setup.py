#!/usr/bin/env python2
from __future__ import absolute_import
from setuptools import find_packages
from setuptools import setup

from lib.ansiblelint import __version__

setup(
    name='ansible-lint',
    version=__version__,
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
