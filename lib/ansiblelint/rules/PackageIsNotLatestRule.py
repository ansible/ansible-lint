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

from ansiblelint import AnsibleLintRule


class PackageIsNotLatestRule(AnsibleLintRule):
    id = 'ANSIBLE0010'
    shortdesc = 'Package installs should not use latest'
    description = 'Package installs should use state=present ' + \
                  'with or without a version'
    tags = ['repeatability']

    _package_managers = ['yum', 'apt', 'dnf', 'homebrew', 'pacman', 'openbsd_package', 'pkg5',
                         'portage', 'pkgutil', 'slackpkg', 'swdepot', 'zypper', 'bundler', 'pip',
                         'pear', 'npm', 'gem', 'easy_install', 'bower', 'package']

    def matchtask(self, file, task):
        return (task['action']['__ansible_module__'] in self._package_managers and
                task['action'].get('state') == 'latest')
