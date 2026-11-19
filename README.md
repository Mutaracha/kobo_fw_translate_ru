# Русификация Kobo

Готовый перевод для прошивки **4.38.23852** устанавливается как патч `KoboRoot.tgz`.

## Локальная сборка патча

Для локальной сборки на Linux (GNU tar и coreutils) из корня репозитория:

```sh
./scripts/build_patch.sh translated/4.38.23852/trans_ru.qm KoboRoot.tgz
tar -tzf KoboRoot.tgz
```

## Состав патча

- `usr/local/Kobo/translations/trans_ru.qm` — перевод выбранной версии.
- `usr/local/Trolltech/QtEmbedded-4.6.2-arm/lib/fonts/` — восемь файлов Avenir и Georgia из исходного патча 4.38.23852. Для сборки они хранятся в `patch/fonts/`.

## Файлы репозитория

- `src/trans_en_4.38.23852.qm` — английский исходник, извлечённый из `usr/local/Kobo/nickel` прошивки 4.38.23852.
- `translated/<версия>/` — переведённые строки (`trans_ru.ts`, `trans_ru.qm`); в `translated/4.38.23852/` также находится готовый патч `KoboRoot.tgz`.
- `py_script/` — инструменты на Python 3, не требующие Qt:
  - `ts2qm.py` — компиляция `.ts` → `.qm`;
  - `qm2ts.py` — преобразование `.qm` → `.ts` с полным списком строк прошивки;
  - `qmtool.py` — поиск и разбор `.qm` внутри `nickel` (`python3 py_script/qmtool.py find <папка> nickel`);
  - `qmwrite.py` — запись `.qm` в формате `lrelease`.

## Сверка перевода 4.38.23852

[Английский каталог в формате Qt Linguist](src/trans_en_4.38.23852.ts) можно читать и сравнивать с русским `.ts`, не устанавливая Qt. Чтобы повторить выгрузку, передайте английский `.qm` как каталог перевода и как список ключей:

```sh
python3 py_script/qm2ts.py src/trans_en_4.38.23852.qm src/trans_en_4.38.23852.qm src/trans_en_4.38.23852.ts en
```

[Результаты редактуры и проверки перевода](translated/4.38.23852/review.md).
