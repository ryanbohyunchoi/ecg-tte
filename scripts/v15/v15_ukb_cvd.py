"""v1.5 UKB CV-death sensitivity (protocol deviation log 2026-09-26, "UKB CV-death sensitivity").

Source dirs (not modified): claude-v15-ukb-<trial> and claude-v15s-ukb-<trial>-elig.
Targets: claude-v15s-ukb-<trial>-cvd and claude-v15s-ukb-<trial>-elig-cvd.
Cohort, baseline, roles, panel, dictionary, ecg/clmbr embeddings and rct.json are copied, restricted to index
(imaging visit) before CVD_END. New outcomes: ONTARGET = first of CV death, MI, stroke, HF; ALLHAT/ASCOT = CV death
(proxy for CHD death) or MI. CV death = cv_death_all == 1 in ukb_working_file.csv (date = 40000 death date).
Censoring at the earliest of non-CV death, horizon and CVD_END. Aggregates only; counts 1-10 suppressed.
Usage: python v15_ukb_cvd.py [trial ...]
"""
import json
import os
import shutil
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v15_ukb_build as V
from v15_ukb_common import AUDIT, NCO, OUT_CODES

os.umask(0o077)
WORK = "/mnt/nfs_yale_ecg/biobank/ukb_working_file.csv"
CVD_END = pd.Timestamp("2020-12-31")  # end of cause-of-death coverage (max death date in WORK: 2020-12-18)
OUTC = {"ontarget": ["cv_death", "mi", "stroke", "hf"], "allhat": ["cv_death", "mi"], "ascot": ["cv_death", "mi"]}
COPY = ["cohort.parquet", "baseline.parquet", "panel.parquet", "ecg_embedding.parquet", "clmbr_embedding.parquet",
        "ecg_manifest.parquet"]
sup = V.sup


def load_cv():
    c = duckdb.connect()
    w = c.execute(f"""select eid, cv_death_all, cv_death_all_date, "Date of death_40000-0.0" d0
                      from read_csv_auto('{WORK}', delim='\t', all_varchar=true, sample_size=-1)""").df()
    w["eid"] = w.eid.astype(str)
    w = w.drop_duplicates("eid").set_index("eid")
    chk = dict(rows=len(w), deaths=int(w.d0.notna().sum()), max_death_date=str(w.d0.dropna().max()),
               cv_deaths=int((w.cv_death_all == "1").sum()),
               cv_date_differs_from_40000=int(((w.cv_death_all == "1") & (w.cv_death_all_date != w.d0)).sum()))
    return w, chk


def main(trials):
    w, chk = load_cv()
    base, dx, _, _ = V.load()
    dx["eid"] = dx.eid.astype(str)
    dx["date"] = pd.to_datetime(dx.date)
    b = V.prep_base(base)
    b = b.join(w[["cv_death_all"]], how="left")
    death_match = int(((b.death_date.notna()) & (b.death_date <= CVD_END)).sum())
    death_linked = int(((b.death_date.notna()) & (b.death_date <= CVD_END) & b.cv_death_all.notna()).sum())
    for trial in trials:
        for src_name, dst_name in [(f"claude-v15-ukb-{trial}", f"claude-v15s-ukb-{trial}-cvd"),
                                   (f"claude-v15s-ukb-{trial}-elig", f"claude-v15s-ukb-{trial}-elig-cvd")]:
            src, dst = Path(AUDIT) / src_name, Path(AUDIT) / dst_name
            if not all((src / m).exists() for m in ("READY_COHORT", "READY_ECG")):
                print(src_name, "not ready; skipped")
                continue
            dst.mkdir(mode=0o700, exist_ok=True)
            coh = pd.read_parquet(src / "cohort.parquet")
            coh["pid"] = coh.pid.astype(str)
            keep = set(coh.pid[pd.to_datetime(coh.index_day, unit="D") < CVD_END])
            for f in COPY:
                if (src / f).exists():
                    x = pd.read_parquet(src / f)
                    x = x[x.pid.astype(str).isin(keep)]
                    x.to_parquet(dst / f, index=False)
            for f in ("roles.json", "panel_dictionary.csv"):
                shutil.copy2(src / f, dst / f)
            rct = json.load(open(src / "rct.json"))
            rct["endpoint"] = {"ontarget": "CV death (cv_death_all), MI, stroke or HF",
                               "allhat": "CV death (proxy for CHD death) or MI",
                               "ascot": "CV death (proxy for CHD death) or MI"}[trial]
            rct["notes"] += (f" CV-death sensitivity: CV death from ukb_working_file.csv cv_death_all; follow-up censored at "
                             f"{CVD_END.date()} (cause-of-death coverage end); index before that date.")
            json.dump(rct, open(dst / "rct.json", "w"), indent=1)
            coh = coh[coh.pid.isin(keep)]
            c = b.loc[coh.pid].copy()
            c["treated"] = coh.treated.values
            idx = c.index_date
            H = rct["horizon_days"]
            dd = dx[dx.eid.isin(c.index)].join(idx, on="eid")
            died = c.death_date.where(c.death_date <= CVD_END)
            cv = died.where(c.cv_death_all == "1")
            noncv = died.where(c.cv_death_all != "1")  # includes deaths not linked in WORK (treated as non-CV censoring)
            admin_end = pd.concat([pd.Series(CVD_END, index=c.index), noncv], axis=1).min(axis=1)

            def first_after(codes, extra=None):
                s = dd[dd.code.str.startswith(tuple(codes)) & (dd.date > dd.index_date)].groupby("eid").date.min().reindex(c.index)
                if extra is not None:
                    s = pd.concat([s, extra.where(extra > idx)], axis=1).min(axis=1)
                return s

            def te(evdate, horizon, end_base):
                end = pd.concat([end_base, idx + pd.Timedelta(days=horizon)], axis=1).min(axis=1)
                e = (evdate.notna() & (evdate <= end)).astype(int)
                t = np.where(e == 1, (evdate - idx).dt.days, (end - idx).dt.days).astype(float)
                return np.where(t <= 0, 0.5, t), e.values

            comp = {}
            for k in OUTC[trial]:
                if k == "cv_death":
                    comp[k] = cv.where(cv > idx)
                elif k == "mi":
                    comp[k] = first_after(OUT_CODES["mi"], c.mi_alg_date)
                elif k == "stroke":
                    comp[k] = first_after(OUT_CODES["stroke"], c.stroke_alg_date)
                else:
                    comp[k] = first_after(OUT_CODES[k])
            ev = pd.concat(comp.values(), axis=1).min(axis=1)
            # non-event components still censor at CV death? No: CV death is an event; non-CV death censors.
            out = pd.DataFrame({"pid": c.index.astype(str)})
            out["t"], out["e"] = te(ev, H, admin_end)
            all_death_end = pd.Series(CVD_END, index=c.index)
            if trial == "ontarget":
                sec_h = rct["secondary"][0]["horizon_days"]
                out["t_sec_death"], out["e_sec_death"] = te(died.where(died > idx), sec_h, all_death_end)
            # NCOs: censor at any death (CV or not), horizon, CVD_END
            nco_end = pd.concat([all_death_end, died], axis=1).min(axis=1)
            tr = coh.treated.values == 1
            ncos = {}
            for nm, codes in NCO.items():
                prev = dd[dd.code.str.startswith(tuple(codes)) & (dd.date <= dd.index_date)].eid.unique()
                t, e = te(first_after(codes), H, nco_end)
                p = c.index.isin(prev)
                out[f"t_nco_{nm}"] = np.where(p, np.nan, t)
                out[f"e_nco_{nm}"] = np.where(p, np.nan, e.astype(float))
                ok = ~p
                ncos[nm] = dict(n_at_risk=sup(ok.sum()), events=[sup(e[ok & tr].sum()), sup(e[ok & ~tr].sum())])
            out.to_parquet(dst / "outcomes.parquet", index=False)
            end_h = pd.concat([admin_end, idx + pd.Timedelta(days=H)], axis=1).min(axis=1)
            per = {k: [sup((v.notna() & (v <= end_h))[tr].sum()), sup((v.notna() & (v <= end_h))[~tr].sum())] for k, v in comp.items()}
            ecg = pd.read_parquet(dst / "ecg_embedding.parquet", columns=["pid"])
            has_ecg = out.pid.isin(set(ecg.pid.astype(str))).values
            clm_n = None
            if (dst / "clmbr_embedding.parquet").exists():
                clm = set(pd.read_parquet(dst / "clmbr_embedding.parquet", columns=["pid"]).pid.astype(str))
                clm_n = [sup(out.pid[tr].isin(clm).sum()), sup(out.pid[~tr].isin(clm).sum())]
            fu = lambda m: [round(float(np.median(out.t[m])) / 365.25, 2), round(float(np.percentile(out.t[m], 25)) / 365.25, 2),
                            round(float(np.percentile(out.t[m], 75)) / 365.25, 2)]
            src_s = json.load(open(src / "summary.json"))
            summ = dict(trial=trial, source_dir=src_name, sensitivity="CV-death outcome, cause-of-death coverage censoring",
                        arms=src_s["arms"], n_source=[sup(src_s_n) for src_s_n in [len(pd.read_parquet(src / "cohort.parquet"))]],
                        n_excluded_index_after_cvd_end=sup(len(pd.read_parquet(src / "cohort.parquet")) - len(coh)),
                        n_arm=[sup(tr.sum()), sup((~tr).sum())], n_arm_with_ecg=[sup((tr & has_ecg).sum()), sup((~tr & has_ecg).sum())],
                        n_arm_with_clmbr=clm_n,
                        outcomes=dict(components=OUTC[trial], horizon_days=H, events_primary=[sup(out.e[tr].sum()), sup(out.e[~tr].sum())],
                                      events_primary_with_ecg=[sup(out.e[tr & has_ecg].sum()), sup(out.e[~tr & has_ecg].sum())],
                                      events_by_component=per, followup_years_median_iqr=dict(first=fu(tr), second=fu(~tr)),
                                      noncv_deaths_censored=[sup((noncv.notna() & (noncv > idx))[tr].sum()), sup((noncv.notna() & (noncv > idx))[~tr].sum())],
                                      nco=ncos),
                        cv_death_source=dict(file=WORK, flag="cv_death_all", **chk,
                                             deaths_to_cvd_end_in_imaging_population=death_match,
                                             of_which_linked_to_flag=death_linked),
                        notes=[f"CV death = cv_death_all == 1 (derivation undocumented; likely I00-I99 underlying or contributory); "
                               f"date = 40000 death date (cv_death_all_date identical for all CV deaths)",
                               f"follow-up end {CVD_END.date()}: cause-of-death coverage (max death date in file 2020-12-18; "
                               f"December 2020 deaths appear incompletely recorded, about half of prior months)",
                               "censoring at min(non-CV death, horizon, 2020-12-31); events strictly after index",
                               "ALLHAT/ASCOT: CV death is a proxy for CHD death" if trial != "ontarget" else
                               "ONTARGET: CV death replaces all-cause death; t_sec_death = all-cause death (ELITE II), censored 2020-12-31",
                               "NCOs recomputed: censored at any death, horizon and 2020-12-31; prevalent cases NaN",
                               "MI/stroke/HF from 41270/41280 first occurrences and 42000/42006 (first event only)",
                               V.ECG_ON_TREATMENT, "field 191 (lost to follow-up) not applied, as in the main dirs"])
            json.dump(summ, open(dst / "summary.json", "w"), indent=1, default=str)
            (dst / "READY_COHORT").write_text("ok\n")
            (dst / "READY_ECG").write_text(json.dumps(dict(copied_from=src_name, n_with_ecg=int(has_ecg.sum()))) + "\n")
            (dst / "READY_OUTCOMES").write_text("ok\n")
            print(dst_name, json.dumps({k: summ[k] for k in ("n_arm", "n_arm_with_ecg", "n_arm_with_clmbr", "n_excluded_index_after_cvd_end")}),
                  json.dumps({k: summ["outcomes"][k] for k in ("events_primary", "events_primary_with_ecg", "events_by_component",
                                                                 "followup_years_median_iqr", "nco")}, default=str))
    print(json.dumps(chk), death_match, death_linked)


if __name__ == "__main__":
    main(sys.argv[1:] or list(OUTC))
