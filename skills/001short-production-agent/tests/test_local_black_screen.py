from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_episode_capcut as builder
import track_template_matrix as matrix


class LocalBlackScreenTest(unittest.TestCase):
    def test_black_has_its_own_asset_while_white_is_unchanged(self):
        self.assertEqual(matrix.track_template_profile(matrix.FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE).pinned_assets['SCREEN_WHITE'], 'black_frame_local_1080x1920.png')
        for name in (matrix.V2_TEMPLATE_PROFILE, matrix.V3_TEMPLATE_PROFILE, matrix.BLACK_TOP_TEMPLATE_PROFILE):
            self.assertEqual(matrix.track_template_profile(name).pinned_assets['SCREEN_WHITE'], 'transparent_center_white_1080x1920.png')

    def test_v3_black_archive_extracts_without_white_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            archive=root/'black.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('root/draft_content.json','{}')
                z.writestr('root/draft_meta_info.json','{}')
                z.writestr('root/Resources/media/black_frame_local_1080x1920.png',b'black-pixels')
            extracted=builder._extract_template(archive,root/'out',matrix.FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE)
            self.assertTrue((extracted/'Resources/media/black_frame_local_1080x1920.png').is_file())
            self.assertFalse((extracted/'Resources/media/transparent_center_white_1080x1920.png').exists())

    def test_local_binding_removes_online_identity_and_preserves_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            media=Path(tmp)
            (media/'black_frame_local_1080x1920.png').write_bytes(b'black')
            material={'id':'screen-uuid','type':'photo','material_id':'7655295384293543169',
                      'source_platform':9,'source':0,'team_id':'old-team','category_id':'pc_brand_pic',
                      'category_name':'online','material_name':'old.png','media_path':'cached.png',
                      'path':'C:/Cache/onlineMaterial/white.png','material_url':'old',
                      'width':1080,'height':1920,'crop':{'upper_left_x':0.0},'check_flag':62978047}
            geometry=copy.deepcopy(material['crop'])
            builder._bind_pinned_screen_material(material,media,'PREFIX/',matrix.track_template_profile(matrix.FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE))
            self.assertEqual(material['id'],'screen-uuid')
            self.assertEqual(material['crop'],geometry)
            self.assertEqual(material['source_platform'],0)
            for field in ('material_id','team_id','category_id','category_name','material_url','media_path'):
                self.assertEqual(material[field],'')
            self.assertEqual(material['material_name'],'black_frame_local_1080x1920.png')
            self.assertTrue(material['path'].endswith('/Resources/media/black_frame_local_1080x1920.png'))
            self.assertNotIn('onlineMaterial',json.dumps(material))

    def test_missing_black_never_falls_back_to_white(self):
        with tempfile.TemporaryDirectory() as tmp:
            media=Path(tmp);(media/'transparent_center_white_1080x1920.png').write_bytes(b'white')
            material={'id':'screen'}
            with self.assertRaisesRegex(RuntimeError,'PINNED_SCREEN_ASSET_MISSING'):
                builder._bind_pinned_screen_material(material,media,'PREFIX',matrix.track_template_profile(matrix.FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE))
            self.assertEqual(material,{'id':'screen'})

if __name__=='__main__':unittest.main()
