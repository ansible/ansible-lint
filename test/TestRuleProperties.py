def test_serverity_valid(default_rules_collection):
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
