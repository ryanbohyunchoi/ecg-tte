#!/usr/bin/env python
"""Single entry point for the MIMIC-IV external validation (docs/mimic/MIMIC_EXTERNAL_VALIDATION.md).

Imports the existing modules (scripts/v20/*, scripts/v21/* are not modified) and reproduces every number of the doc
from the restricted outputs under /mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014 (umask 077), with gates.

  python run_mimic_external.py all          CPU steps in order, each gated (tte-analysis env):
      gate0      Step 0: PS-CVD5 +/- ECG +/- permuted ECG re-run from scratch == v21 (cells and headline exact)
      meds       Step 1: MIMIC -> MEDS (skipped if built; leakage checks asserted inside)
      coverage   Step 1.5: vocabulary coverage gate vs Yale (STOP / GO)
      encode     Step 2: CLMBR-T inference (prints the mosaic-env command; needs a GPU; checks hashes vs Yale if run)
      analyze    Step 3: all arms x bases x populations; base / ECG / permECG cells == v21 exactly
      summarize  Step 3: endpoints, masks, agreement, PEPTIC, validity, Yale s31 side by side
      meds_prior build the primary CLMBR-T input (meds_prior; skipped if built)
      prior      PRIMARY CLMBR-T input (decision 2026-10-15): history before the index admission only (own GPU run);
                 the 'summarize' outputs (index-admission pre-t0 labs and orders included) are the sensitivity
      numbers    every headline number of the doc, regenerated (OUT/summary/doc_numbers.json)
      check-doc  each regenerated number must appear verbatim in the doc
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from mimic_common import CLMBR, MEDS, MODEL, OUT, status

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/mimic/MIMIC_EXTERNAL_VALIDATION.md"
YALE_MANIFEST = OUT.parent / "claude-plato-clmbr-codeonly/report/manifest.json"
ENCODE_CMD = ("CUDA_VISIBLE_DEVICES=<free GPU, never 7> LD_PRELOAD=$MOS/lib/libstdc++.so.6 $MOS/bin/python "
              f"scripts/mimic/encode_mimic_clmbr.py --meds-root {MEDS} --model-root {MODEL} --numeric-mode code-only "
              f"--max-tokens 4096 --limit 0 --output-dir {CLMBR}/full   (MOS=/mnt/raid0/rbc58/ecg-tte/software/mosaic-env)")


def gate0():
    import step0_gate
    sys.argv = [sys.argv[0]] + (["--reuse"] if (OUT / "step0" / "results").exists() else [])
    return step0_gate.main()


def meds():
    if (MEDS / "summary.json").exists():
        s = json.load(open(MEDS / "summary.json"))
        lc = s["qc"]["leakage_checks"]
        return s["status"] == "complete_cohort_meds" and lc["at_or_after_t0"] == 0 and lc["dxpx_index_adm"] == 0
    import build_mimic_meds
    return build_mimic_meds.main() == 0


def coverage():
    import coverage as COV
    COV.main()
    return (OUT / "coverage" / "GO").exists()


def encode():
    """Checks of the finished run (the run itself is a GPU job; ENCODE_CMD)."""
    import glob
    import numpy as np
    import pandas as pd
    s = json.load(open(CLMBR / "full" / "summary.json"))
    m = json.load(open(CLMBR / "full" / "manifest.json"))
    y = json.load(open(YALE_MANIFEST))
    R = pd.read_parquet(MEDS / "restricted_cohort.parquet")
    E = pd.concat([pd.read_parquet(f, columns=["subject_id", "embedding"]) for f in sorted(glob.glob(str(CLMBR / "full" / "restricted_embeddings_part-*.parquet")))])
    X = np.stack(E.embedding.to_numpy())
    chk = dict(status=s["status"], model_sha256_equal_yale=m["model_sha256"] == y["model_sha256"], runtime_equal_yale=m["runtime"] == y["runtime"],
               numeric_mode=m["numeric_mode"], max_tokens=m["max_tokens"], n_embeddings=len(E), n_subjects=len(R),
               one_per_subject=bool(E.subject_id.is_unique and set(E.subject_id) == set(R.subject_id)),
               all_finite=bool(np.isfinite(X).all()), dim=int(X.shape[1]), manifest_has_hashes=bool(m["outputs"]) and all(len(h) == 64 for h in m["outputs"].values()),
               birth_only=int(s["totals"].get("encoded_birth_only", 0)), truncated=int(s["totals"].get("truncated_patients", 0)))
    json.dump(chk, open(CLMBR / "full" / "checks.json", "w"), indent=1)
    print(json.dumps(chk, indent=1))
    ok = (chk["status"] == "complete_embeddings" and chk["model_sha256_equal_yale"] and chk["runtime_equal_yale"] and chk["one_per_subject"]
          and chk["all_finite"] and chk["dim"] == 768 and chk["manifest_has_hashes"] and chk["numeric_mode"] == "code-only" and chk["max_tokens"] == 4096)
    status(f"step 2 checks {'PASS' if ok else 'FAIL'}: {chk}")
    return ok


def analyze():
    import mimic_clmbr_analysis as AN
    return AN.main() == 0


def summarize():
    import mimic_clmbr_summary as SM
    return SM.main() == 0


def prior():
    """Primary CLMBR-T input since 2026-10-15 (was a sensitivity): history before the index admission only (build_meds_prior_only.py; GPU run into
    CLMBR/prior_full with the same command on --meds-root OUT/meds_prior). Same analysis and summary, own output dirs."""
    from multiprocessing import Pool
    import mimic_clmbr_analysis as AN
    import mimic_clmbr_summary as SM
    s = json.load(open(CLMBR / "prior_full" / "manifest.json"))
    y = json.load(open(YALE_MANIFEST))
    assert s["model_sha256"] == y["model_sha256"] and s["runtime"] == y["runtime"]
    AN.EMB, AN.RES = CLMBR / "prior_full", OUT / "results_prior"
    with Pool(8) as p:
        p.map(AN.run_trial, AN.TRIALS)
    print(AN.gate_v21())
    SM.RES, SM.SUM = OUT / "results_prior", OUT / "summary_prior"
    SM.status = lambda s: status("primary (CLMBR-T input = history before the index admission time): " + s)
    return SM.main() == 0


def _f(x, d=1):
    return f"{x:.{d}f}".replace("-", "−")


def _ci(c):
    return f"{_f(c['relred'])}% ({_f(c['lo'])} to {_f(c['hi'])})"


def _p(p):
    return "<.001" if p < 0.001 else f"{p:.3f}".lstrip("0")


def numbers():
    """The headline numbers of the doc, formatted as written there.

    Primary (2026-10-15): CLMBR-T input = history before the index admission (OUT/summary_prior). The ECG, base and
    permuted-ECG cells are identical in both runs. The index-admission-stream input (OUT/summary) is the sensitivity
    (keys sens_idx_*)."""
    S = json.load(open(OUT / "summary_prior" / "summary.json"))
    COV = json.load(open(OUT / "coverage" / "coverage.json"))
    G0 = json.load(open(OUT / "step0" / "gate.json"))
    MS_ = json.load(open(MEDS / "summary.json"))
    C = S["contrasts"]
    N = {}
    m, y = COV["mimic_all8"], COV["yale_s31"]
    N["cov_share_mimic"] = f"{100 * m['share_events_in_vocab']:.1f}%"
    N["cov_share_yale"] = f"{100 * y['share_events_in_vocab']:.1f}%"
    N["cov_median_mimic"] = f"{m['in_vocab_events_per_patient'][0]:.0f} ({m['in_vocab_events_per_patient'][1]:.0f}–{m['in_vocab_events_per_patient'][2]:.0f})"
    N["cov_median_yale"] = f"{y['in_vocab_events_per_patient'][0]:.0f} ({y['in_vocab_events_per_patient'][1]:.0f}–{y['in_vocab_events_per_patient'][2]:.0f})"
    N["cov_nohist_mimic"] = f"{100 * m['share_no_prior_coded_history']:.1f}%"
    N["cov_nohist_outside_mimic"] = f"{100 * m['share_no_history_outside_index_admission']:.1f}%"
    N["meds_subjects"] = f"{MS_['subjects']:,}"
    N["meds_rows"] = f"{MS_['rows'] / 1e6:.1f} million"
    N["analysed_patients"] = f"{m['n_patients']:,}"
    N["gate0"] = f"{G0['headline']['relred']}% ({G0['headline']['ci'][0]}–{G0['headline']['ci'][1]})"
    for key, lab in (("ecg", "+ ECG vs PS-CVD5"), ("clm", "+ CLMBR-T vs PS-CVD5"), ("both", "+ ECG + CLMBR-T vs PS-CVD5"),
                     ("both_vs_clm", "+ ECG + CLMBR-T vs + CLMBR-T"), ("both_vs_ecg", "+ ECG + CLMBR-T vs + ECG"),
                     ("clm_vs_ecg", "+ CLMBR-T vs + ECG"), ("ecg_vs_perm", "+ ECG vs + permuted ECG"),
                     ("clm_vs_perm", "+ CLMBR-T vs + permuted CLMBR-T"), ("permecg", "+ permuted ECG vs PS-CVD5"),
                     ("permclm", "+ permuted CLMBR-T vs PS-CVD5")):
        c = C[f"primary7|cvd5|all|{lab}"]
        N[f"{key}_relred"] = _ci(c)
        N[f"{key}_lower"] = c["lower"]
        N[f"{key}_p"] = _p(c["p"])
        N[f"{key}_pct"] = f"{c['pct_b']:.1f} → {c['pct_a']:.1f}"
        N[f"{key}_absd"] = f"{c['absd_b']:.3f} → {c['absd_a']:.3f}"
        if lab in S["yale_s31"]:
            N[f"{key}_yale"] = _ci(S["yale_s31"][lab])
    for var, ck in (("anydm", "primary7|cvd5_anydm|all"), ("incl", "primary7|cvd5_incl|all"), ("noidx", "primary7|cvd5|no_index_day_ecg"),
                    ("all8", "all8|cvd5|all")):
        for key, lab in (("ecg", "+ ECG vs PS-CVD5"), ("clm", "+ CLMBR-T vs PS-CVD5"), ("both", "+ ECG + CLMBR-T vs PS-CVD5"),
                         ("both_vs_clm", "+ ECG + CLMBR-T vs + CLMBR-T")):
            c = C[f"{ck}|{lab}"]
            N[f"sens_{var}_{key}"] = f"{_ci(c)}; {c['lower']}"
    for key, lab in (("clm", "+ CLMBR-T vs PS-CVD5"), ("both", "+ ECG + CLMBR-T vs PS-CVD5"), ("both_vs_clm", "+ ECG + CLMBR-T vs + CLMBR-T")):
        c = C[f"primary7|cvd5|all|{lab}|unmasked"]
        N[f"sens_unmasked_{key}"] = f"{_ci(c)}; {c['lower']}"
    for arm, g in S["peptic"]["cvd5"].items():
        N[f"peptic_{arm}"] = f"{g['hr']:.2f} ({g['lo']:.2f}–{g['hi']:.2f})"
    for arm, g in S["agreement"]["primary7|cvd5|all"].items():
        N[f"agree_{arm}"] = f"| {g['r']:.2f} | {g['est_agree']} | {g['std_agree']} | {g['mean_abs_dloghr']:.3f} |"
    I = json.load(open(OUT / "summary" / "summary.json"))  # sensitivity: index-admission pre-t0 labs and orders included
    for key, lab in (("clm", "+ CLMBR-T vs PS-CVD5"), ("both", "+ ECG + CLMBR-T vs PS-CVD5"), ("both_vs_clm", "+ ECG + CLMBR-T vs + CLMBR-T")):
        c = I["contrasts"][f"primary7|cvd5|all|{lab}"]
        N[f"sens_idx_{key}"] = f"{_ci(c)}; {c['lower']}"
    N["sens_idx_peptic_clm"] = "{hr:.2f} ({lo:.2f}–{hi:.2f})".format(**I["peptic"]["cvd5"]["CLMBR"])
    return N


def check_doc():
    N = numbers()
    json.dump(N, open(OUT / "summary" / "doc_numbers.json", "w"), indent=1, ensure_ascii=False)
    text = DOC.read_text()
    missing = {k: v for k, v in N.items() if v not in text}
    print(json.dumps(dict(n=len(N), missing=missing), indent=1, ensure_ascii=False))
    status(f"check-doc: {len(N) - len(missing)}/{len(N)} regenerated numbers found verbatim in the doc" + (f"; missing {sorted(missing)}" if missing else ""))
    return not missing


def meds_prior():
    """Build the primary CLMBR-T input (OUT/meds_prior) from OUT/meds (build_meds_prior_only.py; skipped if built)."""
    if (OUT / "meds_prior" / "summary.json").exists():
        return True
    import build_meds_prior_only as BP
    return BP.main() in (None, 0)


STEPS = dict(gate0=gate0, meds=meds, meds_prior=meds_prior, coverage=coverage, encode=encode, analyze=analyze, summarize=summarize, prior=prior,
             numbers=lambda: print(json.dumps(numbers(), indent=1, ensure_ascii=False)) or True, **{"check-doc": check_doc})


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "all":
        for name in ("gate0", "meds", "coverage", "encode", "analyze", "summarize", "meds_prior", "prior", "check-doc"):
            if name == "encode" and not (CLMBR / "full" / "manifest.json").exists():
                print("run the GPU step first:\n" + ENCODE_CMD)
                return 1
            if not STEPS[name]():
                print(f"gate failed at {name}")
                return 1
        return 0
    return 0 if STEPS[cmd]() else 1


if __name__ == "__main__":
    sys.exit(main())
