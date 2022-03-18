"""Tests for no-jinja-when rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.no_jinja_when import NoFormattingInWhenRule
from ansiblelint.runner import Runner


def test_file_positive() -> None:
    """Positive test for no-jinja-when."""
    collection = RulesCollection()
    collection.register(NoFormattingInWhenRule())
    success = "examples/playbooks/jinja2-when-success.yml"
    good_runner = Runner(success, rules=collection)
    assert [] == good_runner.run()


def test_file_negative() -> None:
    """Negative test for no-jinja-when."""
    collection = RulesCollection()
    collection.register(NoFormattingInWhenRule())
    failure = "examples/playbooks/jinja2-when-failure.yml"
    bad_runner = Runner(failure, rules=collection)
    errs = bad_runner.run()
    assert len(errs) == 2
