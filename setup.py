import os
import sys
from setuptools import setup, find_packages

sys.path.insert(0, os.path.abspath('lib'))

execfile('lib/ansiblelint/version.py')

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
    scripts=['bin/ansible-lint'],
    license='MIT',
    include_package_date=True,
)
