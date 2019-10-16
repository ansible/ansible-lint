#! /usr/bin/env python
import setuptools


def cut_local_version_on_upload(version):
    """Generate a PEP440 local version if uploading to PyPI."""
    import os
    import setuptools_scm.version  # only present during setup time
    IS_PYPI_UPLOAD = os.getenv('PYPI_UPLOAD') == 'true'  # set in tox.ini
    return (
        '' if IS_PYPI_UPLOAD
        else setuptools_scm.version.get_local_node_and_date(version)
    )


setup_params = {}
setup_params['use_scm_version'] = {
    'local_scheme': cut_local_version_on_upload,
}


__name__ == '__main__' and setuptools.setup(**setup_params)
