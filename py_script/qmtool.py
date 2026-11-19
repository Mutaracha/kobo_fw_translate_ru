import sys, zlib, struct, os, re, json
from xml.etree import ElementTree as ET

QM_MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")


def find_qms(path, outdir):
    data = open(path, "rb").read()
    found = []
    # uncompressed qm
    for m in re.finditer(re.escape(QM_MAGIC), data):
        found.append(("raw", m.start(), None))
    # zlib-compressed rcc entries: 4-byte BE size + zlib stream
    for m in re.finditer(rb"\x78[\x01\x5e\x9c\xda]", data):
        off = m.start()
        try:
            d = zlib.decompressobj()
            chunk = d.decompress(data[off:off + 64], 16)
            if not chunk.startswith(QM_MAGIC[:len(chunk)]) or len(chunk) < 16:
                continue
            full = zlib.decompress(data[off:off + 20_000_000]) if False else None
        except Exception:
            continue
        d = zlib.decompressobj()
        try:
            full = d.decompress(data[off:])
        except Exception:
            continue
        found.append(("zlib", off, full))
    res = []
    for i, (kind, off, blob) in enumerate(found):
        if kind == "raw":
            continue  # handled below only if needed
        fn = os.path.join(outdir, f"{os.path.basename(path)}_{off:x}.qm")
        open(fn, "wb").write(blob)
        res.append((fn, len(blob)))
    raws = [o for k, o, _ in found if k == "raw"]
    return res, raws


def parse_qm(path):
    b = open(path, "rb").read()
    assert b[:16] == QM_MAGIC
    p = 16
    msgs_blk = None
    lang = None
    while p < len(b):
        tag = b[p]; ln = struct.unpack(">I", b[p + 1:p + 5])[0]
        blk = b[p + 5:p + 5 + ln]
        if tag == 0x69:
            msgs_blk = blk
        elif tag == 0xA7:
            lang = blk.decode("latin1")
        p += 5 + ln
    out = []
    q = 0
    cur = {}
    while msgs_blk and q < len(msgs_blk):
        t = msgs_blk[q]; q += 1
        if t == 1:  # end
            out.append(cur); cur = {}
            continue
        if t == 3:  # translation utf16
            ln = struct.unpack(">I", msgs_blk[q:q + 4])[0]; q += 4
            if ln == 0xFFFFFFFF:
                s = None
            else:
                s = msgs_blk[q:q + ln].decode("utf-16-be", "replace"); q += ln
            cur.setdefault("tr", []).append(s)
        elif t in (6, 7, 8):  # source, context, comment (utf8/latin1)
            ln = struct.unpack(">I", msgs_blk[q:q + 4])[0]; q += 4
            s = msgs_blk[q:q + ln].decode("utf-8", "replace"); q += ln
            cur[{6: "src", 7: "ctx", 8: "cmt"}[t]] = s
        elif t == 5:  # obsolete1
            ln = struct.unpack(">I", msgs_blk[q:q + 4])[0]; q += 4 + ln
        elif t == 4:  # obsolete2 (source16)
            ln = struct.unpack(">I", msgs_blk[q:q + 4])[0]; q += 4 + ln
        elif t == 2:  # obsolete
            pass
        else:
            raise ValueError(f"unknown tag {t} at {q}")
    return lang, out


def parse_ts(path):
    root = ET.parse(path).getroot()
    out = []
    for c in root.iter("context"):
        ctx = c.findtext("name")
        for m in c.iter("message"):
            tr = m.find("translation")
            out.append({"ctx": ctx, "src": m.findtext("source"), "cmt": m.findtext("comment") or "",
                        "unfinished": tr is not None and tr.get("type") in ("unfinished", "vanished", "obsolete"),
                        "tr": "".join(tr.itertext()) if tr is not None else ""})
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "find":
        outdir = sys.argv[2]
        for f in sys.argv[3:]:
            res, raws = find_qms(f, outdir)
            print(f, "raw-qm-offsets:", [hex(x) for x in raws][:20])
            for fn, n in res:
                lang, msgs = parse_qm(fn)
                print("  ", os.path.basename(fn), n, "lang=", lang, "msgs=", len(msgs))
    elif cmd == "qm":
        lang, msgs = parse_qm(sys.argv[2])
        print(lang, len(msgs))
        print(json.dumps(msgs[:5], ensure_ascii=False, indent=1))
