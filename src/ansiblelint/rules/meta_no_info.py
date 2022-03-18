"""Implementation of meta-no-info rule."""
# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from typing import TYPE_CHECKING, Generator, List

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Any, Tuple

    from ansiblelint.constants import odict

META_STR_INFO = ("author", "description")
META_INFO = tuple(
    list(META_STR_INFO)
    + [
        "license",
        "min_ansible_version",
        "platforms",
    ]
)


def _platform_info_errors_itr(
    platforms: "List[odict[str, str]]",
) -> Generator[str, None, None]:
    if not isinstance(platforms, list):
        yield "Platforms should be a list of dictionaries"
        return

    for platform in platforms:
        if not isinstance(platform, dict):
            yield "Platforms should be a list of dictionaries"
        elif "name" not in platform:
            yield "Platform should contain name"


def _galaxy_info_errors_itr(
    galaxy_info: "odict[str, Any]",
    info_list: "Tuple[str, ...]" = META_INFO,
    str_info_list: "Tuple[str, ...]" = META_STR_INFO,
) -> Generator[str, None, None]:
    for info in info_list:
        g_info = galaxy_info.get(info, False)
        if g_info:
            if info in str_info_list and not isinstance(g_info, str):
                yield f"{info} should be a string"
            elif info == "platforms":
                for err in _platform_info_errors_itr(g_info):
                    yield err
        else:
            yield f"Role info should contain {info}"


class MetaMainHasInfoRule(AnsibleLintRule):
    """meta/main.yml should contain relevant info."""

    id = "meta-no-info"
    str_info = META_STR_INFO
    info = META_INFO
    description = f"meta/main.yml should contain: {', '.join(info)}"
    severity = "HIGH"
    tags = ["metadata"]
    version_added = "v4.0.0"

    def matchplay(self, file: Lintable, data: "odict[str, Any]") -> List[MatchError]:
        if file.kind != "meta":
            return []

        # since Ansible 2.10 we can add a meta/requirements.yml but
        # we only want to match on meta/main.yml
        if file.path.name != "main.yml":
            return []

        galaxy_info = data.get("galaxy_info", False)
        if galaxy_info:
            return [
                self.create_matcherror(message=err, filename=file)
                for err in _galaxy_info_errors_itr(galaxy_info)
            ]
        return [self.create_matcherror(message="No 'galaxy_info' found", filename=file)]
