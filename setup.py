#! /usr/bin/env python
"""Ansible-lint distribution package setuptools installer."""


__requires__ = ('setuptools >= 34.4', )


import setuptools
from setuptools.config import read_configuration


def cut_local_version_on_upload(version):
    """Generate a PEP440 local version if uploading to PyPI."""
    import os
    import setuptools_scm.version  # only present during setup time
    IS_PYPI_UPLOAD = os.getenv('PYPI_UPLOAD') == 'true'
    return (
        '' if IS_PYPI_UPLOAD
        else setuptools_scm.version.get_local_node_and_date(version)
    )


# This is needed because even new
# setuptools don't parse
# `setup_requires` from `setup.cfg`:
declarative_setup_params = read_configuration('setup.cfg')
setup_params = {
    'setup_requires': declarative_setup_params['options']['setup_requires'],
    'use_scm_version': {
        'local_scheme': cut_local_version_on_upload,
    }
}


__name__ == '__main__' and setuptools.setup(**setup_params)
