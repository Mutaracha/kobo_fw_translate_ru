"""Interactive front end for the repository's translation tools."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET
import struct

from check_lengths import messages
from qm2ts import write_ts

SCRIPTS = Path(__file__).resolve().parent


def run(script, *args):
    subprocess.run([sys.executable, SCRIPTS / script, *args], check=True)


def path_input(prompt):
    return input(prompt).strip().strip('"')


def allow_write(path):
    return not path.exists() or input(f'Перезаписать {path}? [y/N] ').strip().lower() == 'y'


def reference_matches(untagged):
    reference = messages(SCRIPTS.parent / 'src' / 'trans_en_4.38.23852.ts')
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


def select_english(src, en):
    candidates = sorted(p for p in src.glob('nickel_*.qm')
                        if p.is_file() and re.fullmatch(r'nickel_[0-9a-fA-F]+\.qm', p.name))
    if not candidates:
        if not en.is_file():
            raise ValueError(f'В {src} нет извлечённых nickel_*.qm. Сначала выполните пункт 1.')
        if not en.with_suffix('.ts').is_file():
            write_ts(en, en, en.with_suffix('.ts'), 'en')
        print(f'Английский каталог уже выбран: {en}')
        return

    target = src / en.name  # Never overwrite the legacy catalog in the parent directory.
    ts = target.with_suffix('.ts')
    with TemporaryDirectory(dir=src) as tmp:
        matches = []
        untagged = []
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
        if not matches and untagged:
            matches = reference_matches(untagged)
            if len(matches) == 1:
                qm, trial = matches[0]
                print(f'{qm.name}: английский определён по переводам из образца.')
                write_ts(qm, qm, trial, 'en')
        if len(matches) != 1:
            raise ValueError(f'Подходящих английских каталогов: {len(matches)} (нужен один). '
                             'Файлы QM сохранены. Язык не определяется по имени или порядку.')
        if not allow_write(target) or not allow_write(ts):
            return
        qm, trial = matches[0]
        staged = Path(tmp) / target.name
        shutil.copyfile(qm, staged)
        staged.replace(target)
        trial.replace(ts)
    for qm in candidates:
        qm.unlink()
    # Earlier versions of step 1 also published the extracted binary here.
    old_nickel = src / 'nickel'
    if old_nickel.is_file():
        old_nickel.unlink()
    print(f'Сохранены {target} и {ts}.')


def choose_source_version():
    root = Path('src')
    pattern = r'[0-9]+\.[0-9]+\.[0-9]+'
    locations = {}
    for path in root.glob('trans_en_*.qm'):
        match = re.fullmatch(rf'trans_en_({pattern})\.qm', path.name)
        if match and path.is_file():
            locations[match[1]] = path  # Legacy flat layout.
    for path in root.glob('*'):
        if path.is_dir() and re.fullmatch(pattern, path.name):
            locations[path.name] = path
    versions = sorted(locations, key=lambda v: tuple(map(int, v.split('.'))), reverse=True)
    if not versions:
        raise ValueError('В src нет исходников прошивок. Сначала выполните пункт 1.')
    print('Исходники прошивок:')
    for number, version in enumerate(versions, 1):
        print(f'{number}. {locations[version]}')
    while True:
        answer = input('Номер в списке (0 — назад): ').strip()
        if answer == '0':
            return None
        if answer.isascii() and answer.isdecimal() and 1 <= int(answer) <= len(versions):
            return versions[int(answer) - 1]
        print(f'Введите число от 0 до {len(versions)}.')


def action(choice):
    if choice == '1':
        archive = path_input('Путь к ZIP (Enter — найти автоматически): ')
        run('bin2qm.py', *([archive] if archive else []))
        return

    if choice == '2':
        version = choose_source_version()
        if version is None:
            return
    else:
        version = input('Версия прошивки (например, 4.38.23697): ').strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError('Ожидается версия в формате X.Y.Z.')
    src = Path('src') / version
    en = src / f'trans_en_{version}.qm'
    legacy = Path('src') / en.name
    if not en.exists() and legacy.is_file():
        en = legacy
    ru = Path('translated') / version / 'trans_ru.ts'
    if choice == '2':
        select_english(src, en)
    elif choice == '3':
        if not en.is_file():
            raise ValueError('Сначала выберите английский каталог в пункте 2.')
        prev = path_input('Путь к прежнему trans_ru.qm (Enter — начать без перевода): ')
        if allow_write(ru):
            ru.parent.mkdir(parents=True, exist_ok=True)
            run('qm2ts.py', prev or '-', en, ru, 'ru_RU')
            print(f'Отредактируйте {ru}, затем выполните пункты 4 и 5.')
    elif choice == '4':
        run('check_lengths.py', en.with_suffix('.ts'), ru)
    elif choice == '5' and allow_write(ru.with_suffix('.qm')):
        run('ts2qm.py', ru, ru.with_suffix('.qm'))
        print('После проверки отправьте trans_ru.ts и trans_ru.qm в Git. Патч соберёт Actions.')


def main():
    while True:
        print('\n1. Извлечь nickel и .qm из прошивки\n2. Автоматически найти английский .qm → .ts'
              '\n3. Подготовить русский .ts\n4. Сравнить длины EN/RU\n5. Собрать trans_ru.qm\n0. Выход')
        try:
            choice = input('> ').strip()
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
