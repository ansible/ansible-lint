"""Version tools set."""

import os

from setuptools_scm import get_version


def get_version_from_scm_tag(
        root='.',
        relative_to=None,
        local_scheme='node-and-date',
):
    """Retrieve the version from SCM tag in Git or Hg."""
    try:
        return get_version(
            root=root,
            relative_to=relative_to,
            local_scheme=local_scheme,
        )
    except LookupError:
        return 'unknown'


def cut_local_version_on_upload(version):
    """Return empty local version if uploading to PyPI."""
    is_pypi_upload = os.getenv('PYPI_UPLOAD') == 'true'
    if is_pypi_upload:
        return ''

    import setuptools_scm.version  # only available during setup time
    return setuptools_scm.version.get_local_node_and_date(version)


def get_self_version():
    """Calculate the version of the dist itself."""
    return get_version_from_scm_tag(local_scheme=cut_local_version_on_upload)
