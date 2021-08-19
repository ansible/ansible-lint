"""Utilities for configuring ansible runtime environment."""
import json
import logging
import os
import pathlib
import re
import subprocess
import sys
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import packaging
import tenacity
from packaging import version

from ansiblelint.config import (
    ansible_collections_path,
    collection_list,
    options,
    parse_ansible_version,
)
from ansiblelint.constants import (
    ANSIBLE_DEFAULT_ROLES_PATH,
    ANSIBLE_MIN_VERSION,
    ANSIBLE_MISSING_RC,
    ANSIBLE_MOCKED_MODULE,
    INVALID_CONFIG_RC,
    INVALID_PREREQUISITES_RC,
)
from ansiblelint.loaders import yaml_from_file

_logger = logging.getLogger(__name__)


def check_ansible_presence(exit_on_error: bool = False) -> Tuple[str, str]:
    """Assures we stop execution if Ansible is missing or outdated.

    Returne found version and an optional exception if something wrong
    was detected.
    """

    @lru_cache()
    def _get_ver_err() -> Tuple[str, str]:

        err = ""
        failed = False
        ver = ""
        result = subprocess.run(
            args=["ansible", "--version"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        if result.returncode != 0:
            return (
                ver,
                "FATAL: Unable to retrieve ansible cli version: %s" % result.stdout,
            )

        ver, error = parse_ansible_version(result.stdout)
        if error is not None:
            return "", error
        try:
            # pylint: disable=import-outside-toplevel
            from ansible.release import __version__ as ansible_module_version

            if version.parse(ansible_module_version) < version.parse(
                ANSIBLE_MIN_VERSION
            ):
                failed = True
        except (ImportError, ModuleNotFoundError) as e:
            failed = True
            ansible_module_version = "none"
            err += f"{e}\n"
        if failed:
            err += (
                "FATAL: ansible-lint requires a version of Ansible package"
                " >= %s, but %s was found. "
                "Please install a compatible version using the same python interpreter. See "
                "https://docs.ansible.com/ansible/latest/installation_guide"
                "/intro_installation.html#installing-ansible-with-pip"
                % (ANSIBLE_MIN_VERSION, ansible_module_version)
            )

        elif ver != ansible_module_version:
            err = (
                f"FATAL: Ansible CLI ({ver}) and python module"
                f" ({ansible_module_version}) versions do not match. This "
                "indicates a broken execution environment."
            )
        return ver, err

    ver, err = _get_ver_err()
    if exit_on_error and err:
        _logger.error(err)
        sys.exit(ANSIBLE_MISSING_RC)
    return ver, err


def install_collection(collection: str, destination: Optional[str] = None) -> None:
    """Install an Ansible collection.

    Can accept version constraints like 'foo.bar:>=1.2.3'
    """
    cmd = [
        "ansible-galaxy",
        "collection",
        "install",
        "--force",  # required for ansible 2.9
        "-v",
    ]
    if destination:
        cmd.extend(["-p", destination])
    cmd.append(f"{collection}")

    _logger.info("Running %s", " ".join(cmd))
    run = subprocess.run(
        cmd,
        universal_newlines=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if run.returncode != 0:
        _logger.error("Command returned %s code:\n%s", run.returncode, run.stdout)
        sys.exit(INVALID_PREREQUISITES_RC)


@tenacity.retry(  # Retry up to 3 times as galaxy server can return errors
    reraise=True,
    wait=tenacity.wait_fixed(30),  # type: ignore
    stop=tenacity.stop_after_attempt(3),  # type: ignore
    before_sleep=tenacity.after_log(_logger, logging.WARNING),  # type: ignore
)
def install_requirements(requirement: str) -> None:
    """Install dependencies from a requirements.yml."""
    if not os.path.exists(requirement):
        return

    cmd = [
        "ansible-galaxy",
        "role",
        "install",
        "--force",  # required for ansible 2.9
        "--roles-path",
        f"{options.cache_dir}/roles",
        "-vr",
        f"{requirement}",
    ]

    _logger.info("Running %s", " ".join(cmd))
    run = subprocess.run(
        cmd,
        universal_newlines=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if run.returncode != 0:
        _logger.error(run.stdout)
        raise RuntimeError(run.returncode)

    # Run galaxy collection install works on v2 requirements.yml
    if "collections" in yaml_from_file(requirement):

        cmd = [
            "ansible-galaxy",
            "collection",
            "install",
            "--force",  # required for ansible 2.9
            "-p",
            f"{options.cache_dir}/collections",
            "-vr",
            f"{requirement}",
        ]

        _logger.info("Running %s", " ".join(cmd))
        run = subprocess.run(
            cmd,
            universal_newlines=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if run.returncode != 0:
            _logger.error(run.stdout)
            raise RuntimeError(run.returncode)


def prepare_environment(required_collections: Optional[Dict[str, str]] = None) -> None:
    """Make dependencies available if needed."""
    if not options.configured:
        # Allow method to be used without calling the command line, so we can
        # reuse it in other tools, like molecule.
        # pylint: disable=import-outside-toplevel,cyclic-import
        from ansiblelint.__main__ import initialize_options

        initialize_options()

    if not options.offline:
        install_requirements("requirements.yml")
        for req in pathlib.Path(".").glob("molecule/*/requirements.yml"):
            install_requirements(str(req))

    if required_collections:
        for name, min_version in required_collections.items():
            install_collection(
                f"{name}:>={min_version}",
                destination=f"{options.cache_dir}/collections"
                if options.cache_dir
                else None,
            )

    _install_galaxy_role()
    _perform_mockings()
    _prepare_ansible_paths()


def _get_galaxy_role_ns(galaxy_infos: Dict[str, Any]) -> str:
    """Compute role namespace from meta/main.yml, including trailing dot."""
    role_namespace = galaxy_infos.get('namespace', "")
    if len(role_namespace) == 0:
        role_namespace = galaxy_infos.get('author', "")
    # if there's a space in the name space, it's likely author name
    # and not the galaxy login, so act as if there was no namespace
    if re.match(r"^\w+ \w+", role_namespace):
        role_namespace = ""
    else:
        role_namespace = f"{role_namespace}."
    if not isinstance(role_namespace, str):
        raise RuntimeError("Role namespace must be string, not %s" % role_namespace)
    return role_namespace


def _get_galaxy_role_name(galaxy_infos: Dict[str, Any]) -> str:
    """Compute role name from meta/main.yml."""
    return galaxy_infos.get('role_name', "")


def _get_role_fqrn(galaxy_infos: Dict[str, Any]) -> str:
    """Compute role fqrn."""
    role_namespace = _get_galaxy_role_ns(galaxy_infos)
    role_name = _get_galaxy_role_name(galaxy_infos)
    if len(role_name) == 0:
        role_name = pathlib.Path(".").absolute().name
        role_name = re.sub(r'(ansible-|ansible-role-)', '', role_name)

    return f"{role_namespace}{role_name}"


def _install_galaxy_role() -> None:
    """Detect standalone galaxy role and installs it."""
    if not os.path.exists("meta/main.yml"):
        return
    yaml = yaml_from_file("meta/main.yml")
    if 'galaxy_info' not in yaml:
        return

    fqrn = _get_role_fqrn(yaml['galaxy_info'])

    if 'role-name' not in options.skip_list:
        if not re.match(r"[a-z0-9][a-z0-9_]+\.[a-z][a-z0-9_]+$", fqrn):
            msg = (
                """\
Computed fully qualified role name of %s does not follow current galaxy requirements.
Please edit meta/main.yml and assure we can correctly determine full role name:

galaxy_info:
role_name: my_name  # if absent directory name hosting role is used instead
namespace: my_galaxy_namespace  # if absent, author is used instead

Namespace: https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespace-limitations
Role: https://galaxy.ansible.com/docs/contributing/creating_role.html#role-names

As an alternative, you can add 'role-name' to either skip_list or warn_list.
"""
                % fqrn
            )
            if 'role-name' in options.warn_list:
                _logger.warning(msg)
            else:
                _logger.error(msg)
                sys.exit(INVALID_PREREQUISITES_RC)
    else:
        # when 'role-name' is in skip_list, we stick to plain role names
        if 'role_name' in yaml['galaxy_info']:
            role_namespace = _get_galaxy_role_ns(yaml['galaxy_info'])
            role_name = _get_galaxy_role_name(yaml['galaxy_info'])
            fqrn = f"{role_namespace}{role_name}"
        else:
            fqrn = pathlib.Path(".").absolute().name
    p = pathlib.Path(f"{options.cache_dir}/roles")
    p.mkdir(parents=True, exist_ok=True)
    link_path = p / fqrn
    # despite documentation stating that is_file() reports true for symlinks,
    # it appears that is_dir() reports true instead, so we rely on exits().
    target = pathlib.Path(options.project_dir).absolute()
    if not link_path.exists() or os.readlink(link_path) != str(target):
        if link_path.exists():
            link_path.unlink()
        link_path.symlink_to(target, target_is_directory=True)
    _logger.info(
        "Using %s symlink to current repository in order to enable Ansible to find the role using its expected full name.",
        link_path,
    )


def _prepare_ansible_paths() -> None:
    """Configure Ansible environment variables."""
    library_paths: List[str] = []
    roles_path: List[str] = []

    for path_list, path in (
        (library_paths, "plugins/modules"),
        (library_paths, f"{options.cache_dir}/modules"),
        (collection_list, f"{options.cache_dir}/collections"),
        (roles_path, "roles"),
        (roles_path, f"{options.cache_dir}/roles"),
    ):
        if path not in path_list and os.path.exists(path):
            path_list.append(path)

    _update_env('ANSIBLE_LIBRARY', library_paths)
    _update_env(ansible_collections_path(), collection_list)
    _update_env('ANSIBLE_ROLES_PATH', roles_path, default=ANSIBLE_DEFAULT_ROLES_PATH)


def _make_module_stub(module_name: str) -> None:
    # a.b.c is treated a collection
    if re.match(r"^(\w+|\w+\.\w+\.[\.\w]+)$", module_name):
        parts = module_name.split(".")
        if len(parts) < 3:
            path = f"{options.cache_dir}/modules"
            module_file = f"{options.cache_dir}/modules/{module_name}.py"
            namespace = None
            collection = None
        else:
            namespace = parts[0]
            collection = parts[1]
            path = f"{ options.cache_dir }/collections/ansible_collections/{ namespace }/{ collection }/plugins/modules/{ '/'.join(parts[2:-1]) }"
            module_file = f"{path}/{parts[-1]}.py"
        os.makedirs(path, exist_ok=True)
        _write_module_stub(
            filename=module_file,
            name=module_file,
            namespace=namespace,
            collection=collection,
        )
    else:
        _logger.error("Config error: %s is not a valid module name.", module_name)
        sys.exit(INVALID_CONFIG_RC)


def _write_module_stub(
    filename: str,
    name: str,
    namespace: Optional[str] = None,
    collection: Optional[str] = None,
) -> None:
    """Write module stub to disk."""
    body = ANSIBLE_MOCKED_MODULE.format(
        name=name, collection=collection, namespace=namespace
    )
    with open(filename, "w") as f:
        f.write(body)


def _update_env(varname: str, value: List[str], default: str = "") -> None:
    """Update colon based environment variable if needed. by appending."""
    if value:
        orig_value = os.environ.get(varname, default=default)
        if orig_value:
            # Prepend original or default variable content to custom content.
            value = [*orig_value.split(':'), *value]
        value_str = ":".join(value)
        if value_str != os.environ.get(varname, ""):
            os.environ[varname] = value_str
            _logger.info("Added %s=%s", varname, value_str)


def _perform_mockings() -> None:
    """Mock modules and roles."""
    for role_name in options.mock_roles:
        if re.match(r"\w+\.\w+\.\w+$", role_name):
            namespace, collection, role_dir = role_name.split(".")
            path = f"{options.cache_dir}/collections/ansible_collections/{ namespace }/{ collection }/roles/{ role_dir }/"
        else:
            path = f"{options.cache_dir}/roles/{role_name}"
        os.makedirs(path, exist_ok=True)

    if options.mock_modules:
        for module_name in options.mock_modules:
            _make_module_stub(module_name)

    # if inside a collection repo, symlink it to simulate its installed state
    if not os.path.exists("galaxy.yml"):
        return
    yaml = yaml_from_file("galaxy.yml")
    if not yaml:
        # ignore empty galaxy.yml file
        return
    namespace = yaml.get('namespace', None)
    collection = yaml.get('name', None)
    if not namespace or not collection:
        return
    p = pathlib.Path(
        f"{options.cache_dir}/collections/ansible_collections/{ namespace }"
    )
    p.mkdir(parents=True, exist_ok=True)
    link_path = p / collection
    target = pathlib.Path(options.project_dir).absolute()
    if not link_path.exists() or os.readlink(link_path) != target:
        if link_path.exists():
            link_path.unlink()
        link_path.symlink_to(target, target_is_directory=True)


def ansible_config_get(key: str, kind: Type[Any] = str) -> Union[str, List[str], None]:
    """Return configuration item from ansible config."""
    env = os.environ.copy()
    # Avoid possible ANSI garbage
    env["ANSIBLE_FORCE_COLOR"] = "0"
    # Avoid our own override as this prevents returning system paths.
    colpathvar = ansible_collections_path()
    if colpathvar in env:
        env.pop(colpathvar)

    config = subprocess.check_output(
        ["ansible-config", "dump"], universal_newlines=True, env=env
    )

    if kind == str:
        result = re.search(rf"^{key}.* = (.*)$", config, re.MULTILINE)
        if result:
            return result.groups()[0]
    elif kind == list:
        result = re.search(rf"^{key}.* = (\[.*\])$", config, re.MULTILINE)
        if result:
            val = eval(result.groups()[0])  # pylint: disable=eval-used
            if not isinstance(val, list):
                raise RuntimeError(f"Unexpected data read for {key}: {val}")
            return val
    else:
        raise RuntimeError("Unknown data type.")
    return None


def require_collection(  # noqa: C901
    name: str, version: Optional[str] = None, install: bool = True
) -> None:
    """Check if a minimal collection version is present or exits.

    In the future this method may attempt to install a missing or outdated
    collection before failing.
    """
    try:
        ns, coll = name.split('.', 1)
    except ValueError:
        sys.exit("Invalid collection name supplied: %s" % name)

    paths = ansible_config_get('COLLECTIONS_PATHS', list)
    if not paths or not isinstance(paths, list):
        sys.exit(f"Unable to determine ansible collection paths. ({paths})")

    if options.cache_dir:
        # if we have a cache dir, we want to be use that would be preferred
        # destination when installing a missing collection
        paths.insert(0, f"{options.cache_dir}/collections")

    for path in paths:
        collpath = os.path.join(path, 'ansible_collections', ns, coll)
        if os.path.exists(collpath):
            mpath = os.path.join(collpath, 'MANIFEST.json')
            if not os.path.exists(mpath):
                _logger.fatal(
                    "Found collection at '%s' but missing MANIFEST.json, cannot get info.",
                    collpath,
                )
                sys.exit(INVALID_PREREQUISITES_RC)

            with open(mpath, 'r') as f:
                manifest = json.loads(f.read())
                found_version = packaging.version.parse(
                    manifest['collection_info']['version']
                )
                if version and found_version < packaging.version.parse(version):
                    if install:
                        install_collection(f"{name}:>={version}")
                        require_collection(name, version, install=False)
                    else:
                        _logger.fatal(
                            "Found %s collection %s but %s or newer is required.",
                            name,
                            found_version,
                            version,
                        )
                        sys.exit(INVALID_PREREQUISITES_RC)
            break
    else:
        if install:
            install_collection(f"{name}:>={version}")
            require_collection(name, version, install=False)
        else:
            _logger.fatal("Collection '%s' not found in '%s'", name, paths)
            sys.exit(INVALID_PREREQUISITES_RC)
