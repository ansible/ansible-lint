# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.MetaVideoLinksRule import MetaVideoLinksRule
from ansiblelint.testing import RunFromText

META_VIDEO_LINKS = '''
galaxy_info:
  video_links:
  - url: https://youtu.be/aWmRepTSFKs
    title: Proper format
  - https://youtu.be/this_is_not_a_dictionary
  - my_bad_key: https://youtu.be/aWmRepTSFKs
    title: This has a bad key
  - url: www.myvid.com/vid
    title: Bad format of url
'''


class TestMetaVideoLinks(unittest.TestCase):
    collection = RulesCollection()
    collection.register(MetaVideoLinksRule())

    def setUp(self) -> None:
        self.runner = RunFromText(self.collection)

    def test_video_links(self) -> None:
        results = self.runner.run_role_meta_main(META_VIDEO_LINKS)
        assert "Expected item in 'video_links' to be a dictionary" in str(results)
        assert "'video_links' to contain only keys 'url' and 'title'" in str(results)
        assert "URL format 'www.myvid.com/vid' is not recognized" in str(results)
