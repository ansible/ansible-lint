import logging
import os
import sys
from typing import TYPE_CHECKING, List

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError

_logger = logging.getLogger(__name__)

# yamllint is a soft-dependency (not installed by default)
try:
    from yamllint.config import YamlLintConfig
    from yamllint.linter import run as run_yamllint
except ImportError:
    pass


YAMLLINT_CONFIG = """
extends: default
rules:
  document-start: disable
  # 160 chars was the default used by old E204 rule, but
  # you can easily change it or disable in your .yamllint file.
  line-length:
    max: 160
"""

DESCRIPTION = """\
Rule violations reported by YamlLint when this is installed.

You can fully disable all of them by adding 'YAML' to the 'skip_list'.

Specific tag identifiers that are printed at the end of rule name,
like 'trailing-spaces' or 'indentation' can also be be skipped, allowing
you to have a more fine control.
"""


class YamllintRule(AnsibleLintRule):
    id = 'YAML'
    shortdesc = 'Violations reported by yamllint'
    description = DESCRIPTION
    severity = 'VERY_LOW'
    tags = ['formatting', 'experimental', 'yamllint']
    version_added = 'v5.0.0'
    config = None
    if "yamllint.config" in sys.modules:
        config = YamlLintConfig(content=YAMLLINT_CONFIG)
        # if we detect local yamllint config we use it but raise a warning
        # as this is likely to get out of sync with our internal config.
        for file in ['.yamllint', '.yamllint.yaml', '.yamllint.yml']:
            if os.path.isfile(file):
                _logger.warning(
                    "Loading custom %s config file, this extends our "
                    "internal yamllint config.",
                    file)
                config_override = YamlLintConfig(file=file)
                config_override.extend(config)
                break
        _logger.debug("Effective yamllint rules used: %s", config.rules)

    def __init__(self) -> None:
        """Construct a rule instance."""
        # customize id by adding the one reported by yamllint
        self.id = self.__class__.id

    def matchyaml(self, file: Lintable) -> List["MatchError"]:
        """Return matches found for a specific YAML text."""
        matches = []
        filtered_matches = []

        if YamllintRule.config:
            for p in run_yamllint(file.content, YamllintRule.config):
                matches.append(
                    self.create_matcherror(
                        message=p.desc,
                        linenumber=p.line,
                        details="",
                        filename=str(file.path),
                        tag=p.rule))

        if matches:
            lines = file.content.splitlines()
            for match in matches:
                # rule.linenumber starts with 1, not zero
                skip_list = get_rule_skips_from_line(lines[match.linenumber-1])
                # print(skip_list)
                if match.rule.id not in skip_list and match.tag not in skip_list:
                    filtered_matches.append(match)
        return filtered_matches
