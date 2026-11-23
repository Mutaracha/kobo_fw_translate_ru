import gzip
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LocalPatchBuildTests(unittest.TestCase):
    def test_builder_packages_translation_dictionary_and_all_fonts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'KoboRoot.tgz'
            subprocess.run([sys.executable, ROOT / 'scripts/build_patch.py',
                            ROOT / 'translated/4.38.23852/trans_ru.qm', output], check=True)
            with tarfile.open(output, 'r:gz') as archive:
                names = archive.getnames()
                self.assertEqual(len(names), 10)
                self.assertIn('./usr/local/Kobo/translations/trans_ru.qm', names)
                self.assertIn('./usr/local/Kobo/hyphenDicts/hyph_ru.dic', names)
                self.assertEqual(sum('/fonts/' in n for n in names), 8)
                self.assertTrue(all(m.uid == 0 and m.gid == 0 and m.mode == 0o644 for m in archive.getmembers()))


if __name__ == '__main__':
    unittest.main()
