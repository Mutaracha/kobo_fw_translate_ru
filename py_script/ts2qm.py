"""Compile a Qt .ts into .qm (Russian plural rules). Usage: ts2qm.py in.ts out.qm"""
import sys, os
from xml.etree import ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
from qmwrite import write_qm
msgs = []
for c in ET.parse(sys.argv[1]).getroot().iter("context"):
    ctx = c.findtext("name")
    for m in c.iter("message"):
        tr = m.find("translation")
        if tr is None or tr.get("type") in ("unfinished", "vanished", "obsolete"):
            continue
        forms = [nf.text or "" for nf in tr.findall("numerusform")] if m.get("numerus") == "yes" else [tr.text or ""]
        if not any(f.strip() for f in forms):
            continue
        msgs.append({"ctx": ctx, "src": m.findtext("source") or "", "cmt": m.findtext("comment") or "", "tr": forms})
n = write_qm(sys.argv[2], msgs, b"ru_RU", bytes.fromhex("1101fd290bff140204fd2c0a13"))
print("messages", len(msgs), "bytes", n)
