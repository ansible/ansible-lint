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
        '``register: my_result`` and ``until: my_result | success``'
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

    def matchtask(self, file, task):
        module = task["action"]["__ansible_module__"]
        if module in self._package_modules:
            if 'until' not in task:
                # Exclude tasks where state is `absent`.
                if task['action'].get('state') not in self._module_ignore_states:
                    message = '{0} {1}'
                    return message.format(self.shortdesc, module)
                return False
