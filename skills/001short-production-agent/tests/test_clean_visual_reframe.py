import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_clean_visual import _portrait_aspect_compatible


LANDSCAPE = (1920, 1080)
PORTRAIT = (1080, 1920)


class CleanVisualReframeTest(unittest.TestCase):
    """Pulling a Short out of a landscape longform reframes the clean asset to
    portrait, so its aspect deliberately differs from the source.  Accepting that
    for every landscape source would drop the guard entirely - an undeclared
    aspect change is exactly the mistake it exists to catch - so the reframe has
    to be declared in the manifest."""

    def test_a_landscape_source_needs_the_reframe_declared(self):
        self.assertFalse(_portrait_aspect_compatible(*LANDSCAPE, *PORTRAIT))
        self.assertFalse(
            _portrait_aspect_compatible(*LANDSCAPE, *PORTRAIT, "SAME_FRAMING_AS_SOURCE"))
        self.assertTrue(
            _portrait_aspect_compatible(*LANDSCAPE, *PORTRAIT, "REFRAME_TO_PORTRAIT"))

    def test_a_portrait_source_still_has_to_keep_its_aspect(self):
        self.assertTrue(_portrait_aspect_compatible(*PORTRAIT, *PORTRAIT))
        # A declared reframe is not a way around the ratio check when the source
        # was already portrait: 720x1560 is a different shape from 1080x1920.
        self.assertFalse(
            _portrait_aspect_compatible(*PORTRAIT, 720, 1560, "REFRAME_TO_PORTRAIT"))

    def test_the_result_still_has_to_be_portrait(self):
        for transform in (None, "REFRAME_TO_PORTRAIT"):
            self.assertFalse(_portrait_aspect_compatible(*LANDSCAPE, *LANDSCAPE, transform))
            self.assertFalse(_portrait_aspect_compatible(*PORTRAIT, *LANDSCAPE, transform))

    def test_a_missing_dimension_is_never_compatible(self):
        self.assertFalse(_portrait_aspect_compatible(0, 1080, *PORTRAIT, "REFRAME_TO_PORTRAIT"))
        self.assertFalse(_portrait_aspect_compatible(*LANDSCAPE, 1080, 0, "REFRAME_TO_PORTRAIT"))


if __name__ == "__main__":
    unittest.main()
