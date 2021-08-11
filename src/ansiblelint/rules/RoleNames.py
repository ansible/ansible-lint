# Copyright (c) 2020 Gael Chamoulaud <gchamoul@redhat.com>
# Copyright (c) 2020 Sorin Sbarnea <ssbarnea@redhat.com>
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

import re
from pathlib import Path
from typing import TYPE_CHECKING, List

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError


ROLE_NAME_REGEX = r'^[a-z][a-z0-9_]+$'


def _remove_prefix(text: str, prefix: str) -> str:
    return re.sub(r'^{0}'.format(re.escape(prefix)), '', text)


class RoleNames(AnsibleLintRule):
    id = 'role-name'
    shortdesc = "Role name {0} does not match ``%s`` pattern" % ROLE_NAME_REGEX
    description = (
        "Role names are now limited to contain only lowercase alphanumeric "
        "characters, plus '_' and start with an alpha character. See "
        "`developing collections <https://docs.ansible.com/ansible/devel/dev_guide/"
        "developing_collections_structure.html#roles-directory>`_"
    )
    severity = 'HIGH'
    done: List[str] = []  # already noticed roles list
    tags = ['deprecations', 'metadata']
    version_added = 'v4.3.0'

    def __init__(self) -> None:
        """Save precompiled regex."""
        self._re = re.compile(ROLE_NAME_REGEX)

    def matchdir(self, lintable: "Lintable") -> List["MatchError"]:
        return self.matchyaml(lintable)

    def matchyaml(self, file: Lintable) -> List["MatchError"]:
        result: List["MatchError"] = []

        if file.kind not in ('meta', 'role'):
            return result
        if file.kind == 'role':
            role_name = self._infer_role_name(
                meta=file.path / "meta" / "main.yml", default=file.path.name
            )
        else:
            role_name = self._infer_role_name(
                meta=file.path, default=file.path.resolve().parents[1].name
            )

        role_name = _remove_prefix(role_name, "ansible-role-")
        if role_name not in self.done:
            self.done.append(role_name)
            if role_name and not self._re.match(role_name):
                result.append(
                    self.create_matcherror(
                        filename=str(file.path),
                        message=self.__class__.shortdesc.format(role_name),
                    )
                )
        return result

    def _infer_role_name(self, meta: Path, default: str) -> str:
        if meta.is_file():
            meta_data = parse_yaml_from_file(str(meta))
            if meta_data:
                try:
                    return str(meta_data['galaxy_info']['role_name'])
                except KeyError:
                    pass
        return default
