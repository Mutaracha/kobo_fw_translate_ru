"""Minimal Qt .qm writer matching lrelease (Qt5) layout:
Language(0xA7), Hashes(0x42), Messages(0x69), NumerusRules(0x88).
Message record: Translation(3)*, Comment(8), SourceText(6), Context(7), End(1).
"""
import struct
from qmtool import QM_MAGIC


def elf_hash(data: bytes) -> int:
    h = 0
    for c in data:
        h = ((h << 4) + c) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
        h &= ~g & 0xFFFFFFFF
    return h or 1


def blk(tag, data):
    return bytes([tag]) + struct.pack(">I", len(data)) + data


def write_qm(path, messages, language: bytes, numerus: bytes):
    """messages: list of dict(ctx, src, cmt, tr=[str,...])"""
    msgs = sorted(messages, key=lambda m: (m["ctx"].encode(), m["src"].encode(), m["cmt"].encode()))
    mb = bytearray()
    hashes = []
    for m in msgs:
        off = len(mb)
        for t in m["tr"]:
            e = t.encode("utf-16-be")
            mb += b"\x03" + struct.pack(">I", len(e)) + e
        for tag, s in ((8, m["cmt"]), (6, m["src"]), (7, m["ctx"])):
            e = s.encode("utf-8")
            mb += bytes([tag]) + struct.pack(">I", len(e)) + e
        mb += b"\x01"
        hashes.append((elf_hash((m["src"] + m["cmt"]).encode("utf-8")), off))
    hashes.sort()
    hb = b"".join(struct.pack(">II", h, o) for h, o in hashes)
    out = QM_MAGIC + blk(0xA7, language) + blk(0x42, hb) + blk(0x69, bytes(mb)) + blk(0x88, numerus)
    open(path, "wb").write(out)
    return len(out)
