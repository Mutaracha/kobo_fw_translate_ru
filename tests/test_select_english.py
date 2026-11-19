"""Exercise menu step 2 with offset-named catalogs, as produced by step 1."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1] / 'py_script'
sys.path.insert(0, str(SCRIPTS))
from qmtool import parse_qm
from qmwrite import write_qm


class EnglishSelectionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cwd = Path(tmp.name)
        self.src = self.cwd / 'src/4.38.23828'
        self.src.mkdir(parents=True)
        self.en = self.src / 'trans_en_4.38.23828.qm'

    def candidate(self, name, language):
        path = self.src / name
        write_qm(path, [{'ctx': 'Home', 'src': 'Done', 'cmt': '', 'tr': ['Done']}], language, b'')
        return path

    def step2(self):
        run = subprocess.run([sys.executable, SCRIPTS / 'translate_menu.py'], cwd=self.cwd,
                             input='2\n4.38.23828\n0\n', capture_output=True, text=True, check=True)
        self.assertNotIn('Traceback', run.stderr)
        return run.stderr

    def test_select_by_language_and_clean_generated_files(self):
        original = self.candidate('nickel_14f49f8.qm', b'en').read_bytes()
        self.candidate('nickel_15b7878.qm', b'fr')
        (self.src / 'nickel').touch()  # from an earlier extractor
        (self.src / 'notes.txt').touch()
        self.assertEqual(self.step2(), '')
        self.assertEqual(self.en.read_bytes(), original)
        ts = self.en.with_suffix('.ts')
        self.assertEqual(ET.parse(ts).getroot().get('language'), 'en')
        self.assertEqual(set(self.src.iterdir()), {self.en, ts, self.src / 'notes.txt'})
        self.assertEqual(self.step2(), '')  # no offset-named files on rerun

    def test_unknown_or_ambiguous_language_keeps_inputs(self):
        self.candidate('nickel_1.qm', b'')
        self.candidate('nickel_2.qm', b'de')
        for n in (0, 2):
            if n:
                self.candidate('nickel_1.qm', b'en')
                self.candidate('nickel_2.qm', b'en')
            self.assertIn(f'английских каталогов: {n}', self.step2())
            self.assertEqual(sorted(p.name for p in self.src.iterdir()), ['nickel_1.qm', 'nickel_2.qm'])

    def test_untagged_firmware_matches_reference_across_versions(self):
        sample = SCRIPTS.parent / 'src/trans_en_4.38.23852.qm'
        lang, rows = parse_qm(sample)
        self.assertIsNone(lang)
        # Simulate a nearby firmware: most keys overlap, but not all.
        rows = [m for m in rows[15:] if all(m['tr'])]
        rows[0]['tr'] = ['New English wording']
        source = self.src / 'nickel_1971124.qm'
        write_qm(source, rows, b'', b'')
        original = source.read_bytes()
        # Same English source keys do not make this translation English.
        for m in rows:
            m['tr'] = ['Fremdsprache'] * len(m['tr'])
        write_qm(self.src / 'nickel_1.qm', rows, b'', b'')
        self.assertEqual(self.step2(), '')
        self.assertEqual(self.en.read_bytes(), original)
        root = ET.parse(self.en.with_suffix('.ts')).getroot()
        self.assertEqual(root.get('language'), 'en')
        self.assertTrue(any(tr.text == 'New English wording' for tr in root.iter('translation')))
        self.assertFalse(list(self.src.glob('nickel_*.qm')))

    def test_two_untagged_reference_matches_preserve_inputs(self):
        sample = (SCRIPTS.parent / 'src/trans_en_4.38.23852.qm').read_bytes()
        for name in ('nickel_1.qm', 'nickel_2.qm'):
            (self.src / name).write_bytes(sample)
        self.assertIn('английских каталогов: 2', self.step2())
        self.assertFalse(self.en.exists())
        self.assertEqual(len(list(self.src.glob('nickel_*.qm'))), 2)

    def test_missing_inputs_have_actionable_error(self):
        self.assertIn('Сначала выполните пункт 1', self.step2())
