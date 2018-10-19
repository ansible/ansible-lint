r"""JSON formatter
"""
from __future__ import absolute_import
import json
from .base import BaseFormatter


class JsonFormatter(BaseFormatter):

    def formats(self, matches, **kwargs):
        """
        :param matches: A list of :class:`ansiblelint.Match` objects
        :return: Formatted string for matches
        """
        return json.dumps([m.as_dict() for m in matches], indent=2)
