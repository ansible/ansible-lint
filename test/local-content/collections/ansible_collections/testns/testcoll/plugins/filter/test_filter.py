"""A filter plugin."""


def a_test_filter(a, b):
    """Return a string containing both a and b."""
    return '{0}:{1}'.format(a, b)


class FilterModule:
    """Filter plugin."""

    def filters(self):
        """Return filters."""
        return {'test_filter': a_test_filter}
