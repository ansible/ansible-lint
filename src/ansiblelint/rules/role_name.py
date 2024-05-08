"""Implementation of role-name rule."""

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
from __future__ import annotations

import re
import sys
from functools import cache
from typing import TYPE_CHECKING

from ansiblelint.constants import ROLE_IMPORT_ACTION_NAMES
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from pathlib import Path

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


ROLE_NAME_REGEX = re.compile(r"^[a-z][a-z0-9_]*$")


def _remove_prefix(text: str, prefix: str) -> str:
    return re.sub(rf"^{re.escape(prefix)}", "", text)


@cache
def _match_role_name_regex(role_name: str) -> bool:
    return ROLE_NAME_REGEX.match(role_name) is not None


class RoleNames(AnsibleLintRule):
    """Role name {0} does not match ``^[a-z][a-z0-9_]*$`` pattern."""

    id = "role-name"
    description = (
        "Role names are now limited to contain only lowercase alphanumeric "
        "characters, plus underline and start with an alpha character."
    )
    link = "https://docs.ansible.com/ansible/devel/dev_guide/developing_collections_structure.html#roles-directory"
    severity = "HIGH"
    tags = ["deprecations", "metadata"]
    version_added = "v6.8.5"
    _ids = {
        "role-name[path]": "Avoid using paths when importing roles.",
    }

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        results = []
        if task["action"]["__ansible_module__"] in ROLE_IMPORT_ACTION_NAMES:
            name = task["action"].get("name", "")
            if "/" in name:
                results.append(
                    self.create_matcherror(
                        f"Avoid using paths when importing roles. ({name})",
                        filename=file,
                        lineno=task["action"].get("__line__", task["__line__"]),
                        tag=f"{self.id}[path]",
                    ),
                )
        return results

    def matchdir(self, lintable: Lintable) -> list[MatchError]:
        return self.matchyaml(lintable)

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        result: list[MatchError] = []

        if file.kind not in ("meta", "role", "playbook"):
            return result

        if file.kind == "meta":
            for role in file.data.get("dependencies", []):
                if isinstance(role, dict):
                    role_name = role["role"]
                elif isinstance(role, str):
                    role_name = role
                else:
                    msg = "Role dependency has unexpected type."
                    raise TypeError(msg)
                if "/" in role_name:
                    result.append(
                        self.create_matcherror(
                            f"Avoid using paths when importing roles. ({role_name})",
                            filename=file,
                            lineno=role_name.ansible_pos[1],
                            tag=f"{self.id}[path]",
                        ),
                    )
            return result

        if file.kind == "playbook":
            for play in file.data:
                if "roles" in play:
                    line = play["__line__"]
                    for role in play["roles"]:
                        if isinstance(role, dict):
                            line = role["__line__"]
                            role_name = role["role"]
                        elif isinstance(role, str):
                            role_name = role
                        if "/" in role_name:
                            result.append(
                                self.create_matcherror(
                                    f"Avoid using paths when importing roles. ({role_name})",
                                    filename=file,
                                    lineno=line,
                                    tag=f"{self.id}[path]",
                                ),
                            )
            return result

        if file.kind == "role":
            role_name = self._infer_role_name(
                meta=file.path / "meta" / "main.yml",
                default=file.path.name,
            )
        else:
            role_name = self._infer_role_name(
                meta=file.path,
                default=file.path.resolve().parents[1].name,
            )

        role_name = _remove_prefix(role_name, "ansible-role-")
        if role_name and not _match_role_name_regex(role_name):
            result.append(
                self.create_matcherror(
                    filename=file,
                    message=self.shortdesc.format(role_name),
                ),
            )
        return result

    @staticmethod
    def _infer_role_name(meta: Path, default: str) -> str:
        if meta.is_file():
            meta_data = parse_yaml_from_file(str(meta))
            if meta_data:
                try:
                    return str(meta_data["galaxy_info"]["role_name"])
                except KeyError:
                    pass
        return default


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failure"),
        (pytest.param("examples/playbooks/rule-role-name-path.yml", 3, id="fail"),),
    )
    def test_role_name_path(
        default_rules_collection: RulesCollection,
        test_file: str,
        failure: int,
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        for result in results:
            assert result.tag == "role-name[path]"
        assert len(results) == failure

    @pytest.mark.parametrize(
        ("test_file", "failure"),
        (pytest.param("examples/roles/role_with_deps_paths", 3, id="fail"),),
    )
    def test_role_deps_path_names(
        default_rules_collection: RulesCollection,
        test_file: str,
        failure: int,
    ) -> None:
        """Test rule matches."""
        results = Runner(
            test_file,
            rules=default_rules_collection,
        ).run()
        expected_errors = (
            ("role-name[path]", 3),
            ("role-name[path]", 9),
            ("role-name[path]", 10),
        )
        assert len(expected_errors) == failure
        for idx, result in enumerate(results):
            assert result.tag == expected_errors[idx][0]
            assert result.lineno == expected_errors[idx][1]
        assert len(results) == failure

    @pytest.mark.parametrize(
        ("test_file", "failure"),
        (pytest.param("examples/roles/test-no-deps-role", 0, id="no_deps"),),
    )
    def test_role_no_deps(
        default_rules_collection: RulesCollection,
        test_file: str,
        failure: int,
    ) -> None:
        """Test role if no dependencies are present in meta/main.yml."""
        results = Runner(
            test_file,
            rules=default_rules_collection,
        ).run()
        assert len(results) == failure
