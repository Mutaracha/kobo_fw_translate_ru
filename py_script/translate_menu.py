"""Interactive front end for the repository's translation tools."""
from datetime import datetime
import filecmp
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET
import struct

from catalog_review import write_untranslated
from check_lengths import length_report, messages
from qm2ts import write_ts

SCRIPTS = Path(__file__).resolve().parent


def run(script, *args):
    subprocess.run([sys.executable, SCRIPTS / script, *args], check=True)


def read_answer(prompt):
    answer = input(prompt).strip()
    print(flush=True)  # Separate the echoed answer from the next console output.
    return answer


def allow_write(path):
    return not path.exists() or read_answer(f'Перезаписать {path}? [y/N] ').lower() == 'y'


def reference_matches(untagged, reference_ts):
    reference = messages(reference_ts)
    matches = []
    for qm, trial in untagged:
        candidate = messages(trial)
        common = reference.keys() & candidate.keys()
        equal = [key for key in common if candidate[key] == reference[key]]
        # Names, placeholders and untranslated source strings alone are not
        # evidence of English. Require actual singular/plural renderings too.
        plurals = sum(len(set(reference[key])) > 1 for key in equal)
        print(f'{qm.name}: совпало с образцом {len(equal)}/{len(common)}, '
              f'в том числе с разными формами числа: {plurals}')
        if len(common) >= 50 and len(equal) >= 0.90 * len(common) and plurals >= 3:
            matches.append((qm, trial))
    return matches


def report_identical(catalog, reference):
    print('\n=== Новый перевод не требуется ===')
    print(f'Английские QM идентичны:\n  {catalog}\n  {reference}')


def select_english(src, en):
    candidates = sorted(p for p in src.glob('nickel_*.qm')
                        if p.is_file() and re.fullmatch(r'nickel_[0-9a-fA-F]+\.qm', p.name))
    if not candidates and not en.is_file():
        raise ValueError(f'В {src} нет извлечённых nickel_*.qm. Сначала выполните пункт 1.')
    refs = [d / 'trans_en.qm' for d in version_folders(src.parent, 'trans_en.qm') if d != src]
    reference = None
    if refs:
        reference = choose_folder(refs, 'Английский QM прежней прошивки для сверки:')
        if reference is None:
            return
    if not candidates:
        if not en.with_suffix('.ts').is_file():
            write_ts(en, en, en.with_suffix('.ts'), 'en')
        print(f'Английский каталог уже выбран: {en}')
        if reference and filecmp.cmp(en, reference, shallow=False):
            report_identical(en, reference)
        return

    ts = en.with_suffix('.ts')
    with TemporaryDirectory(dir=src) as tmp:
        matches = []
        untagged = []
        identical = [p for p in candidates if reference and filecmp.cmp(p, reference, shallow=False)]
        if len(identical) == 1:
            qm = identical[0]
            trial = Path(tmp) / 'selected.ts'
            write_ts(qm, qm, trial, 'en')
            matches.append((qm, trial))
        elif identical:
            raise ValueError(f'Подходящих английских каталогов: {len(identical)}. Файлы QM сохранены.')
        else:
            for qm in candidates:
                trial = Path(tmp) / qm.with_suffix('.ts').name
                try:
                    write_ts(qm, qm, trial)  # Use the QM language, not the intended target language.
                    language = ET.parse(trial).getroot().get('language')
                except (ValueError, IndexError, KeyError, struct.error, ET.ParseError) as exc:
                    raise ValueError(f'Не удалось преобразовать {qm.name}. Исходные QM сохранены.') from exc
                print(f'{qm.name}: {language or "язык не указан"}')
                if language == 'en':
                    matches.append((qm, trial))
                elif not language:
                    untagged.append((qm, trial))
            if not matches and untagged and reference:
                reference_ts = Path(tmp) / "reference.ts"
                write_ts(reference, reference, reference_ts, "en")
                matches = reference_matches(untagged, reference_ts)
                if len(matches) == 1:
                    qm, trial = matches[0]
                    print(f'{qm.name}: английский определён по переводам из образца.')
                    write_ts(qm, qm, trial, 'en')
        if len(matches) != 1:
            raise ValueError(f'Подходящих английских каталогов: {len(matches)} (нужен один). '
                             'Файлы QM сохранены. Язык не определяется по имени или порядку.')
        if not allow_write(en) or not allow_write(ts):
            return
        qm, trial = matches[0]
        staged = Path(tmp) / en.name
        shutil.copyfile(qm, staged)
        staged.replace(en)
        trial.replace(ts)
    for qm in candidates:
        qm.unlink()
    # Earlier versions of step 1 also published the extracted binary here.
    old_nickel = src / 'nickel'
    if old_nickel.is_file():
        old_nickel.unlink()
    print(f'Сохранены {en} и {ts}.')
    if identical:
        report_identical(identical[0], reference)


def version_folders(root, required_file=None):
    folders = (path for path in root.glob('*') if path.is_dir()
               and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', path.name)
               and (required_file is None or (path / required_file).is_file()))
    return sorted(folders, key=lambda path: tuple(map(int, path.name.split('.'))), reverse=True)


def choose_folder(folders, title, allow_blank=False):
    print(title)
    for number, folder in enumerate(folders, 1):
        version_dir = folder if folder.is_dir() else folder.parent
        modified = datetime.fromtimestamp(version_dir.stat().st_mtime)
        print(f'{number}. {folder}    Папка изменена: {modified:%d.%m.%Y %H:%M}')
    if allow_blank:
        print('Enter — начать без прежнего перевода.')
    while True:
        answer = read_answer('Номер в списке (0 — назад): ')
        if answer == '0':
            return None
        if not answer and allow_blank:
            return ''
        if answer.isascii() and answer.isdecimal() and 1 <= int(answer) <= len(folders):
            return folders[int(answer) - 1]
        print(f'Введите число от 0 до {len(folders)}.')


def english_ts(version):
    return Path('src') / version / 'trans_en.ts'


def action(choice):
    if choice == '1':
        archive = read_answer('Путь к ZIP (Enter — найти автоматически): ').strip('"')
        run('bin2qm.py', *([archive] if archive else []))
        return

    if choice in ('2', '3'):
        folders = version_folders(Path('src'))
        if not folders:
            raise ValueError('В src нет исходников в папках версий. Сначала выполните пункт 1.')
        title = 'Исходники прошивок:'
    else:
        folders = version_folders(Path('translated'), 'trans_ru.ts')
        if choice == '5':
            folders = [d for d in folders if english_ts(d.name).is_file()]
        if not folders:
            raise ValueError('Нет версий с нужными TS для этого пункта.')
        title = 'Версия перевода:'
    folder = choose_folder(folders, title)
    if folder is None:
        return
    version = folder.name
    src = Path('src') / version
    en = src / 'trans_en.qm'
    reports = Path('reports') / version
    ru = Path('translated') / version / 'trans_ru.ts'
    if choice == '2':
        select_english(src, en)
    elif choice == '3':
        if not en.is_file():
            raise ValueError('Сначала выберите английский каталог в пункте 2.')
        folders = version_folders(Path('translated'), 'trans_ru.qm')
        if not folders:
            print('В translated нет папок с trans_ru.qm.')
        folder = choose_folder(folders, 'Папка прежнего перевода:', allow_blank=True)
        if folder is None:
            return
        prev = folder / 'trans_ru.qm' if folder else '-'
        if allow_write(ru):
            ru.parent.mkdir(parents=True, exist_ok=True)
            run('qm2ts.py', prev, en, ru, 'ru_RU')
            write_untranslated(ru, reports / 'untranslated.txt')
            print(f'Отредактируйте {ru}, затем соберите QM в пункте 4.')
    elif choice == '4' and allow_write(ru.with_suffix('.qm')):
        run('ts2qm.py', ru, ru.with_suffix('.qm'))
        print('После проверки отправьте trans_ru.ts и trans_ru.qm в Git. Патч соберёт Actions.')
    elif choice == '5':
        lines = list(length_report(english_ts(version), ru))
        reports.mkdir(parents=True, exist_ok=True)
        report = reports / 'lengths.txt'
        report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f'{lines[-1]}\nОтчёт: {report}')


def main():
    while True:
        print('\n1. Извлечь nickel и .qm из прошивки\n2. Автоматически найти английский .qm → .ts'
              '\n3. Подготовить русский .ts\n4. Собрать trans_ru.qm\n5. Диагностика длин EN/RU (необязательно)\n0. Выход')
        try:
            choice = read_answer('> ')
            if choice == '0':
                return
            if choice in {'1', '2', '3', '4', '5'}:
                action(choice)
        except (EOFError, KeyboardInterrupt):
            return
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            print(f'Ошибка: {exc}', file=sys.stderr)


if __name__ == '__main__':
    main()
