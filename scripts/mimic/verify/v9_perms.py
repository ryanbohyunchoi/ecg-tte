"""Verifier: count files / dirs under the restricted output tree that are group- or world-accessible (umask 077 rule)."""
import os
import stat

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
n = bad = 0
badtop = set()
for root, dirs, files in os.walk(OUT):
    for x in dirs + files:
        p = os.path.join(root, x)
        m = os.lstat(p).st_mode
        n += 1
        if m & (stat.S_IRWXG | stat.S_IRWXO):
            bad += 1
            badtop.add(p[len(OUT) + 1:].split("/")[0])
m = os.stat(OUT).st_mode
print("entries", n, "group/other-accessible", bad, "top-level dirs affected", sorted(badtop), "| OUT itself mode", oct(m & 0o777))
