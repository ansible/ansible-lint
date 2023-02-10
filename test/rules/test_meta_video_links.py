"""Tests for meta-video-links rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.meta_video_links import MetaVideoLinksRule
from ansiblelint.testing import RunFromText

META_VIDEO_LINKS = """
galaxy_info:
  video_links:
  - url: https://www.youtube.com/watch?v=aWmRepTSFKs&feature=youtu.be
    title: Proper format
  - https://www.youtube.com/watch?v=aWmRepTSFKs&feature=youtu.be
  - my_bad_key: https://www.youtube.com/watch?v=aWmRepTSFKs&feature=youtu.be
    title: This has a bad key
  - url: www.acme.com/vid
    title: Bad format of url
"""


def test_video_links() -> None:
    """Test meta_video_links."""
    collection = RulesCollection()
    collection.register(MetaVideoLinksRule())
    runner = RunFromText(collection)

    results = runner.run_role_meta_main(META_VIDEO_LINKS)
    assert "Expected item in 'video_links' to be a dictionary" in str(results)
    assert "'video_links' to contain only keys 'url' and 'title'" in str(results)
    assert "URL format 'www.acme.com/vid' is not recognized" in str(results)
