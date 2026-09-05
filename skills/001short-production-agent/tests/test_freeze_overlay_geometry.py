import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import user_provided_media_overlay as overlay


class FreezeGeometryTest(unittest.TestCase):
    def setUp(self):
        self.item = {'media_kind': 'image', 'match_video_geometry': True,
                     'target_range_us': [400000, 1400000],
                     'dimensions': {'width': 1080, 'height': 1920}}
        self.clip = {'scale': {'x': 1., 'y': 1.}, 'rotation': 0.,
                     'transform': {'x': 0., 'y': -.05}, 'alpha': 1.,
                     'flip': {'horizontal': False, 'vertical': False}}
        self.tracks = [{'segments': [{'material_id': 'v', 'clip': self.clip,
            'target_timerange': {'start': 0, 'duration': 2000000},
            'common_keyframes': [], 'keyframe_refs': [], 'extra_material_refs': []}]}]
        self.materials = {'v': {'width': 1080, 'height': 1920,
                              'crop': {'upper_left_x': .1}}}

    def test_freeze_inherits_video_geometry_without_modifying_base(self):
        before = copy.deepcopy(self.tracks)
        result = overlay.freeze_overlay_geometry(self.item, self.tracks, self.materials)
        self.assertEqual(result['clip'], self.clip)
        self.assertEqual(result['crop'], self.materials['v']['crop'])
        result['clip']['scale']['x'] = 2
        self.assertEqual(self.tracks, before)

    def test_freeze_cannot_cross_cut_or_use_different_dimensions(self):
        for key, value in [('target_range_us', [1900000, 2200000]),
                           ('dimensions', {'width': 941, 'height': 1672})]:
            with self.subTest(key=key):
                item = {**self.item, key: value}
                with self.assertRaisesRegex(ValueError, 'FREEZE_'):
                    overlay.freeze_overlay_geometry(item, self.tracks, self.materials)

    def test_freeze_rejects_animated_base_and_nonimage(self):
        self.tracks[0]['segments'][0]['common_keyframes'] = [{'id': 'zoom'}]
        with self.assertRaisesRegex(ValueError, 'FREEZE_'):
            overlay.freeze_overlay_geometry(self.item, self.tracks, self.materials)
        self.tracks[0]['segments'][0]['common_keyframes'] = []
        with self.assertRaisesRegex(ValueError, 'FREEZE_'):
            overlay.freeze_overlay_geometry({**self.item, 'media_kind': 'audio'}, self.tracks, self.materials)

    def test_ordinary_overlay_keeps_existing_behavior(self):
        self.assertIsNone(overlay.freeze_overlay_geometry({}, [], {}))

    def test_typeless_color_map_preserves_validation_and_rejects_missing_ref(self):
        colors = {'id': 'empty-color', 'is_color_clip': False, 'is_gradient': False}
        mapped = overlay.freeze_material_map({'videos': [{'id': 'v', 'type': 'video', **self.materials['v']}],
                                             'material_colors': [colors]})
        self.tracks[0]['segments'][0]['extra_material_refs'] = ['empty-color']
        self.assertEqual(overlay.freeze_overlay_geometry(self.item, self.tracks, mapped)['clip'], self.clip)
        mapped.pop('empty-color')
        with self.assertRaisesRegex(ValueError, 'FREEZE_ANIMATED'):
            overlay.freeze_overlay_geometry(self.item, self.tracks, mapped)

    def test_static_refs_allowed_but_nested_or_unknown_refs_rejected(self):
        segment = self.tracks[0]['segments'][0]
        static_refs = [
            {'type': 'speed', 'speed': 1.0, 'curve_speed': None},
            {'type': 'canvas_color', 'color': '', 'blur': 0.0, 'image': ''},
            {'type': 'placeholder_info', 'meta_type': 'none', 'res_path': ''},
            {'type': 'vocal_separation', 'choice': 0},
            {'type': 'none', 'audio_channel_mapping': 0},
            {'is_color_clip': False, 'is_gradient': False, 'solid_color': ''},
        ]
        for index, ref in enumerate(static_refs):
            self.materials[str(index)] = ref
        segment['extra_material_refs'] = [str(i) for i in range(len(static_refs))]
        self.assertEqual(overlay.freeze_overlay_geometry(self.item, self.tracks, self.materials)['clip'], self.clip)
        for ref in [{'type': 'combination', 'combination_type': 'none', 'draft': {'tracks': []}},
                    {'type': 'speed', 'speed': 2.0}, {'type': 'animation'},
                    {'type': 'canvas_color', 'color': '#fff'}, {}]:
            with self.subTest(ref=ref):
                self.materials['bad'] = ref
                segment['extra_material_refs'] = ['bad']
                with self.assertRaisesRegex(ValueError, 'FREEZE_ANIMATED'):
                    overlay.freeze_overlay_geometry(self.item, self.tracks, self.materials)


if __name__ == '__main__':
    unittest.main()
