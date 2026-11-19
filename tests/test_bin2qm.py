"""Exercise the firmware ZIP → KoboRoot.tgz → nickel → QM workflow offline."""
import io
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'py_script' / 'bin2qm.py'
QM = (ROOT / 'src' / 'trans_en_4.38.23852.qm').read_bytes()


class FirmwareTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cwd = Path(tmp.name)
        self.zip = self.cwd / 'kobo-update-4.38.23697 aura.zip'

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.cwd,
                              capture_output=True, text=True)

    def archive(self, data, member='./usr/local/Kobo/nickel'):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w:gz') as root:
            entry = tarfile.TarInfo(member)
            entry.size = len(data)
            root.addfile(entry, io.BytesIO(data))
        with zipfile.ZipFile(self.zip, 'w') as update:
            update.writestr('KoboRoot.tgz', buf.getvalue())

    def test_auto_archive(self):
        nickel = b'prefix' + QM + struct.pack('>I', len(QM)) + zlib.compress(QM) + b'tail'
        self.archive(nickel)
        (self.cwd / 'nickel').write_bytes(b'ignored when ZIP present')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.cwd / 'src/4.38.23697'
        self.assertFalse((out / 'nickel').exists())
        self.assertEqual([f.read_bytes() for f in out.glob('*.qm')], [QM, QM])
        self.assertNotEqual(self.run_cli().returncode, 0)  # no overwrite

    def test_no_zip_uses_nickel(self):
        (self.cwd / 'nickel').write_bytes(zlib.compress(QM))
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual((self.cwd / 'extracted-qm/nickel_0.qm').read_bytes(), QM)

    def test_errors_do_not_publish_partial_output(self):
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.archive(QM, 'wrong/nickel')
        (self.cwd / 'kobo-update-other.zip').touch()
        self.assertIn('несколько', self.run_cli().stderr)
        self.assertIn('нет usr/local/Kobo/nickel', self.run_cli(self.zip).stderr)
        self.archive(b'no translations')
        self.assertIn('не найдены каталоги QM', self.run_cli(self.zip).stderr)
        self.assertFalse((self.cwd / 'src/4.38.23697').exists())

    def test_version_and_output_override(self):
        self.archive(QM)
        archive = self.zip.rename(self.cwd / 'kobo-update-12.123.456789.zip')
        self.assertEqual(self.run_cli(archive).returncode, 0)
        self.assertFalse((self.cwd / 'src/12.123.456789/nickel').exists())
        self.assertTrue((self.cwd / 'src/12.123.456789/nickel_0.qm').is_file())
        archive = archive.rename(self.cwd / 'custom.zip')
        self.assertNotEqual(self.run_cli(archive).returncode, 0)
        self.assertEqual(self.run_cli(archive, '-o', 'custom output').returncode, 0)
        self.assertTrue((self.cwd / 'custom output/nickel_0.qm').is_file())
