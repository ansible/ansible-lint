# Copyright (c) 2018, Ansible Project

import re
import sys
from typing import TYPE_CHECKING, List

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class MetaTagValidRule(AnsibleLintRule):
    id = 'meta-no-tags'
    shortdesc = 'Tags must contain lowercase letters and digits only'
    description = (
        'Tags must contain lowercase letters and digits only, '
        'and ``galaxy_tags`` is expected to be a list'
    )
    severity = 'HIGH'
    tags = ['metadata']
    version_added = 'v4.0.0'

    TAG_REGEXP = re.compile('^[a-z0-9]+$')

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        if file.kind != 'meta':
            return []

        galaxy_info = data.get('galaxy_info', None)
        if not galaxy_info:
            return []

        tags = []
        results = []

        if 'galaxy_tags' in galaxy_info:
            if isinstance(galaxy_info['galaxy_tags'], list):
                tags += galaxy_info['galaxy_tags']
            else:
                results.append(
                    self.create_matcherror("Expected 'galaxy_tags' to be a list")
                )

        if 'categories' in galaxy_info:
            results.append(
                self.create_matcherror("Use 'galaxy_tags' rather than 'categories'")
            )
            if isinstance(galaxy_info['categories'], list):
                tags += galaxy_info['categories']
            else:
                results.append(
                    self.create_matcherror("Expected 'categories' to be a list")
                )

        for tag in tags:
            msg = self.shortdesc
            if not isinstance(tag, str):
                results.append(
                    self.create_matcherror("Tags must be strings: '{}'".format(tag))
                )
                continue
            if not re.match(self.TAG_REGEXP, tag):
                results.append(
                    self.create_matcherror(message="{}, invalid: '{}'".format(msg, tag))
                )

        return results


META_TAG_VALID = '''
galaxy_info:
    galaxy_tags: ['database', 'my s q l', 'MYTAG']
    categories: 'my_category_not_in_a_list'
'''

# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    @pytest.mark.parametrize(
        'rule_runner', (MetaTagValidRule,), indirect=['rule_runner']
    )
    def test_valid_tag_rule(rule_runner: "Any") -> None:
        """Test rule matches."""
        results = rule_runner.run_role_meta_main(META_TAG_VALID)
        assert "Use 'galaxy_tags' rather than 'categories'" in str(results)
        assert "Expected 'categories' to be a list" in str(results)
        assert "invalid: 'my s q l'" in str(results)
        assert "invalid: 'MYTAG'" in str(results)
