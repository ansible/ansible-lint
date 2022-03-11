"""A test plugin."""


def compatibility_in_test(element, container):
    """Return True when element is contained in container."""
    return element in container


class TestModule:
    """Test plugin."""

    def tests(self):
        """Return tests."""
        return {
            "b_test_failed": compatibility_in_test,
        }
