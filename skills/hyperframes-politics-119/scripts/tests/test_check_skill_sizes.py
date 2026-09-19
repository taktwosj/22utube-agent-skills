import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "check_skill_sizes.py"
spec = importlib.util.spec_from_file_location("size_audit", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SizeAuditTests(unittest.TestCase):
    def test_thresholds_nested_paths_and_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            files = {"SKILL.md": b"x" * 8192,
                     "references/nested/detail.md": "가".encode() * 2049,
                     "scripts/hf119/core.py": b"x" * 15361,
                     "scripts/tests/test_large.py": b"x" * 20000,
                     "references/old.md.bak": b"x" * 20000}
            for name, data in files.items():
                path = root / "sample" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            result = module.audit(root, ["sample"])
            rows = {r['file']: r for r in result['files']}
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows['sample/SKILL.md']['status'], 'PASS')
            self.assertEqual(rows['sample/references/nested/detail.md']['bytes'], 6147)
            self.assertEqual(rows['sample/scripts/hf119/core.py']['status'], 'WARN')
            p = subprocess.run([sys.executable, '-B', str(SCRIPT), '--skills-root', str(root),
                                '--skills', 'sample', '--json'], capture_output=True)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(json.loads(p.stdout)['status'], 'WARN')
            self.assertEqual({name: (root/'sample'/name).read_bytes() for name in files}, files)

    def test_missing_skill_is_input_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = subprocess.run([sys.executable, '-B', str(SCRIPT), '--skills-root', tmp,
                                '--skills', 'missing'], capture_output=True)
            self.assertEqual(p.returncode, 2)


if __name__ == '__main__':
    unittest.main()
