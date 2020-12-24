from ansiblelint.runner import Runner


def test_external_dependency_is_ok(default_rules_collection):
    playbook_path = (
        'test/dependency-in-meta/meta/main.yml'.
        format_map(locals())
    )
    good_runner = Runner(default_rules_collection, playbook_path, [], [], [])
    assert [] == good_runner.run()
