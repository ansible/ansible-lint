"""Module hosting functionality about reporting."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(order=True)
class TagStats:
    """Tag statistics."""

    order: int = 0  # to be computed based on rule's profile
    tag: str = ""  # rule effective id (can be multiple tags per rule id)
    count: int = 0  # total number of occurrences
    warning: bool = False  # set true if listed in warn_list
    profile: str = ""
    associated_tags: list[str] = field(default_factory=list)


class SummarizedResults:
    """The statistics about an ansible-lint run."""

    failures: int = 0
    warnings: int = 0
    fixed_failures: int = 0
    fixed_warnings: int = 0
    tag_stats: dict[str, TagStats] = {}
    passed_profile: str = ""

    @property
    def fixed(self) -> int:
        """Get total fixed count."""
        return self.fixed_failures + self.fixed_warnings

    def sort(self) -> None:
        """Sort tag stats by tag name."""
        self.tag_stats = dict(sorted(self.tag_stats.items(), key=lambda t: t[1]))
