"""Tests for config module."""

from ansiblelint.config import PROFILES
from ansiblelint.rules import RulesCollection


def test_profiles(default_rules_collection: RulesCollection) -> None:
    """Test the rules included in profiles are valid."""
    profile_banned_tags = {"opt-in", "experimental"}
    for name, data in PROFILES.items():
        for profile_rule_id in data["rules"]:
            for rule in default_rules_collection.rules:
                if profile_rule_id == rule.id:
                    forbidden_tags = profile_banned_tags & set(rule.tags)
                    assert (
                        not forbidden_tags
                    ), f"Rule {profile_rule_id} from {name} profile cannot use {profile_banned_tags & set(rule.tags)} tag."
