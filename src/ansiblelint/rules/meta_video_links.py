"""Implementation of meta-video-links rule."""
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ansiblelint.constants import FILENAME_KEY, LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class MetaVideoLinksRule(AnsibleLintRule):
    """meta/main.yml video_links should be formatted correctly."""

    id = "meta-video-links"
    description = (
        "Items in ``video_links`` in meta/main.yml should be "
        "dictionaries, and contain only keys ``url`` and ``title``, "
        "and have a shared link from a supported provider"
    )
    severity = "LOW"
    tags = ["metadata"]
    version_added = "v4.0.0"

    VIDEO_REGEXP = {
        "google": re.compile(r"https://drive\.google\.com.*file/d/([0-9A-Za-z-_]+)/.*"),
        "vimeo": re.compile(r"https://vimeo\.com/([0-9]+)"),
        "youtube": re.compile(r"https://youtu\.be/([0-9A-Za-z-_]+)"),
    }

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        if file.kind != "meta" or not file.data:
            return []

        galaxy_info = file.data.get("galaxy_info", None)
        if not galaxy_info:
            return []

        video_links = galaxy_info.get("video_links", None)
        if not video_links:
            return []

        results = []

        for video in video_links:
            if not isinstance(video, dict):
                results.append(
                    self.create_matcherror(
                        "Expected item in 'video_links' to be a dictionary",
                        filename=file,
                    )
                )
                continue

            if set(video) != {"url", "title", FILENAME_KEY, LINE_NUMBER_KEY}:
                results.append(
                    self.create_matcherror(
                        "Expected item in 'video_links' to contain "
                        "only keys 'url' and 'title'",
                        filename=file,
                    )
                )
                continue

            for _, expr in self.VIDEO_REGEXP.items():
                if expr.match(video["url"]):
                    break
            else:
                msg = (
                    f"URL format '{video['url']}' is not recognized. "
                    "Expected it be a shared link from Vimeo, YouTube, "
                    "or Google Drive."
                )
                results.append(self.create_matcherror(msg, filename=file))

        return results
