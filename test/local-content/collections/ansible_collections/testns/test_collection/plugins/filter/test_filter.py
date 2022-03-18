"""A filter plugin."""
# pylint: disable=invalid-name


def a_test_filter(a, b):
    """Return a string containing both a and b."""
    return f"{a}:{b}"


# pylint: disable=too-few-public-methods
class FilterModule:
    """Filter plugin."""

    @staticmethod
    def filters():
        """Return filters."""
        return {"test_filter": a_test_filter}
