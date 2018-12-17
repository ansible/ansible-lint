#! /usr/bin/env python
"""Ansible-lint distribution package setuptools installer."""

import setuptools


try:
    from setuptools.config import read_configuration, ConfigOptionsHandler
    import setuptools.config
    import setuptools.dist

    # Set default value for 'use_scm_version'
    setattr(setuptools.dist.Distribution, 'use_scm_version', False)

    # Attach bool parser to 'use_scm_version' option
    class ShimConfigOptionsHandler(ConfigOptionsHandler):
        """Extension class for ConfigOptionsHandler."""

        @property
        def parsers(self):
            """Return an option mapping with default data type parsers."""
            _orig_parsers = super(ShimConfigOptionsHandler, self).parsers
            return dict(use_scm_version=self._parse_bool, **_orig_parsers)

    setuptools.config.ConfigOptionsHandler = ShimConfigOptionsHandler
except ImportError:
    """This is a shim for setuptools<30.3."""
    import io
    import json

    try:
        from configparser import ConfigParser, NoSectionError
    except ImportError:
        from ConfigParser import ConfigParser, NoSectionError
        ConfigParser.read_file = ConfigParser.readfp

    def maybe_read_files(d):
        """Read files if the string starts with `file:` marker."""
        d = d.strip()
        if not d.startswith('file:'):
            return d
        descs = []
        for fname in map(str.strip, d[5:].split(',')):
            with io.open(fname, encoding='utf-8') as f:
                descs.append(f.read())
        return ''.join(descs)

    def cfg_val_to_list(v):
        """Turn config val to list and filter out empty lines."""
        return list(filter(bool, map(str.strip, str(v).strip().splitlines())))

    def cfg_val_to_dict(v):
        """Turn config val to dict and filter out empty lines."""
        return dict(
            map(lambda l: list(map(str.strip, l.split('=', 1))),
                filter(bool, map(str.strip, str(v).strip().splitlines())))
        )

    def cfg_val_to_primitive(v):
        """Parse primitive config val to appropriate data type."""
        return json.loads(v.strip().lower())

    def read_configuration(filepath):
        """Read metadata and options from setup.cfg located at filepath."""
        cfg = ConfigParser()
        with io.open(filepath, encoding='utf-8') as f:
            cfg.read_file(f)

        md = dict(cfg.items('metadata'))
        for list_key in 'classifiers', 'keywords':
            try:
                md[list_key] = cfg_val_to_list(md[list_key])
            except KeyError:
                pass
        try:
            md['long_description'] = maybe_read_files(md['long_description'])
        except KeyError:
            pass
        opt = dict(cfg.items('options'))
        for list_key in 'use_scm_version', 'zip_safe':
            try:
                opt[list_key] = cfg_val_to_primitive(opt[list_key])
            except KeyError:
                pass
        for list_key in 'scripts', 'install_requires', 'setup_requires':
            try:
                opt[list_key] = cfg_val_to_list(opt[list_key])
            except KeyError:
                pass
        try:
            opt['package_dir'] = cfg_val_to_dict(opt['package_dir'])
        except KeyError:
            pass
        opt_package_data = dict(cfg.items('options.package_data'))
        try:
            if not opt_package_data.get('', '').strip():
                opt_package_data[''] = opt_package_data['*']
                del opt_package_data['*']
        except KeyError:
            pass
        try:
            opt_extras_require = dict(cfg.items('options.extras_require'))
            opt['extras_require'] = {}
            for k, v in opt_extras_require.items():
                opt['extras_require'][k] = cfg_val_to_list(v)
        except NoSectionError:
            pass
        opt['package_data'] = {}
        for k, v in opt_package_data.items():
            opt['package_data'][k] = cfg_val_to_list(v)
        cur_pkgs = opt.get('packages', '').strip()
        if '\n' in cur_pkgs:
            opt['packages'] = cfg_val_to_list(opt['packages'])
        elif cur_pkgs.startswith('find:'):
            opt_packages_find = dict(cfg.items('options.packages.find'))
            opt['packages'] = setuptools.find_packages(**opt_packages_find)
        return {'metadata': md, 'options': opt}


setup_params = {}
declarative_setup_params = read_configuration('setup.cfg')

# Patch incorrectly decoded package_dir option
# ``egg_info`` demands native strings failing with unicode under Python 2
# Ref https://github.com/pypa/setuptools/issues/1136
declarative_setup_params['options']['package_dir'] = {
    str(k): str(v)
    for k, v in declarative_setup_params['options']['package_dir'].items()
}

setup_params = dict(setup_params, **declarative_setup_params['metadata'])
setup_params = dict(setup_params, **declarative_setup_params['options'])


def cut_local_version_on_upload(version):
    import os
    import setuptools_scm.version  # only present during setup time
    IS_PYPI_UPLOAD = os.getenv('PYPI_UPLOAD') == 'true'
    return (
        '' if IS_PYPI_UPLOAD
        else setuptools_scm.version.get_local_node_and_date(version)
    )


setup_params['use_scm_version'] = {
    'local_scheme': cut_local_version_on_upload,
}


__name__ == '__main__' and setuptools.setup(**setup_params)
