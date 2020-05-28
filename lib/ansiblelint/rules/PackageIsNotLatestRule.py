# Copyright (c) 2016 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from ansiblelint.rules import AnsibleLintRule


class PackageIsNotLatestRule(AnsibleLintRule):
    id = '403'
    shortdesc = 'Package installs should not use latest'
    description = (
        'Package installs should use ``state=present`` '
        'with or without a version'
    )
    severity = 'VERY_LOW'
    tags = ['module', 'repeatability', 'ANSIBLE0010']
    version_added = 'historic'

    _package_managers = [
        'apk',
        'apt',
        'bower',
        'bundler',
        'dnf',
        'easy_install',
        'gem',
        'homebrew',
        'jenkins_plugin',
        'npm',
        'openbsd_package',
        'openbsd_pkg',
        'package',
        'pacman',
        'pear',
        'pip',
        'pkg5',
        'pkgutil',
        'portage',
        'slackpkg',
        'sorcery',
        'swdepot',
        'win_chocolatey',
        'yarn',
        'yum',
        'zypper',
    ]

    def matchtask(self, file, task):
        return (task['action']['__ansible_module__'] in self._package_managers and
                not task['action'].get('version') and
                task['action'].get('state') == 'latest')
