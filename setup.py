import os
from setuptools import find_packages
from setuptools import setup
import sys


sys.path.insert(0, os.path.abspath('lib'))

exec(open('lib/ansiblelint/version.py').read())

setup(
    name='ansible-lint',
    version=__version__,
    description='checks playbooks for practices and behaviour that could potentially be improved',
    keywords='ansible, lint',
    maintainer='Ansible by Red Hat',
    maintainer_email='info@ansible.com',
    url='https://github.com/ansible/ansible-lint',
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    zip_safe=False,
    install_requires=['ansible', 'pyyaml', 'six'],
    entry_points={
        'console_scripts': [
            'ansible-lint = ansiblelint.__main__:main'
        ]
    },
    license='MIT',
    test_suite="test"
)
