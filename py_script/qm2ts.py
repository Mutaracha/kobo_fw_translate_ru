"""Write a Qt Linguist .ts from a translated .qm plus the firmware's full string list.
Usage: qm2ts.py translated.qm english_source.qm out.ts [language]
Without a language override, use the language metadata from the source QM.
Use - for translated.qm to start an empty translation. Only firmware keys are emitted.
"""
import sys
from xml.sax.saxutils import escape, quoteattr
from catalog_review import is_license
from qmtool import parse_qm


def x(s):
    return escape(s, {'"': "&quot;", "'": "&apos;"})


def write_ts(tr_qm, src_qm, out, lang=None):
    qm_lang, src = parse_qm(src_qm)
    tr = src if tr_qm == src_qm else ([] if tr_qm == "-" else parse_qm(tr_qm)[1])
    if lang is None:
        lang = qm_lang or ""
    key = lambda m: (m.get("ctx", ""), m.get("src", ""), m.get("cmt", ""))
    trans = {key(m): m["tr"] for m in tr}
    allkeys = {key(m): m for m in src}

    ctxs = {}
    for k in sorted(allkeys, key=lambda k: (k[0].encode(), k[1].encode(), k[2].encode())):
        ctxs.setdefault(k[0], []).append(k)

    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<!DOCTYPE TS>", '<TS version="2.1"' + (f' language={quoteattr(lang)}' if lang else "") + ">"]
    translated = 0
    for c, keys in ctxs.items():
        lines += ["<context>", f"    <name>{x(c)}</name>"]
        for k in keys:
            forms = None if lang.startswith("ru") and is_license(c, k[1]) else trans.get(k)
            numerus = len(allkeys[k]["tr"]) > 1
            if lang.startswith("ru") and len(forms or []) != (3 if numerus else 1):
                forms = [""] * 3 if numerus else []
            if forms and all(forms):
                translated += 1
            lines.append('    <message numerus="yes">' if numerus else "    <message>")
            lines.append(f"        <source>{x(k[1])}</source>")
            if k[2]:
                lines.append(f"        <comment>{x(k[2])}</comment>")
            if not forms or (not numerus and not forms[0]):
                lines.append('        <translation type="unfinished"></translation>')
            elif numerus:
                lines.append('        <translation type="unfinished">' if not all(forms) else "        <translation>")
                lines += [f"            <numerusform>{x(f or '')}</numerusform>" for f in forms]
                lines.append("        </translation>")
            else:
                lines.append(f"        <translation>{x(forms[0])}</translation>")
            lines.append("    </message>")
        lines.append("</context>")
    lines.append("</TS>")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("contexts", len(ctxs), "messages", len(allkeys), "translated", translated)


if __name__ == "__main__":
    write_ts(*sys.argv[1:5])
