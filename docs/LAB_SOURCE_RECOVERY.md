# 2025 hospital lab shard 3: source recovery required

## Reviewed evidence

Ryan's full byte-structure scan of
`Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_3.txt` reached EOF with unchanged
source metadata. Source size: 66,081,132,812 bytes. Header hash:
`cdb32a17c00ec93b8d6b7a9d294c3c249c7c8274f6340381c020153763ed85ab`.

- 87,246,327 physical data lines match the expected 51 columns.
- Final data physical line 87,246,328 has 15,529,283,887 bytes (15.53 GB),
  only five columns, at least one NUL byte and no terminating newline.
- No exact empty lines. Exactly one over-limit line, width mismatch, NUL-bearing
  line and unterminated line; all refer to that final line.
- Diagnostic elapsed 900.682 seconds.
- SHA-256 of bytes AFTER the header:
  `ed5102d22accc1bd05ae5d594482f3f0f6896d30ca54437dd7d88e85fb216236`.
  This is not a checksum of the complete source file.

This source is structurally invalid under the reviewed literal-tab contract. It
is not an ordinary long narrative field or a harmless empty terminal line. The
root cause (upstream export, transfer, storage, or another process) is unknown.
Matching-width prefix rows are structural observations, not a complete validated
lab table or a substitute denominator. Raising the cap would still encounter NUL
and width failures and could exhaust memory. Do not skip or truncate the tail.

## Recovery path

1. Retain the original source, diagnostic and failed snapshot for lineage. Do not
   modify the raw file, discard the tail or mark the incomplete snapshot complete.
2. Ask the source custodian to check the authoritative copy/export and provide an
   expected full-file byte count, checksum and row count if available. A verified
   intact copy may avoid re-export; a matching malformed original requires source
   correction/re-export. No source custodian has been contacted by the assistant.
3. Keep any corrected delivery as a separate version with explicit provenance.
   Verify its header, full structural accounting, encoding and expected completeness
   before accepting it. A transfer checksum validates copying, not export completeness.
4. Define explicit recovery for the existing snapshot after the corrected source
   path/version is known. Do not bypass the resume contract or edit manifests by
   hand. Reuse the six completed stages only after their source/output integrity
   checks; rebuild the incomplete third shard from a valid source. A changed source
   path/contract needs a deliberate migration, not silent substitution.

## Work that can continue

The complete medication/DX/echo core snapshot is independent. Run
`RUN_COMET_CANDIDATES.md` to build the provisional patient roster and review its
aggregate summary. No labs are required by that job. Drug/identity/HF/timing and
observation eligibility gates still apply before final cohort construction.

The six completed extension stages remain saved in
`/mnt/raid0/rbc58/ecg-tte/shared/psm-sources-v1-0815146D/snapshot`.
The current reader correctly refuses this globally incomplete snapshot. No
partial-snapshot access or exclusion of the failed shard is implemented here.
Later extension sources have not yet been processed by this sequential run;
this diagnostic establishes nothing about their structural integrity.
