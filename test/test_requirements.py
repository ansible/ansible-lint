"""Tests requirements module."""

from ansible_compat.runtime import Runtime

from ansiblelint.requirements import Reqs


def test_reqs() -> None:
    """Performs basic testing of Reqs class."""
    reqs = Reqs()
    runtime = Runtime()
    assert "ansible-core" in reqs
    # checks that this ansible core version is not supported:
    assert reqs.matches("ansible-core", "0.0") is False
    # assert that invalid package name
    assert reqs.matches("this-package-does-not-exist", "0.0") is False
    # check the current ansible core version is supported:
    assert reqs.matches("ansible-core", runtime.version)
