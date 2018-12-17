# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule


class PackageHasRetryRule(AnsibleLintRule):
    id = '405'
    shortdesc = 'Remote package tasks should have a retry'
    description = (
        'Package operations are unreliable as they require '
        'network communication and the availability of remote '
        'servers. To mitigate the potential problems, retries '
        'should be used via '
        '``register: my_result`` and ``until: my_result is succeeded``'
    )
    severity = 'LOW'
    tags = ['module', 'reliability']
    version_added = 'v4.0.0'

    # module list generated with:
    # find lib/ansible/modules/packaging/ -type f -printf '%f\n' \
    #   | sort | awk -F '/' \
    #   '/__|dpkg|_repo|_facts|_sub|_chan/{next} {split($NF, words, ".");
    #   print "\""words[1]"\","}'
    _package_modules = [
        "apk",
        "apt_key",
        "apt",
        "apt_rpm",
        "bower",
        "bundler",
        "composer",
        "cpanm",
        "dnf",
        "easy_install",
        "flatpak",
        "flatpak_remote",
        "gem",
        "homebrew_cask",
        "homebrew",
        "homebrew_tap",
        "layman",
        "macports",
        "maven_artifact",
        "npm",
        "openbsd_pkg",
        "opkg",
        "package",
        "pacman",
        "pear",
        "pip",
        "pkg5_publisher",
        "pkg5",
        "pkgin",
        "pkgng",
        "pkgutil",
        "portage",
        "portinstall",
        "rhn_register",
        "rpm_key",
        "slackpkg",
        "snap",
        "sorcery",
        "svr4pkg",
        "swdepot",
        "swupd",
        "urpmi",
        "xbps",
        "yarn",
        "yum",
        "zypper",
    ]

    _module_ignore_states = [
        "absent",
    ]

    _module_ignore_parameters = [
        "data",
    ]

    _package_name_keys = [
        "name",
        "package",
        "pkg",
        "deb",
        "key",
    ]

    def get_package_name(self, action):
        """Attempt to find package name."""
        for key in self._package_name_keys:
            found_package_name = action.get(key)
            if found_package_name:
                return found_package_name
        return found_package_name

    def matchtask(self, file, task):
        module = task["action"]["__ansible_module__"]

        if module not in self._package_modules:
            return False

        is_task_retryable = 'until' in task
        if is_task_retryable:
            return False

        is_state_whitelisted = task['action'].get('state') in self._module_ignore_states
        if is_state_whitelisted:
            return False

        has_whitelisted_parameter = (
            set(self._module_ignore_parameters).intersection(set(task['action']))
        )
        if has_whitelisted_parameter:
            return False

        found_package_name = self.get_package_name(task['action'])
        if not found_package_name:
            return True

        is_package_file = '.' in found_package_name
        is_package_html = '://' in found_package_name
        is_local_package_file = is_package_file and not is_package_html
        if is_local_package_file:
            return False

        return True
