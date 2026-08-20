import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import apply_capcut_polish_profile as profile
import validate_capcut_polish_profile as validator


def _segment(identifier, material_id, start, duration, role=None, source_start=None):
    value = {"id": identifier, "material_id": material_id, "target_timerange": {"start": start, "duration": duration}}
    if role:
        value["role"] = role
    if source_start is not None:
        value["source_timerange"] = {"start": source_start, "duration": duration}
    return value


def _videos(spans):
    """Build (segment, material) pairs from (duration, source_start) pairs."""
    videos, start = [], 0
    for order, (duration, source_start) in enumerate(spans):
        videos.append((_segment(f"video-{order}", "v1", start, duration, source_start=source_start),
                       {"id": "v1", "type": "video"}))
        start += duration
    return videos


class CapCutPolishProfileTest(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        payload = {
            "id": "timeline-test", "main_timeline_id": "timeline-test",
            "materials": {
                "videos": [{"id": "v1", "type": "video", "path": "Resources/media/clean_source.mp4"}, {"id": "v2", "type": "video", "path": "Resources/media/clean_source.mp4"}],
                "audios": [{"id": "a9", "type": "audio", "path": "Resources/media/tts_narrator.wav"}, {"id": "a10", "type": "audio", "path": "Resources/media/a10_vocal_stem.m4a"}],
            },
            "tracks": [
                {"segments": [_segment("video-1", "v1", 0, 2_000_000), _segment("video-2", "v2", 2_000_000, 2_000_000)]},
                {"segments": [_segment("narration", "a9", 0, 1_000_000, "A9")]},
                {"segments": [_segment("source", "a10", 0, 4_000_000, "A10")]},
            ],
        }
        (root / "draft_content.json").write_text(json.dumps(payload), encoding="utf-8")
        return root

    def test_applies_and_verifies_every_required_polish_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = profile.apply_project(project)
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(validator.validate_project(project)["status"], "PASS")
            data = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
            source = data["tracks"][2]["segments"][0]
            self.assertEqual(source["volume"], 0.0)
            self.assertNotIn("vocal_separations", data["materials"])
    def test_flashes_land_only_on_real_jumps(self):
        # Four one-second cuts; only the seam into the third is discontinuous.
        videos = _videos([(1_000_000, 0), (1_000_000, 1_000_000),
                          (1_000_000, 8_000_000), (1_000_000, 9_000_000)])
        self.assertEqual(profile.select_flash_orders(videos), [1])

    def test_a_continuous_timeline_still_gets_one_flash_every_ten_seconds(self):
        # Twenty seamless two-second cuts: no jumps at all, so the floor rules.
        videos = _videos([(2_000_000, order * 2_000_000) for order in range(20)])
        orders = profile.select_flash_orders(videos)
        self.assertTrue(orders, "the floor must promote plain cuts")
        self._assert_density(videos, orders)

    def test_dense_jumps_are_thinned_to_two_per_ten_seconds(self):
        # Half-second jump cuts back to back would otherwise flash 39 times.
        videos = _videos([(500_000, (39 - order) * 500_000) for order in range(40)])
        orders = profile.select_flash_orders(videos)
        self.assertLess(len(orders), 10)
        self._assert_density(videos, orders)

    def test_the_reordered_episode_thins_from_every_cut_to_a_handful(self):
        spans = [(3_250_000, 33_625_000), (1_125_000, 36_875_000), (2_125_000, 2_500_000),
                 (2_000_000, 4_625_000), (2_000_000, 14_250_000), (2_000_000, 16_250_000),
                 (1_125_000, 6_625_000), (1_250_000, 7_750_000), (750_000, 0),
                 (1_750_000, 750_000), (1_625_000, 9_000_000), (2_000_000, 10_625_000),
                 (1_625_000, 12_625_000), (1_875_000, 18_250_000), (1_125_000, 20_125_000),
                 (1_750_000, 21_250_000), (2_250_000, 23_000_000), (1_500_000, 25_250_000),
                 (1_625_000, 26_750_000), (1_000_000, 28_375_000), (2_000_000, 29_375_000),
                 (1_000_000, 31_375_000), (1_250_000, 32_375_000), (1_125_000, 38_000_000),
                 (2_020_000, 39_125_000)]
        videos = _videos(spans)
        orders = profile.select_flash_orders(videos)
        self.assertEqual(orders, [1, 3, 7, 12, 17, 22])
        self._assert_density(videos, orders)

    def _assert_density(self, videos, orders):
        times = [profile._range(videos[order][0])[1] for order in orders]
        end = profile._range(videos[-1][0])[1]
        for boundary in [0, *times]:
            following = next((time for time in times if time > boundary), end)
            self.assertLessEqual(following - boundary, profile.FLASH_WINDOW_US,
                                 f"a {profile.FLASH_WINDOW_US}us hole opens after {boundary}")
        for time in times:
            window = [other for other in times if time - profile.FLASH_WINDOW_US < other <= time]
            self.assertLessEqual(len(window), profile.FLASH_MAX_PER_WINDOW,
                                 f"{len(window)} flashes crowd the window ending at {time}")

    def test_a_clone_loses_the_transitions_the_rule_did_not_choose(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            profile.apply_project(project)
            data = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
            # Hand the second cut a stale transition the way a clone would.
            stale = {**profile.W_FLASH, "id": "stale-transition"}
            data["materials"]["transitions"].append(stale)
            data["tracks"][0]["segments"][1].setdefault("extra_material_refs", []).append("stale-transition")
            (project / "draft_content.json").write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(validator.validate_project(project)["status"], "FAIL")
            profile.apply_project(project)
            self.assertEqual(validator.validate_project(project)["status"], "PASS")
            data = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
            self.assertNotIn("stale-transition", data["tracks"][0]["segments"][1]["extra_material_refs"])
            self.assertNotIn("stale-transition", [row["id"] for row in data["materials"]["transitions"]])


if __name__ == "__main__":
    unittest.main()
