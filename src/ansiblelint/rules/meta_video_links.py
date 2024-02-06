"""Implementation of meta-video-links rule."""

# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from ansiblelint.constants import FILENAME_KEY, LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from collections.abc import Sequence

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
                    ),
                )
                continue

            if set(video) != {"url", "title", FILENAME_KEY, LINE_NUMBER_KEY}:
                results.append(
                    self.create_matcherror(
                        "Expected item in 'video_links' to contain "
                        "only keys 'url' and 'title'",
                        filename=file,
                    ),
                )
                continue

            for expr in self.VIDEO_REGEXP.values():
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


if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                "examples/roles/meta_video_links_fail/meta/main.yml",
                (
                    "Expected item in 'video_links' to be a dictionary",
                    "Expected item in 'video_links' to contain only keys 'url' and 'title'",
                    "URL format 'https://www.youtube.com/watch?v=aWmRepTSFKs&feature=youtu.be' is not recognized. Expected it be a shared link from Vimeo, YouTube, or Google Drive.",
                    "URL format 'www.acme.com/vid' is not recognized",
                ),
                id="1",
            ),
            pytest.param(
                "examples/roles/meta_video_links_pass/meta/main.yml",
                (),
                id="2",
            ),
        ),
    )
    def test_video_links(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: Sequence[str],
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == len(failures)
        for index, result in enumerate(results):
            assert result.tag == "meta-video-links"
            assert failures[index] in result.message
