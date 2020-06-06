import pytest

from ansiblelint.runner import Runner


@pytest.mark.parametrize(
    'filename',
    (
        'bitbucket',
        'galaxy',
        'github',
        'webserver',
        'gitlab',
    ),
)
def test_external_dependency_is_ok(default_rules_collection, filename):
    playbook_path = (
        'test/dependency-in-meta/{filename}.yml'.
        format_map(locals())
    )
    good_runner = Runner(default_rules_collection, playbook_path, [], [], [])
    assert [] == good_runner.run()
