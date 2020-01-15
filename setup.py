#! /usr/bin/env python
"""ansible-lint distribution package setuptools installer."""

import setuptools


if __name__ == "__main__":
    setuptools.setup(
        use_scm_version=True, setup_requires=["setuptools_scm"],
    )
