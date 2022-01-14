"""Rule that finds using non-namespaced ansible_facts."""

import re
import sys
from functools import lru_cache
from typing import List, MutableMapping, Optional, Union

from ansible.constants import MAGIC_VARIABLE_MAPPING

import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY

# This is probably a partial list of facts.
# There is no nice way to extract a list of possible facts from ansible.
# The initial list extracted with:
#   ansible.module_utils.facts.default_collectors.collectors
#     {c.name: list(c._fact_ids) for c in collectors}
FACT_NAMES_BY_COLLECTOR = {
    'platform': [
        # _fact_ids
        'system',
        'kernel',
        'kernel_version',
        'machine',
        'python_version',
        'architecture',
        'machine_id',
        # manually scraped
        'fqdn',
        'hostname',
        'nodename',
        'domain',
        'userspace_bits',
        'userspace_architecture',
    ],
    'distribution': [
        'distribution',
        # _fact_ids
        'distribution_version',
        'distribution_release',
        'distribution_major_version',
        'os_family',
        # manually scraped
        'distribution_file_search_string',
        'distribution_file_path',
        'distribution_file_variety',
        'distribution_file_parsed',
    ],
    'lsb': ['lsb'],  # ansible_lsb is a dict
    'selinux': [
        'selinux',  # ansible_selinux is a dict
        # manually scraped
        'selinux_python_present',
    ],
    'apparmor': ['apparmor'],  # ansible_apparmor is a dict
    'chroot': ['is_chroot'],
    'fips': ['fips'],
    'python': ['python'],  # ansible_python is a dict
    'caps': ['system_capabilities_enforced', 'system_capabilities'],
    'pkg_mgr': ['pkg_mgr'],
    'service_mgr': ['service_mgr'],
    'cmdline': [
        'cmdline',  # ansible_cmdline is a dict
        # manually scraped
        'proc_cmdline',
    ],
    'date_time': ['date_time'],  # ansible_date_time is a dict
    'env': ['env'],  # ansible_env is a dict
    'ssh_pub_keys': [
        'ssh_host_keys',
        # _fact_ids
        'ssh_host_pub_keys',
        'ssh_host_key_dsa_public',
        'ssh_host_key_rsa_public',
        'ssh_host_key_ecdsa_public',
        'ssh_host_key_ed25519_public',
        # manually scraped
        'ssh_host_key_dsa_public_keytype',
        'ssh_host_key_rsa_public_keytype',
        'ssh_host_key_ecdsa_public_keytype',
        'ssh_host_key_ed25519_public_keytype',
    ],
    'user': [
        # _fact_ids
        'user_id',
        'user_uid',
        'user_gid',
        'user_gecos',
        'user_dir',
        'user_shell',
        'real_user_id',
        'effective_user_id',
        'effective_group_ids',
    ],
    'virtual': [
        # _fact_ids
        'virtualization_type',
        'virtualization_role',
        'virtualization_tech_guest',
        'virtualization_tech_host',
        # manually scraped
        'container',
    ],
    'hardware': [
        # _fact_ids
        'processor',  # a list
        'processor_cores',
        'processor_count',
        'mounts',  # a list
        'devices',  # a dict
        # manually scraped
        'processor_threads_per_core',
        'processor_vcpus',
        'processor_nproc',
        'memfree_mb',
        'memtotal_mb',
        'swapfree_mb',
        'swaptotal_mb',
        'swap_allocated_mb',
        'swap_reserved_mb',
        'memory_mb',  # a dict
        'device_links',  # a dict
        'lvm',  # a dict
        'uptime_seconds',
        'bios_date',
        'bios_vendor',
        'bios_version',
        'board_asset_tag',
        'board_name',
        'board_serial',
        'board_vendor',
        'board_version',
        'chassis_asset_tag',
        'chassis_serial',
        'chassis_vendor',
        'chassis_version',
        'form_factor',
        'product_name',
        'product_serial',
        'product_uuid',
        'product_version',
        'system_vendor',
        'model',
        'firmware_version',
        'lpar_info',
        'vgs',  # a dict
        'osversion',
        'osrevision',
    ],
    'dns': ['dns'],  # ansible_dns is a dict
    'fibre_channel_wwn': ['fibre_channel_wwn'],  # a list
    'network': [
        # _fact_ids
        'interfaces',  # a list
        'default_ipv4',
        'default_ipv6',
        'all_ipv4_addresses',
        'all_ipv6_addresses',
        # manually scraped
        # '*',  # a dict (* is any name of interface like eth0)
        'default_interface',
        'default_gateway',
    ],
    'iscsi': ['iscsi_iqn'],
    'nvme': ['hostnqn'],
    # This does not have the be accessed via ansible_facts
    # 'local': ['local'],  # ansible_local is a dict
    # 'facter': ['facter_*'],  # facts namespaced under facter
    # 'ohai': ['ohai_*'],  # facts namespaced under ohai
}
KNOWN_FACT_NAMES = {
    fact for facts in FACT_NAMES_BY_COLLECTOR.values() for fact in facts
}
KNOWN_FACT_NAME_PREFIXES = ['facter_', 'ohai_']

# from https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html
PREFIXLESS_MAGIC_VARS = {  # without the "ansible_" prefix
    # Documented Fact Dicts
    "facts",
    "local",
    # Documented Magic Vars
    "check_mode",
    "config_file",
    "dependent_role_names",
    "diff_mode",
    "forks",
    "inventory_sources",
    "limit",
    "loop",
    "loop_var",
    "index_var",
    "parent_role_names",
    "parent_role_paths",
    "play_batch",
    "play_hosts",
    "play_hosts_hall",
    "play_role_names",
    "playbook_python",
    "role_names",
    "role_name",
    "collection_name",
    "run_tags",
    "search_path",
    "skip_tags",
    "verbosity",
    "version",
    "play_name",
    # Not documented and not included in MAGIC_VARIABLE_MAPPING (below)
    "delegated_vars",
    "python_interpreter",
}
# MAGIC_VARIABLE_MAPPING has lists of magic vars that are, for the most part,
# not listed in the Special Variables doc. It does not include vars listed
# above. It includes vars for connection, shell, become, etc.
# key is property name, value is tuple of magic var names
_prefix_len = len("ansible_")
PREFIXLESS_MAGIC_VARS.update(
    {
        v[_prefix_len:]
        for k, magic_vars in MAGIC_VARIABLE_MAPPING.items()
        for v in magic_vars
    }
)
MAGIC_VAR_SUFFIXES = ["_host", "_port", "_user", "_interpreter"]


@lru_cache
def _re_possible_net_interface() -> re.Pattern[str]:
    # Based on (MIT licensed):
    # https://github.com/bosun-monitor/bosun/blob/db70a05b517710cbf39e000c497155cb6b178e34/cmd/scollector/collectors/ifstat_linux.go#L54-L58
    return re.compile(
        r"eth\d+|em\d+_\d+|em\d+|"
        r"bond\d+|team\d+|p\d+p\d+|"  # simplified the p\d+p\d+ cases. Just use as a prefix.
        r"en[a-zA-Z0-9]+|wl[a-zA-Z0-9]+|ww[a-zA-Z0-9]+"  # Systemd predictable interface names
    )


def is_fact_name(name: str) -> Optional[bool]:
    if name in PREFIXLESS_MAGIC_VARS:
        # confident: node_name IS NOT a fact
        return False

    if (
        name in KNOWN_FACT_NAMES
        or any(name.startswith(prefix) for prefix in KNOWN_FACT_NAME_PREFIXES)
        # try to guess if this is a network interface "ansible_<interface>"
        or _re_possible_net_interface().match(name)
    ):
        # confident: node_name IS a fact
        return True

    # ignore remaining possible magic vars (must be after the prefix check)
    if any(name.endswith(suffix) for suffix in MAGIC_VAR_SUFFIXES):
        return False

    # ambiguous: node_name MIGHT BE a fact
    return None  # use None to signal ambiguity


class AnsibleFactsNamespacingRule(AnsibleLintRule):

    id = "facts-namespacing"
    shortdesc = (
        "Facts are now namespaced. Look for them in the special ansible_facts var."
    )
    description = (
        "Ansible facts are available under the ``ansible_facts.*`` namespace. "
        "Accessing the ``ansible_*`` vars was deprecated in Ansible 2.5. "
        "Setting ``inject_facts_as_vars=False`` in ansible.cfg disables "
        "the legacy behavior of adding facts to the vars namespace. See: "
        "https://docs.ansible.com/ansible/latest/porting_guides/porting_guide_2.5.html#ansible-fact-namespacing"
    )
    severity = "MEDIUM"
    tags = ["deprecations"]
    version_added = "5.3"

    def _error_message(self, legacy_facts: List[str]) -> str:
        # legacy_facts is a list of in-use fact names without the "ansible_" prefix.
        msg = self.shortdesc + (
            "\nMake these changes (original --> use this instead):\n"
        )
        for fact in legacy_facts:
            msg += f"  ansible_{fact} --> ansible_facts.{fact}\n"
        return msg

    @lru_cache
    def _re_possible_facts(self) -> re.Pattern[str]:
        # MAGIC_VARIABLE_MAPPING includes the ssh variants for:
        # ansible_*_host, ansible_*_port, ansible_*_user
        # And I include the python variant of: ansible_*_interpreter
        # These are handled with .endswith()/.startswith() for now,
        # but they could probably be added to this regex.
        return re.compile(
            r"\bansible_"  # match word that starts with "ansible_"
            + r"(?!"  # Non-capturing group
            + r"\b|".join(PREFIXLESS_MAGIC_VARS)  # do not match non-fact vars
            + r"\b)"  # only full word matches, not prefixes
            + r"([a-zA-Z0-9_]+)\b"  # any valid var chars till the end of the word
        )

    def _uses_ansible_facts_as_vars(self, value: str) -> List[str]:
        if "ansible_" not in value:
            return []
        found_facts = set()

        # known magic vars were excluded via the regex.
        possible_facts: List[str] = self._re_possible_facts().findall(value)

        for possible_fact in possible_facts:
            is_a_fact = is_fact_name(possible_fact)
            might_be_a_fact = is_a_fact is None  # None signals ambiguity
            if is_a_fact:
                found_facts.add(possible_fact)
                # found a fact. stop looking.
                continue
            if might_be_a_fact:
                # This is very ambiguous. It might be a fact or it might not.
                # Maybe add a config var to determine whether to add this.
                found_facts.add(possible_fact)

        return list(found_facts)

    def matchyaml(self, file: Lintable) -> List[MatchError]:
        matches: List[MatchError] = []
        if str(file.base_kind) != 'text/yaml':
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(file)
        if not yaml or (isinstance(yaml, str) and yaml.startswith('$ANSIBLE_VAULT')):
            return matches

        yaml = ansiblelint.skip_utils.append_skipped_rules(yaml, file)

        templar = ansiblelint.utils.ansible_templar(str(file.path.parent), {})

        linenumber = 1
        skip_path = []
        for key, value, parent_path in ansiblelint.utils.nested_items_path(yaml):
            if key == "skipped_rules":
                skip_path = parent_path + [key]
                continue
            elif skip_path and parent_path == skip_path:
                continue

            # we can only get the linenumber from the most recent dictionary.
            if isinstance(value, MutableMapping):
                linenumber = value.get(LINE_NUMBER_KEY, linenumber)

            # We handle looping through lists/dicts to get parent_path.
            # So, only strings can be Jinja2 templates.
            if not isinstance(value, str) or (
                isinstance(key, str) and key.startswith("__") and key.endswith("__")
            ):
                continue
            yaml_path = parent_path + [key]
            do_wrap_template = "when" in yaml_path or yaml_path[-2:] == ["debug", "var"]
            if not do_wrap_template and not templar.is_template(value):
                continue
            # We have a Jinja2 template string
            template = "{{" + value + "}}" if do_wrap_template else value
            legacy_facts = self._uses_ansible_facts_as_vars(template)
            if legacy_facts:
                msg = self._error_message(legacy_facts)
                err = self.create_matcherror(
                    message=msg,
                    linenumber=linenumber,
                    details=value,
                    filename=file,
                )
                err.yaml_path = yaml_path
                matches.append(err)
        return matches

    def matchlines(self, file: "Lintable") -> List[MatchError]:
        """Match template lines."""
        matches: List[MatchError] = []
        # we handle yaml separately to handle things like when templates.
        if str(file.base_kind) != 'text/jinja2':
            return matches

        templar = ansiblelint.utils.ansible_templar(str(file.path.parent), {})

        if not templar.is_template(file.content):
            return matches

        matches: List[MatchError] = super().matchlines(file)
        return matches

    def match(self, line: str) -> Union[bool, str]:
        """Match template lines."""
        legacy_facts = self._uses_ansible_facts_as_vars(line)
        if legacy_facts:
            return self._error_message(legacy_facts)
        return False


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                'examples/roles/role_for_facts_namespacing/tasks/fail.yml',
                7,
                id='fail_tasks',
            ),
            pytest.param(
                'examples/roles/role_for_facts_namespacing/tasks/fail.transformed.yml',
                0,
                id='pass_tasks',
            ),
            pytest.param(
                'examples/roles/role_for_facts_namespacing/templates/sample.ini.j2',
                6,
                id='fail_template',
            ),
            pytest.param(
                'examples/roles/role_for_facts_namespacing/templates/sample.ini.transformed.j2',
                0,
                id='pass_template',
            ),
        ),
    )
    def test_jinja_tests_as_filters_rule(
        default_rules_collection: RulesCollection, test_file: str, failures: int
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
        for result in results:
            assert result.message.startswith(AnsibleFactsNamespacingRule.shortdesc)
