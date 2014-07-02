import os
import sys
from setuptools import setup, find_packages

this_dir = os.path.dirname(__file__)
long_description = "\n" + open(os.path.join(this_dir, 'README.md')).read()

sys.path.insert(0, os.path.abspath('lib'))

setup(
    name='ansiblelint',
    version='0.0.0',
    description=('checks playbooks for practices and behaviour that could potentially be improved'),
    long_description=long_description,
    keywords='ansible, lint',
    author='Will Thames',
    author_email='',
    url='https://github.com/willthames/ansible-lint',
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    zip_safe=False,
    install_requires=['ansible'],
    scripts=['bin/ansible-lint'],
)
