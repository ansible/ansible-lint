"""Rule that flags Jinja2 tests used as filters."""

import re
import sys
from functools import lru_cache
from typing import List, MutableMapping, Union

import ansible.plugins.test.core
import ansible.plugins.test.files
import ansible.plugins.test.mathstuff

import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import LINE_NUMBER_KEY


class JinjaTestsAsFilters(AnsibleLintRule):

    id = "jinja-tests-as-filters"
    shortdesc = "Using tests as filters is deprecated."
    description = (
        "Using tests as filters is deprecated.\n"
        "Instead of using ``result|failed`` instead use ``result is failed``. "
        "Deprecated in Ansible 2.5; Removed in Ansible 2.9.\n"
        "see: https://github.com/ansible/proposals/issues/83"
    )
    severity = "VERY_HIGH"
    tags = ["deprecations"]
    version_added = "5.3"

    @staticmethod
    @lru_cache
    def ansible_tests():
        # inspired by https://github.com/ansible/ansible/blob/devel/hacking/fix_test_syntax.py
        return (
            list(ansible.plugins.test.core.TestModule().tests().keys())
            + list(ansible.plugins.test.files.TestModule().tests().keys())
            + list(ansible.plugins.test.mathstuff.TestModule().tests().keys())
        )

    @lru_cache
    def tests_as_filter_re(self):
        return re.compile(r"\s*\|\s*" + f"({'|'.join(self.ansible_tests())})" + r"\b")

    def _uses_test_as_filter(self, value: str) -> bool:
        matches = self.tests_as_filter_re().search(value)
        return bool(matches)

    def matchyaml(self, file: Lintable) -> List[MatchError]:
        matches: List[MatchError] = []
        if str(file.base_kind) != 'text/yaml':
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(file)
        if not yaml or (isinstance(yaml, str) and yaml.startswith('$ANSIBLE_VAULT')):
            return matches

        # If we need to let people disable this rule, then we'll need to enable this.
        # yaml = ansiblelint.skip_utils.append_skipped_rules(yaml, file)

        templar = ansiblelint.utils.ansible_templar(str(file.path.parent), {})

        linenumber = 1
        # skip_path = []
        for key, value, parent_path in ansiblelint.utils.nested_items_path(yaml):
            # if key == "skipped_rules":
            #     skip_path = parent_path + [key]
            #     continue
            # elif skip_path and parent_path == skip_path:
            #     continue

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
            if "when" not in yaml_path and not templar.is_template(value):
                continue
            # We have a Jinja2 template string
            template = value if "when" not in parent_path else "{{" + value + "}}"
            if self._uses_test_as_filter(template):
                err = self.create_matcherror(
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
        return self._uses_test_as_filter(line)


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                'examples/roles/role_for_jinja_tests_as_filters/tasks/fail.yml',
                19,
                id='tasks',
            ),
            pytest.param(
                'examples/roles/role_for_jinja_tests_as_filters/templates/sample.ini.j2',
                2,
                id='template',
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
            assert result.message == JinjaTestsAsFilters.shortdesc
