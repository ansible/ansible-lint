"""A test plugin."""


def compatibility_in_test(element, container):
    """Return True when element is contained in container."""
    return element in container


# pylint: disable=too-few-public-methods
class TestModule:
    """Test plugin."""

    @staticmethod
    def tests():
        """Return tests."""
        return {
            "b_test_failed": compatibility_in_test,
        }
