"""Shared review rules for the Russian firmware catalog."""
from xml.etree import ElementTree as ET


def is_license(context, source):
    return (context == 'N3SettingsDeviceInformationController' and
            source.lstrip().startswith('<h1><span>Attributions</span></h1>'))


def write_untranslated(ts, report):
    lines = []
    for context in ET.parse(ts).getroot().findall('context'):
        name = context.findtext('name')
        for m in context.findall('message'):
            source = m.findtext('source', '')
            tr = m.find('translation')
            if is_license(name, source) or (tr is not None and tr.get('type') in {'vanished', 'obsolete'}):
                continue
            forms = [] if tr is None else ([f.text for f in tr.findall('numerusform')] or [tr.text])
            if tr is None or tr.get('type') == 'unfinished' or not all((f or '').strip() for f in forms):
                comment = m.findtext('comment')
                lines.append(f'{name} | {source}' + (f' | {comment}' if comment else ''))
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f'Непереведённых сообщений: {len(lines)}\n' + ''.join(s + '\n' for s in lines), encoding='utf-8')
    print(f'Непереведённых сообщений: {len(lines)}. Список: {report}')
