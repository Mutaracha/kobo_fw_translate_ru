Русификация Kobo, прошивка 4.38.23852

Source/      trans_en_4.38.23852.qm - английский исходник, извлечённый из usr/local/Kobo/nickel прошивки 4.38.23852
Translated/  trans_ru.ts - перевод (редактировать в Qt Linguist), trans_ru.qm - скомпилированный
             changes.txt - полный список изменений относительно перевода ery14 от 05.12.25
Soft/        скрипты на Python 3, Qt не нужен:
             ts2qm.py   - компиляция:  python ts2qm.py trans_ru.ts trans_ru.qm
             qm2ts.py   - .qm -> .ts с полным списком строк прошивки
             qmtool.py  - поиск .qm внутри nickel и разбор .qm:  python qmtool.py find <папка> nickel
             qmwrite.py - запись .qm (формат lrelease)
             Qt Linguist для правки .ts есть в посте isvmcc.

Готовый trans_ru.qm кладётся в KoboRoot.tgz по пути usr/local/Kobo/translations/trans_ru.qm.
