"""A test plugin."""
# pylint: disable=invalid-name


def compatibility_in_test(a, b):
    """Return True when a is contained in b."""
    return a in b


# pylint: disable=too-few-public-methods
class TestModule:
    """Test plugin."""

    @staticmethod
    def tests():
        """Return tests."""
        return {
            "b_test_failed_complete": compatibility_in_test,
        }
