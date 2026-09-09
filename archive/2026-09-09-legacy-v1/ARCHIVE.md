# Legacy v1 — reference only

Archived on 2026-09-09 at the user's request to start a new bottom-up investigation.

- Source commit: `dd723066e3c6c2e3be9ce61c7503a95dc82e5f5b`.
- Source working tree: clean before archival.
- Scope: every one of the 74 previously tracked files, including a copy of the
  original `.gitignore`. Root `.gitignore` remains active and may evolve.
- Verification: each archived file's SHA-256 digest matched its pre-move contents.
  File details are recorded in [MANIFEST.json](MANIFEST.json).
- The original scripts, configs, trial wrappers, README, handoff, task lists, and
  CLAUDE instructions retain their original contents and relative layout.
- Existing Git history, local `.claude` settings, and cluster data/results were
  not changed. Ignored caches may have moved with their directories; they are
  not part of the tracked-file manifest.

These files are historical evidence, not an active pipeline or scientific protocol.
Some documentation is stale, some scripts contain unsafe scientific defaults, and
some wrappers can fetch code or write to old cluster output paths. Do not run them
as part of the restarted project. Inspect source text and history for reference.

Do not edit archived source to fix issues. Record findings in the active
[component audit](../../docs/COMPONENT_AUDIT.md) and implement tested replacements
after the new contracts are settled.

The archive is a repository snapshot, not an operating-system write lock. Its
integrity is checked against `MANIFEST.json`; future automation should exclude it
from execution and verify the manifest when changing archive-related tooling.
