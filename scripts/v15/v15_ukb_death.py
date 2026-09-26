"""v1.5 amendment (2026-09-26): UKB all-cause death outcome dirs claude-v15d-ukb-<trial>-death.

Cohort = main-dir eligibility (v15_ukb_build.cohort) but index visits allowed up to DEATH_END - 180 d, where
death follow-up censored at 2024-06-30 (July 2024 registration incomplete); index visits to 2023-12-31. Primary t/e = all-cause death strictly after index, censored at
min(trial horizon, DEATH_END). NCOs (hospital first occurrences) stay censored at the hospital data end 2022-10-31;
participants with index on/after that date are NaN for NCOs (no hospital follow-up). ECG linked from the pooled BCL
embeddings (instance 2); CLMBR via v15_ukb_build.clmbr. Existing dirs are not touched. Aggregates only.
Usage: python v15_ukb_death.py [trial ...]
"""
import json
import os
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v15_ukb_build as V
from v15_ukb_common import AUDIT, DATA_CSV, NCO

os.umask(0o077)
HOSP_END = V.END
TRIALS = ["ontarget", "allhat", "ascot"]
DEATH_CENSOR = pd.Timestamp("2024-06-30")  # death follow-up censoring (last complete month of registration)
INDEX_END = pd.Timestamp("2024-01-01")     # exclusive: index visits up to 2023-12-31
sup = V.sup


def death_end():
    r = duckdb.connect().execute(f"""select max(greatest(coalesce(p40000_i0, ''), coalesce(p40000_i1, '')))
        from read_csv_auto('{DATA_CSV}', all_varchar=true, sample_size=-1)""").fetchall()[0][0]
    return pd.Timestamp(r)


def main(trials):
    max_death = death_end()
    DE = DEATH_CENSOR  # coordinator decision: last complete registration month (July 2024 incomplete)
    for trial in trials:  # rebuild in place: remove markers first
        for m in ("READY_COHORT", "READY_ECG", "READY_OUTCOMES"):
            (Path(AUDIT) / f"claude-v15d-ukb-{trial}-death" / m).unlink(missing_ok=True)
    V.MODE.update(dir_fmt="claude-v15d-ukb-{trial}-death", index_end=INDEX_END,
                  index_end_label="visits to 2023-12-31, >= 180 d possible death follow-up")
    V.cohort(trials)
    V.link_ecg(trials)
    V.clmbr(trials)
    base, dx, _, _ = V.load()
    dx["eid"] = dx.eid.astype(str)
    dx["date"] = pd.to_datetime(dx.date)
    b = V.prep_base(base)
    for trial in trials:
        d = V.outdir(trial)
        if not (d / "READY_COHORT").exists():
            continue
        rct = json.load(open(d / "rct.json"))
        H = rct["horizon_days"]
        rct.update(endpoint="all-cause death", hr=None, lo=None, hi=None, our_orientation=None, benchmark_pending=True,
                   notes=rct["notes"].split(" Horizon ")[0] + f" Death amendment: all-cause death (40000) to {DE.date()}; "
                         f"horizon {H} d; benchmark to be filled with the verified all-cause mortality HR.")
        rct.pop("secondary", None)
        json.dump(rct, open(d / "rct.json", "w"), indent=1)
        coh = pd.read_parquet(d / "cohort.parquet")
        c = b.loc[coh.pid].copy()
        tr = coh.treated.values == 1
        idx = c.index_date
        end = pd.concat([pd.Series(DE, index=c.index), idx + pd.Timedelta(days=H)], axis=1).min(axis=1)
        dth = c.death_date
        e = (dth.notna() & (dth > idx) & (dth <= end)).astype(int).values
        t = np.where(e == 1, (dth - idx).dt.days, (end - idx).dt.days).astype(float)
        t = np.where(t <= 0, 0.5, t)
        out = pd.DataFrame({"pid": c.index.astype(str), "t": t, "e": e})
        # NCOs as in the main dir: hospital first occurrences, censored at min(death, HOSP_END, horizon)
        dd = dx[dx.eid.isin(c.index)].join(idx, on="eid")
        nend = pd.concat([pd.Series(HOSP_END, index=c.index), dth.where(dth <= HOSP_END), idx + pd.Timedelta(days=H)], axis=1).min(axis=1)
        late = (idx >= HOSP_END).values
        ncos = {}
        for nm, codes in NCO.items():
            sel = dd[dd.code.str.startswith(tuple(codes))]
            prev = c.index.isin(sel[sel.date <= sel.index_date].eid.unique())
            first = sel[sel.date > sel.index_date].groupby("eid").date.min().reindex(c.index)
            ne = (first.notna() & (first <= nend)).astype(int).values
            nt = np.where(ne == 1, (first - idx).dt.days, (nend - idx).dt.days).astype(float)
            nt = np.where(nt <= 0, 0.5, nt)
            na = prev | late
            out[f"t_nco_{nm}"] = np.where(na, np.nan, nt)
            out[f"e_nco_{nm}"] = np.where(na, np.nan, ne.astype(float))
            ok = ~na
            ncos[nm] = dict(n_at_risk=sup(ok.sum()), events=[sup(ne[ok & tr].sum()), sup(ne[ok & ~tr].sum())])
        out.to_parquet(d / "outcomes.parquet", index=False)
        ecg = set(pd.read_parquet(d / "ecg_embedding.parquet", columns=["pid"]).pid.astype(str))
        he = out.pid.isin(ecg).values
        fu = lambda m: [round(float(np.median(out.t[m])) / 365.25, 2), round(float(np.percentile(out.t[m], 25)) / 365.25, 2),
                        round(float(np.percentile(out.t[m], 75)) / 365.25, 2)]
        summ = json.load(open(d / "summary.json"))
        summ["death_amendment"] = dict(
            max_death_date_in_data=str(max_death.date()), death_censor_date=str(DE.date()), index_visits_up_to="2023-12-31",
            calendar_overlap_index_year_by_arm={str(y): [sup(((c.index_year == y).values & tr).sum()), sup(((c.index_year == y).values & ~tr).sum())]
                                                for y in sorted(c.index_year.unique())},
            reincluded_index_after_hospital_end=[sup((late & tr).sum()), sup((late & ~tr).sum())],
            n_arm=[sup(tr.sum()), sup((~tr).sum())], n_arm_with_ecg=[sup((tr & he).sum()), sup((~tr & he).sum())],
            horizon_days=H, deaths=[sup(out.e[tr].sum()), sup(out.e[~tr].sum())],
            deaths_with_ecg=[sup(out.e[tr & he].sum()), sup(out.e[~tr & he].sum())],
            followup_years_median_iqr=dict(first=fu(tr), second=fu(~tr)), nco=ncos,
            notes=[f"max 40000 date in data.csv is {max_death.date()}, but July 2024 is partially recorded (79 deaths vs "
                   "~440-520 in prior months); death follow-up censored at 2024-06-30 (coordinator decision, logged before results)",
                   "calendar_overlap_index_year_by_arm: [first arm, second arm] counts per index year",
                   "primary: all-cause death strictly after index, censored at min(horizon, death data end)",
                   f"index visits up to 2023-12-31 (>= 181 d possible follow-up); those after the hospital data end {HOSP_END.date()} have "
                   "truncated hospital covariate history (ICD-10 up to 2022-10-31 only) and NaN NCOs",
                   "NCOs: hospital first occurrences censored at min(death, 2022-10-31, horizon); prevalent cases NaN",
                   V.ECG_ON_TREATMENT])
        json.dump(summ, open(d / "summary.json", "w"), indent=1, default=str)
        (d / "READY_OUTCOMES").write_text("ok\n")
        print(d.name, json.dumps(summ["death_amendment"], default=str)[:900])


if __name__ == "__main__":
    main(sys.argv[1:] or TRIALS)
