import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import fitz


SCRIPT = Path(__file__).parents[1] / "scripts" / "ingest_lecture_pdfs.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ingest_lecture_pdfs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IngestLecturePdfsTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.pdf_path = self.root / "lecture.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Digital Nomad High Class Copyright Mara")
        page.insert_text((72, 110), "First useful lecture claim")
        doc.new_page()
        doc.save(self.pdf_path)
        doc.close()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_clean_text_removes_repeated_boilerplate(self):
        module = load_module()
        cleaned = module.clean_text(
            "Digital Nomad High Class Copyright Mara\nFirst useful lecture claim"
        )
        self.assertEqual(cleaned, "First useful lecture claim")

    def test_extract_pdf_records_pages_hash_and_empty_flag(self):
        module = load_module()
        records = module.extract_pdf(self.pdf_path, "일반반 1강")
        expected_hash = hashlib.sha256(self.pdf_path.read_bytes()).hexdigest().upper()
        self.assertEqual([record["page"] for record in records], [1, 2])
        self.assertEqual(records[0]["source_sha256"], expected_hash)
        self.assertFalse(records[0]["needs_visual_review"])
        self.assertTrue(records[1]["needs_visual_review"])

    def test_render_pdf_writes_one_png_per_page(self):
        module = load_module()
        output_dir = self.root / "pages"
        rendered = module.render_pdf(self.pdf_path, output_dir, dpi=72)
        self.assertEqual(len(rendered), 2)
        self.assertTrue(all(path.exists() for path in rendered))


if __name__ == "__main__":
    unittest.main()
