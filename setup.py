#! /usr/bin/env python3
"""Ansible-lint distribution package setuptools installer.

The presence of this file ensures the support
of pip editable mode *with setuptools only*.
"""
import setuptools

# https://github.com/jazzband/pip-tools/issues/1278
setuptools.setup(
    use_scm_version={"local_scheme": "no-local-version"},
    setup_requires=["setuptools_scm[toml]>=3.5.0"],
)
