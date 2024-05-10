"""Rule definition for usage of fully qualified collection names for builtins."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from ruamel.yaml.comments import CommentedSeq

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.utils import load_plugin

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


_logger = logging.getLogger(__name__)

builtins = [
    "add_host",
    "apt",
    "apt_key",
    "apt_repository",
    "assemble",
    "assert",
    "async_status",
    "blockinfile",
    "command",
    "copy",
    "cron",
    "debconf",
    "debug",
    "dnf",
    "dpkg_selections",
    "expect",
    "fail",
    "fetch",
    "file",
    "find",
    "gather_facts",
    "get_url",
    "getent",
    "git",
    "group",
    "group_by",
    "hostname",
    "import_playbook",
    "import_role",
    "import_tasks",
    "include",
    "include_role",
    "include_tasks",
    "include_vars",
    "iptables",
    "known_hosts",
    "lineinfile",
    "meta",
    "package",
    "package_facts",
    "pause",
    "ping",
    "pip",
    "raw",
    "reboot",
    "replace",
    "rpm_key",
    "script",
    "service",
    "service_facts",
    "set_fact",
    "set_stats",
    "setup",
    "shell",
    "slurp",
    "stat",
    "subversion",
    "systemd",
    "sysvinit",
    "tempfile",
    "template",
    "unarchive",
    "uri",
    "user",
    "wait_for",
    "wait_for_connection",
    "yum",
    "yum_repository",
]


class FQCNBuiltinsRule(AnsibleLintRule, TransformMixin):
    """Use FQCN for builtin actions."""

    id = "fqcn"
    severity = "MEDIUM"
    description = (
        "Check whether actions are using using full qualified collection names."
    )
    tags = ["formatting"]
    version_added = "v6.8.0"
    module_aliases: dict[str, str] = {"block/always/rescue": "block/always/rescue"}
    _ids = {
        "fqcn[action-core]": "Use FQCN for builtin module actions",
        "fqcn[action]": "Use FQCN for module actions",
        "fqcn[canonical]": "You should use canonical module name",
    }

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        result: list[MatchError] = []
        if file and file.failed():
            return result
        module = task["action"]["__ansible_module_original__"]
        if not isinstance(module, str):
            msg = "Invalid data for module."
            raise TypeError(msg)

        if module not in self.module_aliases:
            loaded_module = load_plugin(module)
            target = loaded_module.resolved_fqcn
            self.module_aliases[module] = target
            if target is None:
                _logger.warning("Unable to resolve FQCN for module %s", module)
                self.module_aliases[module] = module
                return []
            if target not in self.module_aliases:
                self.module_aliases[target] = target

        if module != self.module_aliases[module]:
            module_alias = self.module_aliases[module]
            if module_alias.startswith("ansible.builtin"):
                legacy_module = module_alias.replace(
                    "ansible.builtin.",
                    "ansible.legacy.",
                    1,
                )
                if module != legacy_module:
                    if module == "ansible.builtin.include":
                        message = f"Avoid deprecated module ({module})"
                        details = "Use `ansible.builtin.include_task` or `ansible.builtin.import_tasks` instead."
                    else:
                        message = f"Use FQCN for builtin module actions ({module})."
                        details = f"Use `{module_alias}` or `{legacy_module}` instead."
                    result.append(
                        self.create_matcherror(
                            message=message,
                            details=details,
                            filename=file,
                            lineno=task["__line__"],
                            tag="fqcn[action-core]",
                        ),
                    )
            elif module.count(".") < 2:
                result.append(
                    self.create_matcherror(
                        message=f"Use FQCN for module actions, such `{self.module_aliases[module]}`.",
                        details=f"Action `{module}` is not FQCN.",
                        filename=file,
                        lineno=task["__line__"],
                        tag="fqcn[action]",
                    ),
                )
            # TODO(ssbarnea): Remove the c.g. and c.n. exceptions from here once # noqa: FIX002
            # community team is flattening these.
            # https://github.com/ansible-community/community-topics/issues/147
            elif not module.startswith("community.general.") or module.startswith(
                "community.network.",
            ):
                result.append(
                    self.create_matcherror(
                        message=f"You should use canonical module name `{self.module_aliases[module]}` instead of `{module}`.",
                        filename=file,
                        lineno=task["__line__"],
                        tag="fqcn[canonical]",
                    ),
                )
        return result

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches found for a specific YAML text."""
        result = []
        if file.kind == "plugin":
            i = file.path.resolve().parts.index("plugins")
            plugin_type = file.path.resolve().parts[i : i + 2]
            short_path = file.path.resolve().parts[i + 2 :]
            if len(short_path) > 1:
                result.append(
                    self.create_matcherror(
                        message=f"Deep plugins directory is discouraged. Move '{file.path}' directly under '{'/'.join(plugin_type)}' folder.",
                        tag="fqcn[deep]",
                        filename=file,
                    ),
                )
        elif file.kind == "playbook":
            for play in file.data:
                if play is None:
                    continue

                result.extend(self.matchplay(file, play))
        return result

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        if file.kind != "playbook":
            return []
        if "collections" in data:
            return [
                self.create_matcherror(
                    message="Avoid `collections` keyword by using FQCN for all plugins, modules, roles and playbooks.",
                    lineno=data[LINE_NUMBER_KEY],
                    tag="fqcn[keyword]",
                    filename=file,
                ),
            ]
        return []

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if match.tag in self.ids():
            target_task = self.seek(match.yaml_path, data)
            # Unfortunately, a lot of data about Ansible content gets lost here, you only get a simple dict.
            # For now, just parse the error messages for the data about action names etc. and fix this later.
            if match.tag == "fqcn[action-core]":
                # split at the first bracket, cut off the last bracket and dot
                current_action = match.message.split("(")[1][:-2]
                # This will always replace builtin modules with "ansible.builtin" versions, not "ansible.legacy".
                # The latter is technically more correct in what ansible has executed so far, the former is most likely better understood and more robust.
                new_action = match.details.split("`")[1]
            elif match.tag == "fqcn[action]":
                current_action = match.details.split("`")[1]
                new_action = match.message.split("`")[1]
            elif match.tag == "fqcn[canonical]":
                current_action = match.message.split("`")[3]
                new_action = match.message.split("`")[1]
            for _ in range(len(target_task)):
                if isinstance(target_task, CommentedSeq):
                    continue
                k, v = target_task.popitem(False)
                target_task[new_action if k == current_action else k] = v
            match.fixed = True


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_fqcn_builtin_fail() -> None:
        """Test rule matches."""
        collection = RulesCollection()
        collection.register(FQCNBuiltinsRule())
        success = "examples/playbooks/rule-fqcn-fail.yml"
        results = Runner(success, rules=collection).run()
        assert len(results) == 3
        assert results[0].tag == "fqcn[keyword]"
        assert "Avoid `collections` keyword" in results[0].message
        assert results[1].tag == "fqcn[action-core]"
        assert "Use FQCN for builtin module actions" in results[1].message
        assert results[2].tag == "fqcn[action]"
        assert "Use FQCN for module actions, such" in results[2].message

    def test_fqcn_builtin_pass() -> None:
        """Test rule does not match."""
        collection = RulesCollection()
        collection.register(FQCNBuiltinsRule())
        success = "examples/playbooks/rule-fqcn-pass.yml"
        results = Runner(success, rules=collection).run()
        assert len(results) == 0, results

    def test_fqcn_deep_fail() -> None:
        """Test rule matches."""
        collection = RulesCollection()
        collection.register(FQCNBuiltinsRule())
        failure = "examples/.collection/plugins/modules/deep/beta.py"
        results = Runner(failure, rules=collection).run()
        assert len(results) == 1
        assert results[0].tag == "fqcn[deep]"
        assert "Deep plugins directory is discouraged" in results[0].message

    def test_fqcn_deep_pass() -> None:
        """Test rule does not match."""
        collection = RulesCollection()
        collection.register(FQCNBuiltinsRule())
        success = "examples/.collection/plugins/modules/alpha.py"
        results = Runner(success, rules=collection).run()
        assert len(results) == 0
