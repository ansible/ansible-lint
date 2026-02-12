"""Utilities for reading Ansible configuration (ansible.cfg)."""

from __future__ import annotations

import configparser
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ansiblelint.config import Options

_logger = logging.getLogger(__name__)


def find_ansible_cfg(project_dir: str) -> Path | None:
    """Find ansible.cfg file following Ansible's search order.

    Search order (from Ansible documentation):
    1. ANSIBLE_CONFIG environment variable
    2. ansible.cfg in current/project directory
    3. ~/.ansible.cfg in user home
    4. /etc/ansible/ansible.cfg system-wide

    Args:
        project_dir: The project directory to start searching from

    Returns:
        Path to ansible.cfg if found, None otherwise
    """
    # 1. Check ANSIBLE_CONFIG environment variable
    if "ANSIBLE_CONFIG" in os.environ:
        config_path = Path(os.environ["ANSIBLE_CONFIG"])
        if config_path.exists():
            _logger.debug("Found ansible.cfg via ANSIBLE_CONFIG: %s", config_path)
            return config_path

    # 2. Check project directory
    project_cfg = Path(project_dir) / "ansible.cfg"
    if project_cfg.exists():
        _logger.debug("Found ansible.cfg in project directory: %s", project_cfg)
        return project_cfg

    # 3. Check user home directory
    home_cfg = Path.home() / ".ansible.cfg"
    if home_cfg.exists():
        _logger.debug("Found ansible.cfg in user home: %s", home_cfg)
        return home_cfg

    # 4. Check system-wide location
    system_cfg = Path("/etc/ansible/ansible.cfg")
    if system_cfg.exists():
        _logger.debug("Found ansible.cfg in system location: %s", system_cfg)
        return system_cfg

    _logger.debug("No ansible.cfg found in standard locations")
    return None


def read_collections_paths_from_ansible_cfg(project_dir: str) -> list[str] | None:
    """Read collections_paths setting from ansible.cfg.

    Args:
        project_dir: The project directory to start searching from

    Returns:
        List of collection paths if configured in ansible.cfg, None otherwise
    """
    ansible_cfg = find_ansible_cfg(project_dir)
    if not ansible_cfg:
        return None

    try:
        config = configparser.ConfigParser()
        config.read(ansible_cfg)

        # Try to read collections_path or collections_paths (both are valid)
        collections_paths_str = None
        if config.has_section("defaults"):
            # Try both valid key names
            if config.has_option("defaults", "collections_path"):
                collections_paths_str = config.get("defaults", "collections_path")
            elif config.has_option("defaults", "collections_paths"):
                collections_paths_str = config.get("defaults", "collections_paths")

        if not collections_paths_str:
            _logger.debug("No collections_path(s) found in ansible.cfg")
            return None

        # Parse the colon-separated paths
        paths = [p.strip() for p in collections_paths_str.split(":") if p.strip()]

        if not paths:
            return None

        # Resolve relative paths relative to the ansible.cfg location
        resolved_paths = []
        ansible_cfg_dir = ansible_cfg.parent
        for path_str in paths:
            path = Path(path_str)
            if not path.is_absolute():
                # Resolve relative to ansible.cfg directory
                path = (ansible_cfg_dir / path).resolve()
            resolved_paths.append(str(path))

        _logger.info(
            "Read collections_paths from %s: %s",
            ansible_cfg,
            resolved_paths,
        )
        return resolved_paths

    except (configparser.Error, OSError) as e:
        _logger.warning("Failed to read ansible.cfg at %s: %s", ansible_cfg, e)
        return None


def load_ansible_config_into_options(options: Options) -> None:
    """Load Ansible configuration from ansible.cfg into Options.

    This function reads ansible.cfg and populates ansible-specific settings
    into the Options object, specifically collections_paths which needs to
    be honored to match Ansible's behavior.

    Args:
        options: The Options object to populate with Ansible config
    """
    if not options.project_dir:
        return

    collections_paths = read_collections_paths_from_ansible_cfg(options.project_dir)
    if collections_paths:
        options.ansible_collections_paths = collections_paths
        _logger.debug(
            "Set ansible_collections_paths in options: %s",
            collections_paths,
        )
