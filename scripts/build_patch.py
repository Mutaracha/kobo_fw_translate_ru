#!/usr/bin/env python3
"""Build KoboRoot.tgz using only Python's standard library (Windows/Linux/macOS)."""
import argparse
import gzip
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent.parent
FONT_NAMES = ('Avenir.ttf', 'Avenir-Bold.ttf', 'Avenir-Italic.ttf',
              'Avenir-BoldItalic.ttf', 'georgia.ttf', 'georgiab.ttf',
              'georgiai.ttf', 'georgiaz.ttf')
DEVICE_FONTS = 'usr/local/Trolltech/QtEmbedded-4.6.2-arm/lib/fonts'


def build(qm, output):
    qm = Path(qm)
    if not qm.is_file():
        raise FileNotFoundError(qm)
    files = [(qm, 'usr/local/Kobo/translations/trans_ru.qm'),
             (ROOT / 'patch/hyphenDicts/hyph_ru.dic', 'usr/local/Kobo/hyphenDicts/hyph_ru.dic')]
    files += [(ROOT / 'patch/fonts' / name, f'{DEVICE_FONTS}/{name}') for name in FONT_NAMES]
    for path, _ in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for path, name in files:
                info = tarfile.TarInfo('./' + name)
                info.size = path.stat().st_size
                info.mode = 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                info.mtime = 0
                with path.open('rb') as data:
                    archive.addfile(info, data)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('qm', help='Russian trans_ru.qm file')
    parser.add_argument('output', help='destination KoboRoot.tgz')
    args = parser.parse_args()
    print(f'Created {build(args.qm, args.output)}')


if __name__ == '__main__':
    main()
