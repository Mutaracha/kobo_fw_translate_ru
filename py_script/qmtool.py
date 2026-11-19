import sys, zlib, struct, os, re, json
from xml.etree import ElementTree as ET

QM_MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")


def raw_qm_end(data, start):
    """Find the end of a Qt5 QM's tagged blocks, not the end of nickel."""
    pos = start + len(QM_MAGIC)
    tags = set()
    while pos + 5 <= len(data):
        tag, size = struct.unpack_from(">BI", data, pos)
        if tag not in (0x2F, 0x42, 0x69, 0x88, 0x96, 0xA7) or tag in tags:
            break
        if not size or pos + 5 + size > len(data):
            break
        tags.add(tag)
        pos += 5 + size
    if {0x42, 0x69} <= tags:  # Offsets and messages; ignore stray magic constants.
        return pos


def find_qms(path, outdir):
    with open(path, "rb") as f:
        data = f.read()
    res, raws = [], []

    def save(off, blob):
        fn = os.path.join(outdir, f"{os.path.basename(path)}_{off:x}.qm")
        with open(fn, "wb") as f:
            f.write(blob)
        res.append((fn, len(blob)))

    for match in re.finditer(re.escape(QM_MAGIC), data):
        off = match.start()
        raws.append(off)
        end = raw_qm_end(data, off)
        if end is not None:
            save(off, memoryview(data)[off:end])

    # Qt resources can also be zlib streams. Probe the signature before
    # inflating the full resource, and don't accept partial streams.
    for match in re.finditer(rb"\x78[\x01\x5e\x9c\xda]", data):
        off = match.start()
        try:
            if zlib.decompressobj().decompress(data[off:off + 1024], 16) != QM_MAGIC:
                continue
            stream = zlib.decompressobj()
            blob = stream.decompress(memoryview(data)[off:])
        except zlib.error:
            continue
        if stream.eof and raw_qm_end(blob, 0) == len(blob):
            save(off, blob)
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
