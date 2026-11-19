"""Write a Qt Linguist .ts from a translated .qm plus the firmware's full string list.
Usage: qm2ts.py translated.qm english_source.qm out.ts language
Strings present in the firmware but missing from translated.qm are written as unfinished.
"""
import sys, os
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(__file__))
from qmtool import parse_qm

tr_qm, src_qm, out, lang = sys.argv[1:5]
_, tr = parse_qm(tr_qm)
_, src = parse_qm(src_qm)
key = lambda m: (m.get("ctx", ""), m.get("src", ""), m.get("cmt", ""))
trans = {key(m): m["tr"] for m in tr}
allkeys = {key(m): m for m in src}
for k, m in trans.items():
    allkeys.setdefault(k, {"ctx": k[0], "src": k[1], "cmt": k[2], "tr": m})

def x(s):
    return escape(s, {'"': "&quot;", "'": "&apos;"})

ctxs = {}
for k in sorted(allkeys, key=lambda k: (k[0].encode(), k[1].encode(), k[2].encode())):
    ctxs.setdefault(k[0], []).append(k)

lines = ['<?xml version="1.0" encoding="utf-8"?>', "<!DOCTYPE TS>", f'<TS version="2.1" language="{lang}">']
for c, keys in ctxs.items():
    lines += ["<context>", f"    <name>{x(c)}</name>"]
    for k in keys:
        forms = trans.get(k)
        numerus = (forms and len(forms) > 1) or (not forms and "%n" in k[1] and len(allkeys[k]["tr"]) > 1)
        lines.append('    <message numerus="yes">' if numerus else "    <message>")
        lines.append(f"        <source>{x(k[1])}</source>")
        if k[2]:
            lines.append(f"        <comment>{x(k[2])}</comment>")
        if not forms:
            lines.append('        <translation type="unfinished"></translation>')
        elif numerus:
            lines.append("        <translation>")
            lines += [f"            <numerusform>{x(f)}</numerusform>" for f in forms]
            lines.append("        </translation>")
        else:
            lines.append(f"        <translation>{x(forms[0])}</translation>")
        lines.append("    </message>")
    lines.append("</context>")
lines.append("</TS>")
open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("contexts", len(ctxs), "messages", len(allkeys), "translated", sum(1 for k in allkeys if k in trans))
