r"""Abstract formatters
"""
from __future__ import absolute_import
import os


class BaseFormatter(object):

    @classmethod
    def name(cls):
        return getattr(cls, "_name",
                       cls.__name__.replace("Formatter", "").lower())

    def formats(self, matches, colored=False, **kwargs):
        """
        :param matches: A list of :class:`ansiblelint.Match` objects or []
        :param colored: Colored output will be returned if True
        :return: Formatted string for matches
        """
        return os.linesep.join(self.format(m, colored=colored, **kwargs) for m
                               in matches)

    def format(self, match, colored=False, **kwargs):
        """
        :param match: :class:`ansiblelint.Match` object
        :param colored: Colored output will be returned if True
        :return: Formatted string for match
        """
        return ""
