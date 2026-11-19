"""Write a Qt Linguist .ts from a translated .qm plus the firmware's full string list.
Usage: qm2ts.py translated.qm english_source.qm out.ts language
Use - for translated.qm to start an empty translation. Only firmware keys are emitted.
"""
import sys, os
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(__file__))
from qmtool import parse_qm

tr_qm, src_qm, out, lang = sys.argv[1:5]
tr = [] if tr_qm == "-" else parse_qm(tr_qm)[1]
_, src = parse_qm(src_qm)
key = lambda m: (m.get("ctx", ""), m.get("src", ""), m.get("cmt", ""))
trans = {key(m): m["tr"] for m in tr}
allkeys = {key(m): m for m in src}

def x(s):
    return escape(s, {'"': "&quot;", "'": "&apos;"})

ctxs = {}
for k in sorted(allkeys, key=lambda k: (k[0].encode(), k[1].encode(), k[2].encode())):
    ctxs.setdefault(k[0], []).append(k)

lines = ['<?xml version="1.0" encoding="utf-8"?>', "<!DOCTYPE TS>", f'<TS version="2.1" language="{lang}">']
translated = 0
for c, keys in ctxs.items():
    lines += ["<context>", f"    <name>{x(c)}</name>"]
    for k in keys:
        forms = trans.get(k)
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
open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("contexts", len(ctxs), "messages", len(allkeys), "translated", translated)
