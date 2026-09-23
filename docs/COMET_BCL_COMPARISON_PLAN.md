# BCL ECG comparison: input review pending

User supplied the invocation:

```text
conda env create -f torch_env.yml
CUDA_VISIBLE_DEVICES=0,1 torchrun --standalone --nproc_per_node=2 bcl_embed_torch.py --input-file /path/to/cohort.csv --output-dir /mnt/<data folder>/bcl_embeddings_<date>
```

These are filenames/placeholders, not verified absolute source/checkpoint paths.
Do not run the template or assume which BCL model it loads. No BCL extraction
or matching has been implemented from this new script yet. The exact script and
environment were not found in the local ecg-tte repository or filename search of
local sibling repositories and /private/tmp. Earlier archived checkpoint lead
`cardiomap/experiments/ecg_biometric/best.pt` was absent on H100. A different
`variant/scripts/run_bcl_1m.sh` references another pretraining workflow; it is not
evidence that the newly supplied script uses that checkpoint. No substitution.

## Next required input

Locate the H100 directory/repository containing `bcl_embed_torch.py` and
`torch_env.yml`, plus the frozen weights or configuration used by that script.
Ryan supplies source code/configuration or makes it available locally for review;
never SSH to the cluster. Do not share cohort CSV rows or patient identifiers.

Review script without executing it: input column names and ECG path convention,
model architecture/checkpoint resolution, preprocessing (sampling rate, lead order,
length/scaling), embedding layer/dimension, eval/no-gradient inference, distributed
sharding and output identity/deduplication. Record hashes before a smoke test.
A two-GPU torchrun invocation alone does not establish distributed correctness.
Install a separate environment with an explicit RAID prefix/cache/tmp once the
actual environment file is inspected; do not overwrite an existing environment.

## Proposed cohort/representation policy (not yet frozen)

Use the existing full clean COMET candidate roster, not only PSM-matched patients.
Select the most recent eligible ECG on strictly prior calendar days1–365, with
an explicit deterministic tie rule and exact patient/date identity validation.
The earlier metadata audit found6,272 patients with a prior-window ECG, but that
is not proof of waveform usability or final encoder coverage. Freeze selection
before inspecting BCL balance. Do not use same-day/future ECGs or substitute a
later recording when an earlier recording fails inference without a declared rule.

Use one frozen BCL vector per included patient. Record all exclusions, selected
recording provenance, source/checkpoint/preprocessing and vector QC privately.
Do not train or select a checkpoint using COMET outcomes or balance results.

## Comparison policy to resolve before running

The ongoing primary representation comparison is direct embedding matching versus
clinical PSM. BCL cosine matching and embedding-derived propensity scores are
separate methods; the phrase 'PSM with embeddings' must not silently replace the
requested direct-comparison design. Confirm if an additional embedding-PS model
is intended and specify dimensionality/model regularization separately.

Rerun the unchanged clinical PSM on the BCL-available population, using existing
imputations subsetted without refitting MICE. For a BCL-versus-CLMBR comparison,
use their common available patients and the same prespecified matching rules.
Keep earlier full-population PSM/CLMBR outputs separate. Cosine geometry differs
between encoders: the CLMBR0.20/0.30/0.40 calipers are not validated equivalent
support constraints for BCL. Any reused grid must be explicitly exploratory.
Report retention, complete/observed balance and missingness together, preserve
all methods, and do not tune to force BCL superiority. No effects readiness implied.
