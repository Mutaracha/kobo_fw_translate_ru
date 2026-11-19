"""List EN/RU display-length outliers in two matching firmware TS catalogs."""
import argparse
import html
import re
from xml.etree import ElementTree as ET


def messages(path):
    result = {}
    for context in ET.parse(path).getroot().findall('context'):
        for m in context.findall('message'):
            key = (context.findtext('name'), m.findtext('source'), m.findtext('comment', ''))
            tr = m.find('translation')
            if tr is None or tr.get('type') in {'unfinished', 'vanished', 'obsolete'}:
                continue
            result[key] = [f.text or '' for f in tr.findall('numerusform')] or [tr.text or '']
    return result


def visible(text):
    # Keep punctuation, spaces and Qt tokens; ignore formatting overhead.
    text = re.sub(r'<br\s*/?>', ' ', text, flags=re.I)
    text = re.sub(r'</?[A-Za-z][^<>]*>', '', text)
    return ' '.join(html.unescape(text).split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('english_ts')
    parser.add_argument('russian_ts')
    args = parser.parse_args()
    en, ru = messages(args.english_ts), messages(args.russian_ts)
    checked = flagged = keys = 0
    for key in sorted(en.keys() & ru.keys()):
        english, russian = en[key], ru[key]
        if (len(english), len(russian)) not in {(1, 1), (2, 3)}:
            continue  # Resolve differences in numerus structure before measuring.
        hits = 0
        for i, form in enumerate(russian):
            a, b = visible(english[min(i, 1)]), visible(form)
            if not a or not b:
                continue
            checked += 1
            if abs(len(b) - len(a)) >= 8 and 100 * abs(len(b) - len(a)) > 30 * len(a):
                print(f'{key[0]} [{i + 1}]: EN {len(a)} → RU {len(b)} | {a} → {b}')
                hits += 1
        flagged += hits
        keys += bool(hits)
    print(f'Compared forms: {checked}; flagged forms: {flagged}; flagged keys: {keys}')


if __name__ == '__main__':
    main()
