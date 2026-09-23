# BCL smoke input preparation

Use scripts/prepare_comet_bcl_smoke.py --report with the completed v2 selection
report and --output-dir with a fresh absolute RAID report directory.
The helper validates linkage digest and selected counts; picks up to eight ECGs
per arm and sampling stratum; checks unchanged waveform size/mtime; and emits
restricted_input.csv plus restricted_formats.csv. The latter is a derived adapter
catalog: 5_0 represents the selection's True250Hz flag; adapter_non250 represents
False. These reproduce upstream's substring test and do not validate frequency.
Never replace the original sampling catalog or use this small catalog for full
cohort inference. The two files must be supplied together for the smoke run.

Expected selection report: /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-input-v2-C9ftzPbQ/report.
No GPU, model, waveforms or other patient records are loaded by this helper.
Actual checkpoint dimensions/configuration, content hash and isolated runtime
still need verification before launching the frozen upstream encoder. Source pin:
d359c04d1f5e6c810f76751777535918870704b7. Outputs remain restricted on H100.
