"""Used only by vulture to determine reachable code."""

# ExampleComRule
from ansiblelint.rules.args import ArgsRule
from ansiblelint.rules.deprecated_local_action import TaskNoLocalActionRule
from ansiblelint.rules.key_order import KeyOrderRule
from ansiblelint.rules.latest import LatestRule
from ansiblelint.rules.literal_compare import ComparisonToLiteralBoolRule
from ansiblelint.rules.meta_incorrect import MetaChangeFromDefaultRule
from ansiblelint.rules.meta_video_links import MetaVideoLinksRule
from ansiblelint.rules.no_handler import UseHandlerRatherThanWhenChangedRule
from ansiblelint.rules.no_relative_paths import RoleRelativePath
from ansiblelint.rules.no_tabs import NoTabsRule
from ansiblelint.rules.risky_file_permissions import MissingFilePermissionsRule
from ansiblelint.rules.syntax_check import AnsibleSyntaxCheckRule
from test.custom_rules.example_com.example_com_rule import ExampleComRule
from test.custom_rules.example_inc.custom_rule import CustomRule
from test.rules.fixtures.unset_variable_matcher import UnsetVariableMatcherRule

__all__ = [
    "AnsibleSyntaxCheckRule",
    "ArgsRule",
    "ComparisonToLiteralBoolRule",
    "CustomRule",
    "ExampleComRule",
    "KeyOrderRule",
    "LatestRule",
    "MetaChangeFromDefaultRule",
    "MetaVideoLinksRule",
    "MissingFilePermissionsRule",
    "NoTabsRule",
    "RoleRelativePath",
    "TaskNoLocalActionRule",
    "UnsetVariableMatcherRule",
    "UseHandlerRatherThanWhenChangedRule",
]
