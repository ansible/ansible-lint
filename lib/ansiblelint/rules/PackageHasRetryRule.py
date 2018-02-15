# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
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


class PackageHasRetryRule(AnsibleLintRule):
    id = 'ANSIBLE0019'
    shortdesc = 'Remote package tasks must have a retry'
    description = ('Package operations are unreliable as they require'
                   'network communication and the availability of remote'
                   'servers. To mitigate the potential problems, retries '
                   'should be used.')
    tags = ['reliability']

    # module list generated with:
    # find lib/ansible/modules/packaging/ -type f \
    #   |awk -F '/' \
    #   '/__|dpkg|_repo|_facts|_sub|_chan/{next} {split($NF, words, "."); print "\""words[1]"\","}'
    package_modules = [
        "bundler",
        "easy_install",
        "composer",
        "maven_artifact",
        "npm",
        "bower",
        "pear",
        "cpanm",
        "pip",
        "gem",
        "package",
        "xbps",
        "pkgutil",
        "pacman",
        "pkgng",
        "zypper",
        "swdepot",
        "layman",
        "portage",
        "apk",
        "homebrew",
        "openbsd_pkg",
        "urpmi",
        "apt_key",
        "swupd",
        "homebrew_tap",
        "yum",
        "dnf",
        "pkgin",
        "svr4pkg",
        "homebrew_cask",
        "sorcery",
        "slackpkg",
        "rpm_key",
        "apt",
        "portinstall",
        "pkg5",
        "opkg",
        "pkg5_publisher",
        "rhn_register",
        "apt_rpm",
        "macports"
    ]

    def matchtask(self, file, task):
        return (task['action']['__ansible_module__'] in self.package_modules
                and 'until' not in task)
