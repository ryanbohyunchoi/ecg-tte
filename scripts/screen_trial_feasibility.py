#!/usr/bin/env python
"""Aggregate-only feasibility screen for active-comparator CV trial emulations.

For each candidate trial, computes (aggregate counts only):
  1. new users per arm: first-ever order of an arm drug within the index window,
     no order of either arm drug in the 365 days before (or on) index, age >= 18,
     and >= 365 days of prior EHR activity (earliest visit_occurrence <= index-365).
     Persons eligible in both arms are kept once, at their earliest index.
  2. final n per arm after the ICD-10 disease gate (condition on/before index).
  3. fraction with >= 1 ECG in [index-365, index] and [index-90, index]
     (plus a strict variant excluding the index day).
  4. fraction with a plausible echo EF (5-90%) in [index-365, index].
  5. all-cause deaths in (index, index+1095d], POOLED across arms only.

No patient-level rows are written or printed. Counts 1..(min_cell-1) are
suppressed in the CSV output.

Drug matching: lower(drug_source_value) is split on '-' and an exposure matches
an arm if any token equals one of the arm's (lower-cased) keywords. In the gold
OMOP build drug_source_value is the first word of the order name (ingredient or
brand, combination products hyphenated), so formulation (e.g. metoprolol
tartrate vs succinate) cannot be distinguished.
"""
import argparse
import os
import sys

import duckdb
import pandas as pd

ASCVD = ["I20", "I21", "I22", "I23", "I24", "I25", "I63", "I65", "I66", "I70",
         "I739", "Z951", "Z955", "Z9861"]

# gate: list of alternatives (OR) of conjunctions (AND) of flag names.
# Flags: hf, af, t2d, ascvd, ckd (any time on/before index), acs30 (I21/I24 in 30d)
TRIALS = [
    dict(key="comet", name="COMET", hr=0.83, gate=[["hf"]],
         arms=[("carvedilol", ["carvedilol", "coreg"]),
               ("metoprolol", ["metoprolol", "lopressor", "toprol"])],
         note="metoprolol formulation (tartrate) not identifiable"),
    dict(key="paradigm_hf", name="PARADIGM-HF", hr=0.80, gate=[["hf"]],
         arms=[("sacubitril_valsartan", ["sacubitril", "entresto"]),
               ("acei", ["enalapril", "vasotec", "lisinopril", "zestril", "prinivil"])],
         note="ACEi arm = enalapril/lisinopril (archived config; IV enalaprilat excluded)"),
    dict(key="aristotle", name="ARISTOTLE", hr=0.79, gate=[["af"]],
         arms=[("apixaban", ["apixaban", "eliquis"]),
               ("warfarin", ["warfarin", "coumadin", "jantoven"])]),
    dict(key="rely", name="RE-LY", hr=0.66, gate=[["af"]],
         arms=[("dabigatran", ["dabigatran", "pradaxa"]),
               ("warfarin", ["warfarin", "coumadin", "jantoven"])],
         note="published HR = dabigatran 150 mg stroke/SE"),
    dict(key="rocket_af", name="ROCKET-AF", hr=0.79, gate=[["af"]],
         arms=[("rivaroxaban", ["rivaroxaban", "xarelto"]),
               ("warfarin", ["warfarin", "coumadin", "jantoven"])]),
    dict(key="empa_reg", rct_control="placebo", name="EMPA-REG", hr=0.86, gate=[["t2d", "ascvd"]],
         arms=[("empagliflozin", ["empagliflozin", "jardiance", "synjardy", "glyxambi", "trijardy"]),
               ("dpp4i", ["sitagliptin", "januvia", "janumet", "saxagliptin", "onglyza",
                          "kombiglyze", "linagliptin", "tradjenta", "jentadueto",
                          "alogliptin", "nesina", "kazano", "vildagliptin"])]),
    dict(key="declare", rct_control="placebo", name="DECLARE-TIMI58", hr=0.83, gate=[["t2d"]],
         arms=[("dapagliflozin", ["dapagliflozin", "farxiga", "forxiga", "xigduo", "qtern"]),
               ("dpp4i", ["sitagliptin", "januvia", "janumet", "saxagliptin", "onglyza",
                          "kombiglyze", "linagliptin", "tradjenta", "jentadueto",
                          "alogliptin", "nesina", "kazano", "vildagliptin"])],
         note="HR = HF hosp/CV death co-primary"),
    dict(key="canvas", rct_control="placebo", name="CANVAS", hr=0.86, gate=[["t2d"]],
         arms=[("canagliflozin", ["canagliflozin", "invokana", "invokamet"]),
               ("dpp4i", ["sitagliptin", "januvia", "janumet", "saxagliptin", "onglyza",
                          "kombiglyze", "linagliptin", "tradjenta", "jentadueto",
                          "alogliptin", "nesina", "kazano", "vildagliptin"])]),
    dict(key="leader", rct_control="placebo", name="LEADER", hr=0.87, gate=[["t2d", "ascvd"], ["t2d", "hf"], ["t2d", "ckd"]],
         arms=[("liraglutide", ["liraglutide", "victoza", "saxenda", "xultophy"]),
               ("dpp4i", ["sitagliptin", "januvia", "janumet", "saxagliptin", "onglyza",
                          "kombiglyze", "linagliptin", "tradjenta", "jentadueto",
                          "alogliptin", "nesina", "kazano", "vildagliptin"])],
         note="saxenda (obesity dose) included per archived config"),
    dict(key="carolina", name="CAROLINA", hr=0.98, gate=[["t2d"]],
         arms=[("linagliptin", ["linagliptin", "tradjenta", "glyxambi", "jentadueto"]),
               ("glimepiride", ["glimepiride", "amaryl", "duetact"])]),
    dict(key="tecos", rct_control="placebo", name="TECOS", hr=0.98, gate=[["t2d", "ascvd"]],
         arms=[("sitagliptin", ["sitagliptin", "januvia", "janumet", "steglujan"]),
               ("sulfonylurea", ["glipizide", "glucotrol", "glimepiride", "amaryl",
                                 "glyburide", "glibenclamide", "tolbutamide"])],
         note="RCT was placebo-controlled; SU comparator is an active-comparator proxy"),
    dict(key="savor", rct_control="placebo", name="SAVOR-TIMI53", hr=1.00, gate=[["t2d"]],
         arms=[("saxagliptin", ["saxagliptin", "onglyza", "kombiglyze", "qtern"]),
               ("sulfonylurea", ["glipizide", "glucotrol", "glimepiride", "amaryl",
                                 "glyburide", "glibenclamide", "tolbutamide"])],
         note="RCT was placebo-controlled; SU comparator is an active-comparator proxy"),
    dict(key="plato", name="PLATO", hr=0.84, gate=[["acs30"]],
         arms=[("ticagrelor", ["ticagrelor", "brilinta"]),
               ("clopidogrel", ["clopidogrel", "plavix"])]),
    dict(key="triton", name="TRITON-TIMI38", hr=0.81, gate=[["acs30"]],
         arms=[("prasugrel", ["prasugrel", "effient"]),
               ("clopidogrel", ["clopidogrel", "plavix"])],
         note="PCI requirement not applied"),
    dict(key="ontarget", name="ONTARGET", hr=1.01, gate=[["ascvd"], ["t2d"]],
         arms=[("telmisartan", ["telmisartan", "micardis", "twynsta"]),
               ("ramipril", ["ramipril", "altace"])],
         note="TRANSCEND is placebo-controlled and not separately screened"),
]

GATE_CODES = {"hf": ["I50"], "af": ["I48"], "t2d": ["E11"], "ckd": ["N18"], "ascvd": ASCVD}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--omop-dir", required=True, help="OMOP gold root with person/, drug_exposure/, ...")
    p.add_argument("--ecg-metadata", required=True)
    p.add_argument("--echo-metadata", required=True)
    p.add_argument("--out-csv", required=True)
    p.add_argument("--index-start", default="2013-01-01")
    p.add_argument("--index-end", default="2024-06-30")
    p.add_argument("--washout-days", type=int, default=365)
    p.add_argument("--prior-activity-days", type=int, default=365)
    p.add_argument("--min-age", type=int, default=18)
    p.add_argument("--followup-days", type=int, default=1095)
    p.add_argument("--death-data-end", default="2024-12-31",
                   help="assumed end of reliable death capture (for full-window count)")
    p.add_argument("--min-cell", type=int, default=11, help="suppress counts 1..min_cell-1")
    p.add_argument("--rank-min-n", type=int, default=300)
    p.add_argument("--rank-ecg90", type=float, default=0.70)
    p.add_argument("--threads", type=int, default=32)
    p.add_argument("--trials", nargs="*", default=None, help="subset of trial keys")
    return p.parse_args()


def mrn_key(col):
    # digits only, strip leading zeros; empty -> NULL
    return f"nullif(ltrim(regexp_replace({col}, '[^0-9]', '', 'g'), '0'), '')"


def main():
    a = parse_args()
    os.umask(0o077)
    trials = [t for t in TRIALS if a.trials is None or t["key"] in a.trials]
    G = a.omop_dir.rstrip("/")
    con = duckdb.connect()
    con.execute(f"SET threads={a.threads}")
    rp = lambda t: f"read_parquet('{G}/{t}/*/*.parquet', hive_partitioning=1)"

    # --- person + key
    con.execute(f"""create temp table person as
        select person_id, cast(birth_datetime as date) dob, {mrn_key('person_source_value')} k
        from read_parquet('{G}/person/*.parquet')""")

    # --- arm keyword map
    rows = []
    for t in trials:
        for i, (arm, kws) in enumerate(t["arms"]):
            for kw in kws:
                rows.append((t["key"], i, arm, kw.lower()))
    con.register("kwmap_df", pd.DataFrame(rows, columns=["trial", "arm_idx", "arm", "kw"]))
    con.execute("create temp table kwmap as select * from kwmap_df")
    kwlist = sorted({r[3] for r in rows})
    kw_sql = ",".join(f"'{k}'" for k in kwlist)

    # --- drug exposure rows for any arm keyword (token match)
    con.execute(f"""create temp table dtok as
        select distinct person_id, drug_exposure_start_date d, tok
        from (select person_id, drug_exposure_start_date,
                     unnest(string_split(lower(drug_source_value), '-')) tok
              from {rp('drug_exposure')}
              where drug_source_value is not null)
        where tok in ({kw_sql}) and drug_exposure_start_date is not null""")
    con.execute("""create temp table armexp as
        select distinct k.trial, k.arm_idx, d.person_id, d.d
        from dtok d join kwmap k on d.tok = k.kw""")

    # --- first-ever per trial-arm within window
    con.execute(f"""create temp table first_use as
        select trial, arm_idx, person_id, min(d) idx from armexp group by 1,2,3""")
    con.execute(f"""create temp table cand0 as select * from first_use
        where idx between date '{a.index_start}' and date '{a.index_end}'""")

    # washout: no comparator exposure in [idx-washout, idx]
    con.execute(f"""create temp table cand1 as
        select c.* from cand0 c
        where not exists (select 1 from armexp e
            where e.trial=c.trial and e.person_id=c.person_id and e.arm_idx<>c.arm_idx
              and e.d between c.idx - interval {a.washout_days} day and c.idx)""")

    # age + prior activity
    con.execute(f"""create temp table firstvisit as
        select person_id, min(visit_start_date) fv from {rp('visit_occurrence')} group by 1""")
    con.execute(f"""create temp table cand2 as
        select c.*, p.k from cand1 c
        join person p using (person_id)
        join firstvisit v using (person_id)
        where p.dob is not null and date_diff('year', p.dob, c.idx) -
              (case when strftime(c.idx,'%m%d') < strftime(p.dob,'%m%d') then 1 else 0 end) >= {a.min_age}
          and v.fv <= c.idx - interval {a.prior_activity_days} day""")
    # dedupe persons eligible in both arms -> earliest index
    con.execute("""create temp table cand as
        select * from (select *, row_number() over (partition by trial, person_id order by idx, arm_idx) rn
                       from cand2) where rn=1""")
    overlap = con.execute("""select trial, count(*) from
        (select trial, person_id from cand2 group by 1,2 having count(*)>1) group by 1""").df()
    overlap = dict(zip(overlap.iloc[:, 0], overlap.iloc[:, 1]))

    # --- condition flags
    allcodes = sorted({c for v in GATE_CODES.values() for c in v})
    likes = " or ".join(f"code like '{c}%'" for c in allcodes)
    con.execute(f"""create temp table cond as
        select person_id, condition_start_date d, code from
          (select person_id, condition_start_date,
                  upper(replace(condition_source_value, '.', '')) code
           from {rp('condition_occurrence')}
           where person_id in (select distinct person_id from cand))
        where ({likes}) and condition_start_date is not null""")
    flag_exprs = []
    for f, codes in GATE_CODES.items():
        cl = " or ".join(f"x.code like '{c}%'" for c in codes)
        flag_exprs.append(f"max(case when ({cl}) and x.d <= c.idx then 1 else 0 end) {f}")
    flag_exprs.append("max(case when (x.code like 'I21%' or x.code like 'I24%') "
                      "and x.d between c.idx - interval 30 day and c.idx then 1 else 0 end) acs30")
    con.execute(f"""create temp table flags as
        select c.trial, c.person_id, {', '.join(flag_exprs)}
        from cand c join cond x using (person_id) group by 1,2""")

    # --- ECG / echo / death
    con.execute(f"""create temp table ecg as select distinct {mrn_key('MRN')} k, try_cast(ECGDate as date) d
        from read_parquet('{a.ecg_metadata}') where try_cast(ECGDate as date) is not null""")
    con.execute(f"""create temp table echo as select distinct {mrn_key('MRN')} k, try_cast(EchoDate as date) d
        from read_parquet('{a.echo_metadata}')
        where try_cast(EchoDate as date) is not null and EF between 5 and 90""")
    con.execute(f"""create temp table death as select person_id, min(death_date) dd
        from {rp('death')} group by 1""")

    con.execute(f"""create temp table cohort as
        select c.trial, c.arm_idx, c.person_id, c.idx,
          coalesce(f.hf,0) hf, coalesce(f.af,0) af, coalesce(f.t2d,0) t2d, coalesce(f.ckd,0) ckd,
          coalesce(f.ascvd,0) ascvd, coalesce(f.acs30,0) acs30,
          exists(select 1 from ecg e where e.k=c.k and e.d between c.idx - interval 365 day and c.idx) ecg365,
          exists(select 1 from ecg e where e.k=c.k and e.d between c.idx - interval 90 day and c.idx) ecg90,
          exists(select 1 from ecg e where e.k=c.k and e.d between c.idx - interval 90 day and c.idx - interval 1 day) ecg90_strict,
          exists(select 1 from echo e where e.k=c.k and e.d between c.idx - interval 365 day and c.idx) echo365,
          (d.dd > c.idx and d.dd <= c.idx + interval {a.followup_days} day) death3y,
          (d.dd <= c.idx) death_before,
          (c.idx + interval {a.followup_days} day <= date '{a.death_data_end}') full_window
        from cand c left join flags f on f.trial=c.trial and f.person_id=c.person_id
        left join death d on d.person_id=c.person_id""")
    coh = con.execute("""select trial, arm_idx, hf, af, t2d, ckd, ascvd, acs30,
            ecg365::int ecg365, ecg90::int ecg90, ecg90_strict::int ecg90_strict, echo365::int echo365,
            coalesce(death3y,false)::int death3y, coalesce(death_before,false)::int death_before,
            full_window::int full_window, count(*) n
        from cohort group by all""").df()
    stage_counts = {}
    for nm in ["cand0", "cand1", "cand2", "cand"]:
        df = con.execute(f"select trial, arm_idx, count(*) n from {nm} group by 1,2").df()
        stage_counts[nm] = {(r.trial, r.arm_idx): int(r.n) for r in df.itertuples()}

    def sup(n):
        return n if (n == 0 or n >= a.min_cell) else f"<{a.min_cell}"

    out = []
    for t in trials:
        sub = coh[coh.trial == t["key"]].copy()
        gate = pd.Series(False, index=sub.index)
        for conj in t["gate"]:
            g = pd.Series(True, index=sub.index)
            for f in conj:
                g &= sub[f] == 1
            gate |= g
        sub["gate"] = gate
        fin_all = sub[sub.gate]
        gate_str = " OR ".join("+".join(c) for c in t["gate"])
        for i, (arm, kws) in enumerate(t["arms"]):
            s = sub[sub.arm_idx == i]
            fn = fin_all[fin_all.arm_idx == i]
            nu = int(s.n.sum()); nf = int(fn.n.sum())
            w = lambda col: (fn[col] * fn.n).sum() / nf if nf else float("nan")
            out.append(dict(
                trial=t["name"], trial_key=t["key"], arm=arm, role="treated" if i == 0 else "comparator",
                published_hr=t["hr"], disease_gate=gate_str,
                n_first_use_in_window=sup(stage_counts["cand0"].get((t["key"], i), 0)),
                n_after_washout=sup(stage_counts["cand1"].get((t["key"], i), 0)),
                n_after_age_prior_activity=sup(stage_counts["cand2"].get((t["key"], i), 0)),
                n_new_users=sup(nu),
                frac_gate=round(nf / nu, 3) if nu else None,
                n_final=sup(nf),
                frac_ecg_365d=round(w("ecg365"), 3), frac_ecg_90d=round(w("ecg90"), 3),
                frac_ecg_90d_excl_index_day=round(w("ecg90_strict"), 3),
                frac_echo_ef_365d=round(w("echo365"), 3),
                frac_ckd_n18=round(w("ckd"), 3),
                rct_control=t.get("rct_control", "active"),
                deaths_3y_pooled=None, n_pooled_full_3y_window=None, deaths_on_or_before_index_pooled=None,
                n_both_arm_eligible_dedup=None, note=t.get("note", "")))
        nfp = int(fin_all.n.sum())
        out.append(dict(
            trial=t["name"], trial_key=t["key"], arm="POOLED", role="pooled", published_hr=t["hr"],
            disease_gate=gate_str, n_new_users=sup(int(sub.n.sum())), n_final=sup(nfp),
            frac_gate=round(nfp / sub.n.sum(), 3) if sub.n.sum() else None,
            frac_ecg_365d=round((fin_all.ecg365 * fin_all.n).sum() / nfp, 3) if nfp else None,
            frac_ecg_90d=round((fin_all.ecg90 * fin_all.n).sum() / nfp, 3) if nfp else None,
            frac_ecg_90d_excl_index_day=round((fin_all.ecg90_strict * fin_all.n).sum() / nfp, 3) if nfp else None,
            frac_echo_ef_365d=round((fin_all.echo365 * fin_all.n).sum() / nfp, 3) if nfp else None,
            frac_ckd_n18=round((fin_all.ckd * fin_all.n).sum() / nfp, 3) if nfp else None,
            rct_control=t.get("rct_control", "active"),
            deaths_3y_pooled=sup(int((fin_all.death3y * fin_all.n).sum())),
            n_pooled_full_3y_window=sup(int((fin_all.full_window * fin_all.n).sum())),
            deaths_on_or_before_index_pooled=sup(int((fin_all.death_before * fin_all.n).sum())),
            n_both_arm_eligible_dedup=sup(int(overlap.get(t["key"], 0))), note=t.get("note", "")))
    res = pd.DataFrame(out)
    os.makedirs(os.path.dirname(os.path.abspath(a.out_csv)), exist_ok=True)
    res.to_csv(a.out_csv, index=False)
    # ranking: criteria = min-arm final n >= min_n, pooled ECG-90d >= ecg_thr, published HR exists
    rk = []
    for t in trials:
        r = res[res.trial_key == t["key"]]
        arms = r[r.role != "pooled"]; pool = r[r.role == "pooled"].iloc[0]
        nmin = pd.to_numeric(arms.n_final, errors="coerce").fillna(0).min()
        e_pool = pool.frac_ecg_90d; e_min = arms.frac_ecg_90d.min()
        crit = int(nmin >= a.rank_min_n) + int(e_pool >= a.rank_ecg90) + int(t["hr"] is not None)
        rk.append(dict(trial=t["name"], rct_control=t.get("rct_control", "active"), published_hr=t["hr"],
                       min_arm_n_final=int(nmin), pooled_n_final=pool.n_final,
                       pooled_ecg90=e_pool, min_arm_ecg90=e_min, pooled_echo365=pool.frac_echo_ef_365d,
                       deaths_3y_pooled=pool.deaths_3y_pooled,
                       pass_n=nmin >= a.rank_min_n, pass_ecg90_pooled=e_pool >= a.rank_ecg90,
                       pass_ecg90_all_arms=e_min >= a.rank_ecg90, criteria_met=crit))
    rk = pd.DataFrame(rk).sort_values(["criteria_met", "pass_ecg90_all_arms", "pooled_ecg90", "min_arm_ecg90"],
                                      ascending=False).reset_index(drop=True)
    rk.insert(0, "rank", range(1, len(rk) + 1))
    rk_path = os.path.splitext(a.out_csv)[0] + "_ranked.csv"
    rk.to_csv(rk_path, index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(rk.to_string(index=False))
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(res[["trial", "arm", "n_new_users", "frac_gate", "n_final", "frac_ecg_365d",
                   "frac_ecg_90d", "frac_echo_ef_365d", "deaths_3y_pooled"]].to_string(index=False))
    print(f"wrote {a.out_csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
