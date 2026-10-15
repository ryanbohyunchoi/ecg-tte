"""Verifier check 6 helper: read-only comparison of working-tree files with their HEAD versions by reading the git
object store directly (loose and packed objects; no git command is run, nothing is written). Prints a unified diff
of each file (docs only; no patient data)."""
import difflib
import glob
import os
import struct
import sys
import zlib

REPO = "/home/rbc58/github/ecg-tte"
GIT = f"{REPO}/.git"


def read_ref(name):
    p = f"{GIT}/{name}"
    if os.path.exists(p):
        s = open(p).read().strip()
        return read_ref(s[5:]) if s.startswith("ref: ") else s
    for line in open(f"{GIT}/packed-refs"):
        if line.strip().endswith(" " + name):
            return line.split()[0]
    raise KeyError(name)


PACKS = []
for idx in glob.glob(f"{GIT}/objects/pack/*.idx"):
    d = open(idx, "rb").read()
    assert d[:4] == b"\xfftOc" and struct.unpack(">I", d[4:8])[0] == 2
    n = struct.unpack(">I", d[8 + 255 * 4:8 + 256 * 4])[0]
    shas = d[8 + 1024:8 + 1024 + 20 * n]
    offs = d[8 + 1024 + 24 * n:8 + 1024 + 28 * n]
    big = d[8 + 1024 + 28 * n:]
    table = {}
    for i in range(n):
        o = struct.unpack(">I", offs[4 * i:4 * i + 4])[0]
        if o & 0x80000000:
            o = struct.unpack(">Q", big[8 * (o & 0x7fffffff):8 * (o & 0x7fffffff) + 8])[0]
        table[shas[20 * i:20 * i + 20].hex()] = o
    PACKS.append((idx[:-4] + ".pack", table))

TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}


def apply_delta(base, delta):
    def varint(i):
        r = s = 0
        while True:
            b = delta[i]; i += 1
            r |= (b & 0x7f) << s; s += 7
            if not b & 0x80:
                return r, i
    _, i = varint(0)
    _, i = varint(i)
    out = bytearray()
    while i < len(delta):
        c = delta[i]; i += 1
        if c & 0x80:
            off = size = 0
            for j in range(4):
                if c & (1 << j):
                    off |= delta[i] << (8 * j); i += 1
            for j in range(3):
                if c & (1 << (4 + j)):
                    size |= delta[i] << (8 * j); i += 1
            size = size or 0x10000
            out += base[off:off + size]
        else:
            out += delta[i:i + c]; i += c
    return bytes(out)


def unpack_at(path, off):
    f = open(path, "rb")
    f.seek(off)
    b = f.read(1)[0]
    typ = (b >> 4) & 7
    while b & 0x80:
        b = f.read(1)[0]
    if typ == 6:
        b = f.read(1)[0]
        neg = b & 0x7f
        while b & 0x80:
            b = f.read(1)[0]
            neg = ((neg + 1) << 7) | (b & 0x7f)
        bt, bd = unpack_at(path, off - neg)
        return bt, apply_delta(bd, zlib.decompressobj().decompress(f.read(1 << 24)))
    if typ == 7:
        ref = f.read(20).hex()
        bt, bd = obj(ref)
        return bt, apply_delta(bd, zlib.decompressobj().decompress(f.read(1 << 24)))
    return TYPES[typ], zlib.decompressobj().decompress(f.read(1 << 24))


def obj(sha):
    p = f"{GIT}/objects/{sha[:2]}/{sha[2:]}"
    if os.path.exists(p):
        raw = zlib.decompress(open(p, "rb").read())
        hdr, _, body = raw.partition(b"\0")
        return hdr.split()[0].decode(), body
    for pack, table in PACKS:
        if sha in table:
            return unpack_at(pack, table[sha])
    raise KeyError(sha)


def tree_lookup(tree_sha, parts):
    _, body = obj(tree_sha)
    i = 0
    while i < len(body):
        sp = body.index(b" ", i)
        nul = body.index(b"\0", sp)
        name = body[sp + 1:nul].decode()
        sha = body[nul + 1:nul + 21].hex()
        i = nul + 21
        if name == parts[0]:
            return sha if len(parts) == 1 else tree_lookup(sha, parts[1:])
    return None


head = read_ref("HEAD")
_, cbody = obj(head)
tree = cbody.split(b"\n")[0].split()[1].decode()
for rel in sys.argv[1:]:
    sha = tree_lookup(tree, rel.split("/"))
    new = open(f"{REPO}/{rel}", encoding="utf-8").read().splitlines()
    if sha is None:
        print(f"=== {rel}: not in HEAD (new file, {len(new)} lines)")
        continue
    old = obj(sha)[1].decode("utf-8").splitlines()
    d = list(difflib.unified_diff(old, new, "HEAD", "worktree", n=0, lineterm=""))
    adds = [x for x in d if x.startswith("+") and not x.startswith("+++")]
    rems = [x for x in d if x.startswith("-") and not x.startswith("---")]
    print(f"=== {rel}: +{len(adds)} -{len(rems)}")
    if "--show" in os.environ.get("VERIFY_FLAGS", "") or len(adds) + len(rems) <= 12:
        for x in d[2:]:
            print("   ", x[:220])
