# Copyright (c) 2018, Ansible Project

import re
from typing import TYPE_CHECKING, List

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class MetaVideoLinksRule(AnsibleLintRule):
    id = 'meta-video-links'
    shortdesc = "meta/main.yml video_links should be formatted correctly"
    description = (
        'Items in ``video_links`` in meta/main.yml should be '
        'dictionaries, and contain only keys ``url`` and ``title``, '
        'and have a shared link from a supported provider'
    )
    severity = 'LOW'
    tags = ['metadata']
    version_added = 'v4.0.0'

    VIDEO_REGEXP = {
        'google': re.compile(r'https://drive\.google\.com.*file/d/([0-9A-Za-z-_]+)/.*'),
        'vimeo': re.compile(r'https://vimeo\.com/([0-9]+)'),
        'youtube': re.compile(r'https://youtu\.be/([0-9A-Za-z-_]+)'),
    }

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        if file.kind != 'meta':
            return []

        galaxy_info = data.get('galaxy_info', None)
        if not galaxy_info:
            return []

        video_links = galaxy_info.get('video_links', None)
        if not video_links:
            return []

        results = []

        for video in video_links:
            if not isinstance(video, dict):
                results.append(
                    self.create_matcherror(
                        "Expected item in 'video_links' to be " "a dictionary"
                    )
                )
                continue

            if set(video) != {'url', 'title', '__file__', '__line__'}:
                results.append(
                    self.create_matcherror(
                        "Expected item in 'video_links' to contain "
                        "only keys 'url' and 'title'"
                    )
                )
                continue

            for name, expr in self.VIDEO_REGEXP.items():
                if expr.match(video['url']):
                    break
            else:
                msg = (
                    "URL format '{0}' is not recognized. "
                    "Expected it be a shared link from Vimeo, YouTube, "
                    "or Google Drive.".format(video['url'])
                )
                results.append(self.create_matcherror(msg))

        return results
