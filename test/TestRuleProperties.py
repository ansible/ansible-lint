from ansiblelint.rules import RulesCollection


def test_serverity_valid(default_rules_collection: RulesCollection) -> None:
    """Test that rules collection only has allow-listed severities."""
    valid_severity_values = [
        'VERY_HIGH',
        'HIGH',
        'MEDIUM',
        'LOW',
        'VERY_LOW',
        'INFO',
    ]
    for rule in default_rules_collection:
        assert rule.severity in valid_severity_values
