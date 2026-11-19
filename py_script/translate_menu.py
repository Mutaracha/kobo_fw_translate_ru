"""Interactive front end for the repository's translation tools."""
from pathlib import Path
import re
import shutil
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parent


def run(script, *args):
    subprocess.run([sys.executable, SCRIPTS / script, *args], check=True)


def path_input(prompt):
    return input(prompt).strip().strip('"')


def allow_write(path):
    return not path.exists() or input(f'Перезаписать {path}? [y/N] ').strip().lower() == 'y'


def action(choice):
    if choice == '1':
        archive = path_input('Путь к ZIP (Enter — найти автоматически): ')
        run('bin2qm.py', *([archive] if archive else []))
        return

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
        for candidate in sorted(src.glob('nickel_*.qm')):
            print(candidate)
        selected = path_input(f'Путь к английскому .qm (Enter — {en}): ')
        selected = Path(selected) if selected else en
        run('qmtool.py', 'qm', selected)
        if input('Это английский каталог? [y/N] ').strip().lower() != 'y':
            return
        if not allow_write(en.with_suffix('.ts')):
            return
        if selected.resolve() != en.resolve():
            if not allow_write(en):
                return
            en.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(selected, en)
        run('qm2ts.py', en, en, en.with_suffix('.ts'), 'en')
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
        print('\n1. Извлечь nickel и .qm из прошивки\n2. Выбрать английский .qm → .ts'
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
