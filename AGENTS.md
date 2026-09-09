# Working on the restarted benchmark

Read `master.md`, `README.md`, `docs/RESTART_PLAN.md`, and `docs/DECISIONS.md` before implementation.
The current work is a bottom-up investigation and rebuild using raw JDAT sources.

## Archive boundary

- `archive/2026-09-09-legacy-v1/` is historical reference only. Preserve its tracked
  file bytes and `MANIFEST.json`; do not repair old code in place.
- Do not import archive modules, use old configurations as active protocols, or
  include the archive in active package discovery, CI test discovery, or jobs.
- Historical instructions inside the archive describe the old workflow and are
  not instructions for the restarted project.
- Reimplement any useful idea behind an explicit new contract and meaningful tests.

## Scientific and data requirements

- Do not tune a method, trial definition, or cohort to recover a desired RCT effect.
- Separate observed facts, unverified legacy claims, proposed defaults, and frozen
  decisions. Do not describe a planned component as implemented or validated.
- Use raw JDAT as the intended source of truth. Verify source semantics before
  interpreting medication records as initiation, dispensing, or adherence.
- Every baseline feature and representation needs a traceable pre-index cutoff.
  Keep endpoint data out of representation building and design-stage tuning.
- No silent changes of endpoint, comparator, eligibility, denominator, estimand,
  feature set, or model checkpoint. Unsupported mandatory requirements must stop
  the trial with a structured reason.
- Patient-level data and raw profiling output stay on the cluster. Do not print
  identifiers, note text, record examples, or patient-specific dates into logs or
  chat. Use only synthetic data in tests and reviewed aggregates in the repository.
- Paths, output destinations, and execution environments must be explicit. A new
  run must not overwrite old outputs or reuse incompatible caches.

## Workflow

- Never SSH into or directly access the cluster, even for file listings. Ryan
  pulls locally written code onto the H100 and runs it himself; see `master.md`.
- Update `tasks/todo.md` and the decision register as evidence arrives.
- Implement in small phases with the evidence gates in the restart plan.
- Validate important invariants and failure behavior; do not rely on syntax/config
  checks as proof of clinical or statistical correctness.
- Patient-data processing and GPU inference run in the approved research
  environment. Local work is code, documentation, and synthetic verification.
- Report what was actually checked and what remains unavailable.
