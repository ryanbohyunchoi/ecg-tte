"""Verifier helper: list the restricted output tree (names and sizes only) and create the scratch dir."""
import os
os.umask(0o077)
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
os.makedirs(OUT + "/verify", exist_ok=True)
for root, dirs, files in os.walk(OUT):
    if "/verify" in root:
        continue
    depth = root[len(OUT):].count("/")
    if depth > 3:
        continue
    shard = [f for f in files if f.startswith("part-") or f.startswith("restricted_embeddings_part-")]
    other = [f for f in files if f not in shard]
    print(root[len(OUT):] or "/", f"[{len(shard)} shards]" if shard else "", sorted(other)[:40])
