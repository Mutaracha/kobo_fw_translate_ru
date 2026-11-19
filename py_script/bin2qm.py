"""Extract nickel and its Qt translation catalogs from a Kobo firmware ZIP."""
import argparse
import re
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from tempfile import TemporaryDirectory
import zipfile

from qmtool import find_qms


def firmware_input():
    archives = sorted(p for p in Path.cwd().glob('kobo-update*.zip') if p.is_file())
    if len(archives) > 1:
        raise ValueError('Найдено несколько архивов. Укажите один явно: ' + ', '.join(p.name for p in archives))
    if archives:
        return archives[0]
    if Path('nickel').is_file():
        return Path('nickel')
    raise ValueError('В текущей папке нет kobo-update*.zip или nickel.')


def default_output(source):
    if source.suffix.lower() != '.zip':
        return Path('extracted-qm')  # A standalone nickel has no firmware version.
    match = re.match(r'kobo-update-([0-9]+\.[0-9]+\.[0-9]+)(?![0-9.])', source.stem, re.I)
    if not match:
        raise ValueError('В имени ZIP нет версии kobo-update-X.Y.Z. Укажите папку с -o.')
    return Path('src') / match[1]


def extract_nickel(archive, dest):
    with zipfile.ZipFile(archive) as update:
        roots = [m for m in update.infolist() if not m.is_dir() and PurePosixPath(m.filename).name == 'KoboRoot.tgz']
        if len(roots) != 1:
            raise ValueError('В ZIP должен быть ровно один KoboRoot.tgz.')
        with update.open(roots[0]) as gz, tarfile.open(fileobj=gz, mode='r|gz') as root:
            for m in root:
                if PurePosixPath(m.name) == PurePosixPath('usr/local/Kobo/nickel'):
                    if not m.isfile():
                        raise ValueError('nickel в архиве не является обычным файлом.')
                    with root.extractfile(m) as src, dest.open('wb') as out:
                        shutil.copyfileobj(src, out)
                    return
    raise ValueError('В KoboRoot.tgz нет usr/local/Kobo/nickel.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, nargs='?', help='архив прошивки ZIP или файл nickel')
    parser.add_argument('-o', '--output', type=Path, help='новая папка для результатов')
    args = parser.parse_args()
    try:
        source = args.input or firmware_input()
        args.output = args.output or default_output(source)
        if args.output.exists():
            raise ValueError(f'{args.output} уже существует. Выберите новую папку с -o.')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=args.output.parent) as tmp:
            stage = Path(tmp) / 'result'
            stage.mkdir()
            nickel = Path(tmp) / 'nickel'
            if source.suffix.lower() == '.zip':
                extract_nickel(source, nickel)
            else:
                shutil.copyfile(source, nickel)
            files, _ = find_qms(nickel, stage)
            if not files:
                raise ValueError('В nickel не найдены каталоги QM.')
            stage.rename(args.output)
        print(f'{source.name}: извлечено каталогов QM: {len(files)}. Результат: {args.output}')
    except (ValueError, OSError, EOFError, tarfile.TarError, zipfile.BadZipFile, RuntimeError) as error:
        parser.exit(1, f'{parser.prog}: {error}\n')


if __name__ == '__main__':
    main()
