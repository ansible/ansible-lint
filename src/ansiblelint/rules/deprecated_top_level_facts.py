"""Implementation of the deprecated-top-level-facts rule."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, nodes
from jinja2.exceptions import TemplateSyntaxError

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import parse_yaml_from_file
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task

# Facts gathered by ansible.builtin.setup (all platforms) and
# ansible.windows.setup, without the ``ansible_`` prefix. Facts whose names
# depend on the host, like network interfaces (``ansible_eth0``), are not
# listed, and neither are ``ansible_local`` and connection or magic variables
# such as ``ansible_host`` or ``ansible_user``, which are not facts.
FACT_NAMES = frozenset(
    {
        "all_ipv4_addresses",
        "all_ipv6_addresses",
        "apparmor",
        "architecture",
        "architecture2",
        "bios_date",
        "bios_vendor",
        "bios_version",
        "board_asset_tag",
        "board_name",
        "board_serial",
        "board_vendor",
        "board_version",
        "chassis_asset_tag",
        "chassis_serial",
        "chassis_vendor",
        "chassis_version",
        "cmdline",
        "container",
        "date_time",
        "default_ipv4",
        "default_ipv6",
        "device_links",
        "devices",
        "distribution",
        "distribution_cpe_name",
        "distribution_file_parsed",
        "distribution_file_path",
        "distribution_file_variety",
        "distribution_major_version",
        "distribution_minor_version",
        "distribution_release",
        "distribution_version",
        "dns",
        "domain",
        "effective_group_id",
        "effective_user_id",
        "env",
        "fibre_channel_wwn",
        "fips",
        "firmware_version",
        "form_factor",
        "fqdn",
        "hostname",
        "hostnqn",
        "interfaces",
        "ip_addresses",
        "is_chroot",
        "iscsi_iqn",
        "kernel",
        "kernel_version",
        "lastboot",
        "loadavg",
        "locally_reachable_ips",
        "lpar_info",
        "lsb",
        "lvm",
        "machine",
        "machine_id",
        "memfree_mb",
        "memory_mb",
        "memtotal_mb",
        "model",
        "mounts",
        "netbios_name",
        "nodename",
        "os_family",
        "os_install_date",
        "os_installation_type",
        "os_name",
        "os_product_type",
        "osrevision",
        "osversion",
        "owner_contact",
        "owner_name",
        "pagefilefree_mb",
        "pagefiletotal_mb",
        "pkg_mgr",
        "powershell_version",
        "proc_cmdline",
        "processor",
        "processor_cores",
        "processor_count",
        "processor_nproc",
        "processor_threads_per_core",
        "processor_vcpus",
        "product_name",
        "product_serial",
        "product_uuid",
        "product_version",
        "python",
        "python_version",
        "real_group_id",
        "real_user_id",
        "reboot_pending",
        "selinux",
        "selinux_python_present",
        "service_mgr",
        "ssh_host_key_dsa_public",
        "ssh_host_key_dsa_public_keytype",
        "ssh_host_key_ecdsa_public",
        "ssh_host_key_ecdsa_public_keytype",
        "ssh_host_key_ed25519_public",
        "ssh_host_key_ed25519_public_keytype",
        "ssh_host_key_rsa_public",
        "ssh_host_key_rsa_public_keytype",
        "swap_allocated_mb",
        "swap_reserved_mb",
        "swapfree_mb",
        "swaptotal_mb",
        "system",
        "system_capabilities",
        "system_capabilities_enforced",
        "system_description",
        "system_vendor",
        "systemd",
        "uptime_seconds",
        "user_dir",
        "user_gecos",
        "user_gid",
        "user_id",
        "user_shell",
        "user_sid",
        "user_uid",
        "userspace_architecture",
        "userspace_bits",
        "vgs",
        "virtualization_role",
        "virtualization_tech_guest",
        "virtualization_tech_host",
        "virtualization_type",
        "win_rm_certificate_expires",
        "win_rm_certificate_thumbprint",
        "windows_domain",
        "windows_domain_member",
        "windows_domain_role",
    },
)

# Task keywords whose values are bare Jinja expressions, not templates.
_CONDITIONAL_KEYS = ("when", "changed_when", "failed_when", "until")
_ASSERT_MODULES = ("ansible.builtin.assert", "ansible.legacy.assert", "assert")
_DEBUG_MODULES = ("ansible.builtin.debug", "ansible.legacy.debug", "debug")
_NESTED_TASK_KEYS = ("block", "ansible.builtin.block", "ansible.legacy.block")
_PLAY_TASK_KEYS = ("tasks", "pre_tasks", "post_tasks", "handlers")

_env = Environment(extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"])


def _fact_name(name: Any) -> str | None:
    """Return the fact name if ``name`` is a top-level fact variable."""
    if isinstance(name, str) and name.startswith("ansible_"):
        fact = name[len("ansible_") :]
        if fact in FACT_NAMES:
            return fact
    return None


def _message(fact: str) -> str:
    return (
        f"Use `ansible_facts['{fact}']` instead of the top-level fact `ansible_{fact}`."
    )


def _is_hostvars_entry(node: nodes.Node) -> bool:
    """Return True for ``hostvars[host]`` or ``hostvars.host``."""
    return (
        isinstance(node, nodes.Getitem | nodes.Getattr)
        and isinstance(node.node, nodes.Name)
        and node.node.name == "hostvars"
    )


def _extracted_fact(node: nodes.Filter) -> str | None:
    """Return the fact read by ``extract`` from ``hostvars``.

    Handles ``host | extract(hostvars, 'ansible_fqdn')`` and
    ``hosts | map('extract', hostvars, ['ansible_default_ipv4', 'address'])``.
    """
    args = node.args
    if node.name == "map" and args and isinstance(args[0], nodes.Const):
        if args[0].value != "extract":
            return None
        args = args[1:]
    elif node.name != "extract":
        return None
    if len(args) < 2 or not (
        isinstance(args[0], nodes.Name) and args[0].name == "hostvars"
    ):
        return None
    key = args[1]
    if isinstance(key, nodes.List) and key.items:
        key = key.items[0]
    return _fact_name(key.value) if isinstance(key, nodes.Const) else None


def find_top_level_facts(
    text: str, *, expression: bool = False
) -> list[tuple[str, int]]:
    """Return ``(fact, line)`` for each top-level fact used in ``text``.

    ``text`` is a Jinja template, or a bare expression (as used by ``when``)
    when ``expression`` is True. Text that Jinja cannot parse is ignored.
    """
    if "ansible_" not in text:
        return []
    if expression and "{{" not in text and "{%" not in text:
        text = f"{{{{ {text} }}}}"
    try:
        ast = _env.parse(text)
    except TemplateSyntaxError:
        return []

    found: list[tuple[str, int]] = []
    # names set or looped over inside the template are not facts
    assigned = {node.name for node in ast.find_all(nodes.Name) if node.ctx != "load"}
    for name_node in ast.find_all(nodes.Name):
        fact = _fact_name(name_node.name)
        if fact and name_node.ctx == "load" and name_node.name not in assigned:
            found.append((fact, name_node.lineno))
    for attr_node in ast.find_all(nodes.Getattr):
        fact = _fact_name(attr_node.attr)
        if fact and _is_hostvars_entry(attr_node.node):
            found.append((fact, attr_node.lineno))
    for item_node in ast.find_all(nodes.Getitem):
        if not isinstance(item_node.arg, nodes.Const):
            continue
        fact = _fact_name(item_node.arg.value)
        if fact and _is_hostvars_entry(item_node.node):
            found.append((fact, item_node.lineno))
    for filter_node in ast.find_all(nodes.Filter):
        fact = _extracted_fact(filter_node)
        if fact:
            found.append((fact, filter_node.lineno))
    return sorted(set(found), key=lambda item: (item[1], item[0]))


class DeprecatedTopLevelFactsRule(AnsibleLintRule):
    """Use ``ansible_facts`` instead of top-level fact variables."""

    id = "deprecated-top-level-facts"
    description = (
        "Since ansible-core 2.20, reading facts as top-level ``ansible_*`` "
        "variables is deprecated (``INJECT_FACTS_AS_VARS``). Use "
        "``ansible_facts['<name>']`` instead."
    )
    severity = "MEDIUM"
    tags = ["deprecations", "experimental"]
    version_changed = "26.12.0"

    def _matches_in(
        self,
        data: Any,
        file: Lintable | None,
        ignored_keys: tuple[str, ...] = (),
    ) -> list[MatchError]:
        results: list[MatchError] = []
        for _key, value, _path in nested_items_path(data, ignored_keys=ignored_keys):
            if isinstance(value, str):
                results.extend(
                    self.create_matcherror(
                        message=_message(fact),
                        filename=file,
                        data=value,
                    )
                    for fact, _line in find_top_level_facts(value)
                )
        return results

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        facts: dict[str, None] = {}
        module = task["action"]["__ansible_module__"]
        for key, value, path in nested_items_path(task, ignored_keys=_NESTED_TASK_KEYS):
            if not isinstance(value, str):
                continue
            # list items of `when` and `that` are expressions too
            parent = path[-1] if isinstance(key, int) and path else key
            parent_path = path[:-1] if isinstance(key, int) and path else path
            expression = (not parent_path and parent in _CONDITIONAL_KEYS) or (
                parent_path == ["action"]
                and (
                    (parent == "that" and module in _ASSERT_MODULES)
                    or (parent == "var" and module in _DEBUG_MODULES)
                )
            )
            facts.update(
                (fact, None)
                for fact, _line in find_top_level_facts(value, expression=expression)
            )
        # one match per fact, even when the task uses it several times
        return [
            self.create_matcherror(
                message=_message(fact),
                lineno=task.line,
                filename=file,
            )
            for fact in facts
        ]

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        if file.kind != "playbook" or not isinstance(data, Mapping):
            return []
        # tasks are checked by matchtask
        return self._matches_in(data, file, ignored_keys=_PLAY_TASK_KEYS)

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        if str(file.kind) == "vars":
            data = parse_yaml_from_file(str(file.path))
            if not isinstance(data, Mapping):
                return []
            results = self._matches_in(data, file)
        elif str(file.kind) == "jinja2":
            results = [
                self.create_matcherror(
                    message=_message(fact),
                    lineno=line,
                    filename=file,
                )
                for fact, line in find_top_level_facts(file.content)
            ]
        else:
            return super().matchyaml(file)

        lines = file.content.splitlines()
        return [
            match
            for match in results
            if self.id
            not in get_rule_skips_from_line(
                line=lines[match.lineno - 1] if 0 < match.lineno <= len(lines) else "",
                lintable=file,
            )
        ]


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.file_utils import Lintable
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("text", "expression", "expected"),
        (
            pytest.param(
                "{{ ansible_hostname }}", False, [("hostname", 1)], id="template"
            ),
            pytest.param(
                "ansible_os_family == 'Debian'",
                True,
                [("os_family", 1)],
                id="expression",
            ),
            pytest.param(
                "{{ ansible_default_ipv4.address }} {{ ansible_default_ipv4['address'] }}",
                False,
                [("default_ipv4", 1)],
                id="attribute-and-item",
            ),
            pytest.param(
                "{{ hostvars[item]['ansible_fqdn'] }} {{ hostvars.web1.ansible_kernel }}",
                False,
                [("fqdn", 1), ("kernel", 1)],
                id="hostvars",
            ),
            pytest.param(
                "{{ ansible_facts['hostname'] }}", False, [], id="ansible-facts"
            ),
            pytest.param(
                "{{ hostvars[item].ansible_facts.fqdn }}",
                False,
                [],
                id="hostvars-facts",
            ),
            pytest.param(
                "{{ ansible_host }} {{ ansible_user }} {{ ansible_check_mode }} {{ ansible_local }}",
                False,
                [],
                id="not-facts",
            ),
            pytest.param("{{ ansible_eth0 }}", False, [], id="interface"),
            pytest.param("ansible_hostname", False, [], id="plain-string"),
            pytest.param(
                "{% set ansible_hostname = 'x' %}{{ ansible_hostname }}",
                False,
                [],
                id="locally-assigned",
            ),
            pytest.param(
                "{% for ansible_kernel in items %}{{ ansible_kernel }}{% endfor %}",
                False,
                [],
                id="loop-variable",
            ),
            pytest.param("{{ ansible_hostname", False, [], id="syntax-error"),
            pytest.param(
                "{{ ansible_distribution_version is version('9', '>=') }}",
                False,
                [("distribution_version", 1)],
                id="unknown-jinja-test",
            ),
            pytest.param(
                "{{ ansible_env | to_nice_json }}",
                False,
                [("env", 1)],
                id="unknown-jinja-filter",
            ),
            pytest.param(
                "{{ groups['all'] | map('extract', hostvars, 'ansible_hostname') }}"
                " {{ host | extract(hostvars, ['ansible_default_ipv4', 'address']) }}",
                False,
                [("default_ipv4", 1), ("hostname", 1)],
                id="extract",
            ),
            pytest.param(
                "{{ groups['all'] | map('extract', hostvars, 'main_ip') }}"
                " {{ x | map('upper', hostvars, 'ansible_fqdn') }}",
                False,
                [],
                id="extract-other",
            ),
            pytest.param(
                "line one\n{% if ansible_distribution == 'Fedora' %}x{% endif %}",
                False,
                [("distribution", 2)],
                id="line-number",
            ),
        ),
    )
    def test_find_top_level_facts(
        text: str, expression: bool, expected: list[tuple[str, int]]
    ) -> None:
        """Test which variable references count as top-level facts."""
        assert find_top_level_facts(text, expression=expression) == expected

    def _run(collection: RulesCollection, path: str) -> list[MatchError]:
        collection.register(DeprecatedTopLevelFactsRule())
        return Runner(Lintable(path), rules=collection).run()

    def test_deprecated_top_level_facts_pass(
        empty_rule_collection: RulesCollection,
    ) -> None:
        """Test that a playbook using ansible_facts passes."""
        results = _run(
            empty_rule_collection,
            "examples/playbooks/rule-deprecated-top-level-facts-pass.yml",
        )
        assert results == []

    def test_deprecated_top_level_facts_fail(
        empty_rule_collection: RulesCollection,
    ) -> None:
        """Test that top-level facts are reported in tasks and play vars."""
        results = _run(
            empty_rule_collection,
            "examples/playbooks/rule-deprecated-top-level-facts-fail.yml",
        )
        assert [(match.lineno, match.message) for match in results] == [
            (5, _message("os_family")),
            (8, _message("hostname")),
            (12, _message("distribution")),
            (17, _message("memtotal_mb")),
            (22, _message("fqdn")),
            (26, _message("kernel")),
            (32, _message("pkg_mgr")),
            (36, _message("default_ipv4")),
            (40, _message("hostname")),
        ]
        assert all(match.rule.id == DeprecatedTopLevelFactsRule.id for match in results)

    def test_deprecated_top_level_facts_vars_file(
        empty_rule_collection: RulesCollection,
    ) -> None:
        """Test that top-level facts are reported in vars files."""
        results = _run(
            empty_rule_collection,
            "examples/top_level_facts/group_vars/all.yml",
        )
        assert [(match.lineno, match.message) for match in results] == [
            (2, _message("hostname")),
        ]

    def test_deprecated_top_level_facts_template(
        empty_rule_collection: RulesCollection,
    ) -> None:
        """Test that top-level facts are reported in Jinja templates."""
        results = _run(
            empty_rule_collection,
            "examples/top_level_facts/templates/motd.j2",
        )
        assert [(match.lineno, match.message) for match in results] == [
            (1, _message("fqdn")),
            (3, _message("distribution")),
        ]
