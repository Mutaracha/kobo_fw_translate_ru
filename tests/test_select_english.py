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
        self.en = self.src / 'trans_en.qm'

    def reference(self, version, data):
        folder = self.src.parent / version
        folder.mkdir()
        (folder / 'trans_en.qm').write_bytes(data)

    def candidate(self, name, language):
        path = self.src / name
        write_qm(path, [{'ctx': 'Home', 'src': 'Done', 'cmt': '', 'tr': ['Done']}], language, b'')
        return path

    def step2(self, selection="1"):
        run = subprocess.run([sys.executable, SCRIPTS / 'translate_menu.py'], cwd=self.cwd,
                             input=f'2\n{selection}\n0\n', capture_output=True, text=True, check=True)
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
        sample = SCRIPTS.parent / 'src/4.38.23852/trans_en.qm'
        self.reference('4.38.23852', sample.read_bytes())
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
        self.assertEqual(self.step2('2\n1'), '')
        self.assertEqual(self.en.read_bytes(), original)
        root = ET.parse(self.en.with_suffix('.ts')).getroot()
        self.assertEqual(root.get('language'), 'en')
        self.assertTrue(any(tr.text == 'New English wording' for tr in root.iter('translation')))
        self.assertFalse(list(self.src.glob('nickel_*.qm')))

    def test_two_untagged_reference_matches_preserve_inputs(self):
        sample = (SCRIPTS.parent / 'src/4.38.23852/trans_en.qm').read_bytes()
        self.reference('4.38.23852', sample)
        for name in ('nickel_1.qm', 'nickel_2.qm'):
            (self.src / name).write_bytes(sample)
        self.assertIn('английских каталогов: 2', self.step2('2\n1'))
        self.assertFalse(self.en.exists())
        self.assertEqual(len(list(self.src.glob('nickel_*.qm'))), 2)

    def test_pick_second_version_after_invalid_choice(self):
        other = self.src.parent / '4.100.1'
        other.mkdir()
        (self.src.parent / 'notes').mkdir()
        original = self.candidate('nickel_1.qm', b'en').read_bytes()
        (other / 'nickel_1.qm').write_bytes(original)
        self.assertEqual(self.step2('3\n2'), '')
        self.assertEqual(self.en.read_bytes(), original)
        self.assertEqual(list(other.iterdir()), [other / 'nickel_1.qm'])

    def test_cancel_or_no_folders(self):
        candidate = self.candidate('nickel_1.qm', b'en')
        self.assertEqual(self.step2('0'), '')
        self.assertTrue(candidate.is_file())
        candidate.unlink()
        self.src.rmdir()
        (self.src.parent / 'trans_en_4.38.23852.qm').touch()  # not a folder
        self.assertIn('В src нет исходников', self.step2('0'))

    def test_step3_selects_source_and_previous_translation_folders(self):
        self.candidate('nickel_1.qm', b'en').rename(self.en)
        (self.src.parent / 'trans_en_9.9.9.qm').touch()
        previous = self.cwd / 'translated/4.37.1'
        previous.mkdir(parents=True)
        (previous.parent / '9.9.9').mkdir()  # not selectable without trans_ru.qm
        write_qm(previous / 'trans_ru.qm', [{'ctx': 'Home', 'src': 'Done', 'cmt': '',
                                              'tr': ['Готово']}], b'ru_RU', b'')
        target = previous.parent / self.src.name / 'trans_ru.ts'
        for selection, expected in [('0', None), ('2\n1', 'Готово'), ('', '')]:
            run = subprocess.run([sys.executable, SCRIPTS / 'translate_menu.py'], cwd=self.cwd,
                                 input=f'3\n1\n{selection}\n0\n', capture_output=True, text=True, check=True)
            self.assertEqual(run.stderr, '')
            self.assertNotIn('9.9.9', run.stdout)
            if expected is None:
                self.assertFalse(target.exists())
            else:
                self.assertEqual(ET.parse(target).findtext('.//translation'), expected)
                target.unlink()

    def test_selected_reference_exact_match_skips_other_candidates(self):
        original = self.candidate('nickel_a.qm', b'').read_bytes()
        (self.src / 'nickel_b.qm').write_bytes(b'not a catalog')
        self.reference('1.0.0', original)
        self.reference('2.0.0', b'other reference')
        run = subprocess.run([sys.executable, SCRIPTS / 'translate_menu.py'], cwd=self.cwd,
                             input='2\n1\n2\n0\n', capture_output=True, text=True, check=True)
        self.assertEqual(run.stderr, '')
        self.assertIn('Новый перевод не требуется', run.stdout)
        self.assertEqual(self.en.read_bytes(), original)

    def test_preparation_compilation_and_reports(self):
        license_source = '<h1><span>Attributions</span></h1><p>License text</p>'
        rows = [dict(ctx='AchievementText', src='Pressed for Details', cmt='', tr=['Pressed for Details']),
                dict(ctx='Home', src='Done', cmt='', tr=['Done']),
                dict(ctx='N3SettingsDeviceInformationController', src=license_source, cmt='', tr=[license_source])]
        write_qm(self.en, rows, b'en', b'')
        subprocess.run([sys.executable, SCRIPTS / 'qm2ts.py', self.en, self.en, self.en.with_suffix('.ts'), 'en'],
                       capture_output=True, check=True)
        previous = self.cwd / 'translated/4.1.1'
        previous.mkdir(parents=True)
        rows[0]['tr'] = ['Подробности']
        rows[2]['tr'] = ['Лицензия']
        write_qm(previous / 'trans_ru.qm', [rows[0], rows[2]], b'ru_RU', b'')
        run = subprocess.run([sys.executable, SCRIPTS / 'translate_menu.py'], cwd=self.cwd,
                             input='3\n1\n1\n4\n1\n5\n1\n0\n', capture_output=True, text=True, check=True)
        self.assertEqual(run.stderr, '')
        reports = self.cwd / 'reports' / self.src.name
        missing = (reports / 'untranslated.txt').read_text(encoding='utf-8')
        self.assertIn('Home | Done', missing)
        self.assertNotIn('Attributions', missing)
        lengths = (reports / 'lengths.txt').read_text(encoding='utf-8')
        self.assertIn('EN 19 → RU 11 | AchievementText [1]: Pressed for Details → Подробности', lengths)
        self.assertNotIn('Attributions', lengths)
        self.assertEqual([m['src'] for m in parse_qm(previous.parent / self.src.name / 'trans_ru.qm')[1]],
                         ['Pressed for Details'])

    def test_missing_inputs_have_actionable_error(self):
        self.assertIn('Сначала выполните пункт 1', self.step2())
