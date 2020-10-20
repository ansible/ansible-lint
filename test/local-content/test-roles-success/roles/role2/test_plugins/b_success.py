"""A test plugin."""


def compatibility_in_test(a, b):
    """Return True when a is contained in b."""
    return a in b


class TestModule:
    """Test plugin."""

    def tests(self):
        """Return tests."""
        return {
            'b_test_success': compatibility_in_test,
        }
