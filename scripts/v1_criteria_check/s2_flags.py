#!/usr/bin/env python
"""Step 2: per-patient criterion flags for the 17 flagged trials (restricted: OUT/flags/restricted_flags_<n>.parquet)
and aggregate counts (OUT/criteria_counts.csv, counts 1-10 suppressed; OUT/life_lvh_categories.csv).

Data read (read-only): analysed keys from step 1; OMOP gold (drug_exposure tokens exactly as
trial_common.create_drug_tokens, condition_occurrence, procedure_occurrence, visit_occurrence, person); echo metadata EF
(as build_trial_cohort.py); ECG metadata Diagnosis (LIFE only, as the LIFE cohort gate; only category counts written);
COMET JDAT medication buckets (restricted_candidates.sqlite medication_evidence, written by build_comet_candidates.py);
outcome files (AMPLIFY, LODESTAR, PROVE IT). Nothing patient-level is printed.

Fix flags (column prefix fx_) mark analysed patients a proposed exclusion would remove.
"""
import re
import sqlite3
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v1_criteria_check")
import common as K  # noqa: E402
from trial_common import code_like, connect, mrn_key, rp, sql_list  # noqa: E402
from trial_specs import (ANTIARRHYTHMIC, CABG_CODES, GLP1RA, HORIZON_MONTHS, PCI_CODES, PRIMARY_BILLING,  # noqa: E402
                         SGLT2_ALL)

G = K.GOLD
AF_ABLATION = ["93656", "02573ZZ", "025S3ZZ", "025T3ZZ"]
AAD = ANTIARRHYTHMIC + ["multaq", "pacerone", "tikosyn", "betapace", "rythmol", "tambocor"]
ARNI = ["sacubitril", "entresto"]
SAXALO = ["saxagliptin", "onglyza", "kombiglyze", "alogliptin", "nesina", "kazano"]
SITALINA = ["sitagliptin", "januvia", "janumet", "linagliptin", "tradjenta", "jentadueto"]
OTHER_GLP1 = {"leader": [g for g in GLP1RA if g not in ("liraglutide", "victoza")],
              "sustain6": [g for g in GLP1RA if g not in ("semaglutide", "ozempic", "rybelsus")],
              "rewind": [g for g in GLP1RA if g not in ("dulaglutide", "trulicity")]}
OTHER_SGLT2 = {"declare": [s for s in SGLT2_ALL if s not in ("dapagliflozin", "farxiga", "xigduo", "qtern")],
               "canvas": [s for s in SGLT2_ALL if s not in ("canagliflozin", "invokana", "invokamet")]}
VTE = ["I26", "I801", "I802", "I824"]


def setup(n):
    D = pd.read_parquet(K.OUT / "keys" / f"restricted_keys_{n}.parquet")
    con = connect(8, "60GB")
    con.register("k0", D[["patient_key", "person_id", "treated", "index_date"]])
    con.execute("CREATE TEMP TABLE k AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, treated, CAST(index_date AS DATE) idx FROM k0")
    return D, con


def tokens(con, kws, table="tok"):
    kw = sql_list(sorted({x.lower() for x in kws}))
    con.execute(f"""CREATE OR REPLACE TEMP TABLE {table} AS SELECT DISTINCT person_id, d, tok, src FROM (
        SELECT person_id, drug_exposure_start_date d, lower(drug_source_value) src,
               unnest(string_split(lower(drug_source_value), '-')) tok
        FROM {rp(G, 'drug_exposure')} WHERE drug_source_value IS NOT NULL AND drug_exposure_start_date IS NOT NULL
          AND person_id IN (SELECT person_id FROM k)) WHERE tok IN ({kw})""")


def drug_window(con, kws, lo, hi, name):
    """flag: any token of kws in [idx+lo, idx+hi] days."""
    tokens(con, kws, "tw")
    s = con.execute(f"""SELECT k.patient_key, bool_or(t.d BETWEEN k.idx + INTERVAL ({lo}) DAY AND k.idx + INTERVAL ({hi}) DAY) f
        FROM k LEFT JOIN tw t USING (person_id) GROUP BY 1""").df().set_index("patient_key").f
    return s.fillna(False).astype(bool).rename(name)


def stays(con):
    con.execute(f"""CREATE OR REPLACE TEMP TABLE iv AS SELECT v.person_id, v.visit_start_date s, coalesce(v.visit_end_date, v.visit_start_date) e
        FROM {rp(G, 'visit_occurrence')} v WHERE v.visit_concept_id = 9201 AND v.person_id IN (SELECT person_id FROM k)""")
    con.execute("""CREATE OR REPLACE TEMP TABLE stays AS
        WITH o AS (SELECT *, max(e) OVER (PARTITION BY person_id ORDER BY s, e ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) pe FROM iv),
             g AS (SELECT *, sum(CASE WHEN pe IS NULL OR s > pe + INTERVAL 1 DAY THEN 1 ELSE 0 END)
                            OVER (PARTITION BY person_id ORDER BY s, e ROWS UNBOUNDED PRECEDING) gid FROM o)
        SELECT person_id, gid, min(s) s, max(e) e FROM g GROUP BY 1, 2""")
    con.execute("""CREATE OR REPLACE TEMP TABLE idxstay AS SELECT k.patient_key, k.person_id, k.idx,
            max(st.s) FILTER (WHERE st.s <= k.idx AND st.e >= k.idx) stay_s,
            coalesce(max(st.e) FILTER (WHERE st.s <= k.idx AND st.e >= k.idx), k.idx) idx_stay_end
        FROM k LEFT JOIN stays st USING (person_id) GROUP BY 1, 2, 3""")


def latest_ef(con, lo_days, hi_days):
    """latest echo EF (5-90) in [idx-lo, idx-hi] (arg_max by date then value, as build_trial_cohort.py)."""
    con.execute(f"""CREATE OR REPLACE TEMP TABLE pk AS SELECT person_id, {mrn_key('person_source_value')} kk FROM {rp(G, 'person')}
        WHERE person_id IN (SELECT person_id FROM k)""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE echo AS SELECT {mrn_key('MRN')} kk, try_cast(EchoDate AS DATE) d, EF
        FROM read_parquet('{K.ECHO_META}') WHERE EF BETWEEN 5 AND 90 AND try_cast(EchoDate AS DATE) IS NOT NULL""")
    return con.execute(f"""SELECT k.patient_key, arg_max(e.EF, (e.d, e.EF)) ef FROM k JOIN pk USING (person_id) JOIN echo e ON e.kk = pk.kk
        WHERE e.d BETWEEN k.idx - INTERVAL {lo_days} DAY AND k.idx - INTERVAL {hi_days} DAY GROUP BY 1""").df().set_index("patient_key").ef


def cond_first(con, codes):
    return con.execute(f"""SELECT k.patient_key, min(c.condition_start_date) d FROM k JOIN {rp(G, 'condition_occurrence')} c USING (person_id)
        WHERE c.condition_start_date IS NOT NULL AND {code_like("upper(replace(c.condition_source_value, '.', ''))", codes)}
        GROUP BY 1""").df().set_index("patient_key").d


def any_cond_on_before(con, codes):
    return con.execute(f"""SELECT DISTINCT k.patient_key FROM k JOIN {rp(G, 'condition_occurrence')} c USING (person_id)
        WHERE c.condition_start_date <= k.idx AND {code_like("upper(replace(c.condition_source_value, '.', ''))", codes)}""").df().patient_key


# ---------------------------------------------------------------- LIFE ECG-LVH statement categories
LVH_RX = re.compile(r"LVH|LEFT VENTRICULAR HYPERTROPHY")


def lvh_category(frag):
    f = frag
    if any(x in f for x in ("NO LONGER PRESENT", "NO LVH", "NO LEFT VENTRICULAR HYPERTROPHY", "NOT PRESENT", "NO LONGER", "RESOLVED",
                            "NO EVIDENCE OF LVH", "NO EVIDENCE OF LEFT", "WITHOUT LVH", "REPLACED")):
        return "negated_or_no_longer_present"
    if "NORMAL VARIANT" in f or "MINIMAL VOLTAGE" in f:
        return "minimal_voltage_or_normal_variant"
    if any(x in f for x in ("CANNOT RULE OUT", "CANNOT EXCLUDE", "POSSIBLE", "BORDERLINE", "R/O")):
        return "possible_or_cannot_rule_out"
    if re.search(r"(POSSIBLY|PROBABLY|MAY BE|LIKELY)\s+(DUE TO|SECONDARY TO|RELATED TO)\s+(LVH|LEFT VENTRICULAR)", f):
        return "other_finding_attributed_to_lvh"
    if "CONSIDER" in f or "SUGGEST" in f:
        return "consider"
    if "PROBABLE" in f:
        return "probable"
    if "VOLTAGE CRITERIA" in f or "VOLTAGE" in f:
        return "voltage_criteria"
    return "definite"


HEDGED_PRIMARY = {"negated_or_no_longer_present", "minimal_voltage_or_normal_variant", "possible_or_cannot_rule_out"}  # auditors A u B
HEDGED_STRICT = HEDGED_PRIMARY | {"other_finding_attributed_to_lvh", "consider"}


def life_flags(con, D):
    con.execute(f"""CREATE OR REPLACE TEMP TABLE pk AS SELECT person_id, {mrn_key('person_source_value')} kk FROM {rp(G, 'person')}
        WHERE person_id IN (SELECT person_id FROM k)""")
    E = con.execute(f"""SELECT k.patient_key, upper(e.Diagnosis) dx FROM read_parquet('{K.ECG_META}') e JOIN pk ON {mrn_key('e.MRN')} = pk.kk
        JOIN k USING (person_id) WHERE e.Diagnosis IS NOT NULL AND try_cast(e.ECGDate AS DATE) BETWEEN k.idx - INTERVAL 365 DAY AND k.idx
          AND (upper(e.Diagnosis) LIKE '%LEFT VENTRICULAR HYPERTROPHY%' OR upper(e.Diagnosis) LIKE '%LVH%')""").df()
    rows = []
    for pkey, dx in zip(E.patient_key, E.dx):
        cats = [lvh_category(f.strip()) for f in re.split(r"\s{2,}|\n|\r", dx) if LVH_RX.search(f)]
        rows += [(pkey, c) for c in (cats or ["definite"])]
    C = pd.DataFrame(rows, columns=["patient_key", "cat"])
    per = C.groupby("patient_key").cat.agg(set).reindex(D.patient_key)
    gate_ok = per.notna()
    only_primary = per.map(lambda s: isinstance(s, set) and s <= HEDGED_PRIMARY)
    only_strict = per.map(lambda s: isinstance(s, set) and s <= HEDGED_STRICT)
    # category frequencies: statements and patients (any statement of the category; patients whose best statement is the category)
    order = ["definite", "voltage_criteria", "probable", "consider", "other_finding_attributed_to_lvh",
             "possible_or_cannot_rule_out", "minimal_voltage_or_normal_variant", "negated_or_no_longer_present"]
    best = per.map(lambda s: min(s, key=order.index) if isinstance(s, set) else None)
    cat_rows = []
    for c in order:
        cat_rows.append(dict(category=c, statements=K.sup((C.cat == c).sum()), patients_any=K.sup(C[C.cat == c].patient_key.nunique()),
                             patients_best=K.sup((best == c).sum()), pct_patients_best=K.pct((best == c).sum(), len(D))))
    best = best.replace({"negated_or_no_longer_present": "possible_or_cannot_rule_out"})  # merged: negated cell is 1-10
    C = C.assign(cat=C.cat.replace({"negated_or_no_longer_present": "possible_or_cannot_rule_out"}))
    cat_rows = []
    for c in order[:-1]:
        lab = "possible_cannot_rule_out_or_negated" if c == "possible_or_cannot_rule_out" else c
        cat_rows.append(dict(category=lab, statements=K.sup((C.cat == c).sum()), patients_any=K.sup(C[C.cat == c].patient_key.nunique()),
                             patients_best=K.sup((best == c).sum()), pct_patients_best=K.pct((best == c).sum(), len(D))))
    pd.DataFrame(cat_rows).to_csv(K.OUT / "life_lvh_categories.csv", index=False)
    return pd.DataFrame({"life_gate_text_found": gate_ok.to_numpy(), "fx_life_hedged_primary": only_primary.to_numpy(),
                         "fx_life_hedged_strict": only_strict.to_numpy()}, index=D.patient_key)


# ---------------------------------------------------------------- per-trial
def run(n):
    K.umask()
    D, con = setup(n)
    idx = D.set_index("patient_key").index_date
    t = D.set_index("patient_key").treated
    F = pd.DataFrame(index=D.patient_key)
    if n == "comet":
        db = sqlite3.connect(f"file:{K.COMET_MED_SQLITE}?mode=ro", uri=True)
        M = pd.read_sql("SELECT patient, day, bucket FROM medication_evidence WHERE bucket IN "
                        "('metoprolol_succinate_review', 'metoprolol_tartrate_candidate', 'carvedilol_not_marked_extended_candidate', "
                        "'carvedilol_extended_review', 'metoprolol_unspecified_review')", db)
        M = M[M.patient.isin(set(D.patient_key))]
        M["day"] = pd.to_datetime(M.day)
        M["lag"] = (M.day - M.patient.map(idx)).dt.days
        for b, tag in (("metoprolol_succinate_review", "succ"), ("metoprolol_tartrate_candidate", "tart"),
                       ("carvedilol_not_marked_extended_candidate", "carv")):
            m = M[M.bucket == b]
            for lab, lo, hi in (("index_day", 0, 0), ("prior365", -365, -1), ("w365_incl_index", -365, 0), ("ever_before", -100000, -1),
                                ("post1_90", 1, 90)):
                F[f"jdat_{tag}_{lab}"] = F.index.isin(m[(m.lag >= lo) & (m.lag <= hi)].patient)
            F[f"jdat_{tag}_undated"] = F.index.isin(m[m.day.isna()].patient)
        F["omop_toprol_w365_incl_index"] = drug_window(con, ["toprol"], -365, 0, "x").reindex(F.index).to_numpy()
        F["omop_toprol_index_day"] = drug_window(con, ["toprol"], 0, 0, "x").reindex(F.index).to_numpy()
        F["omop_toprol_post1_90"] = drug_window(con, ["toprol"], 1, 90, "x").reindex(F.index).to_numpy()
        ef = latest_ef(con, 365, 1).reindex(F.index)
        F["ef_measured"] = ef.notna().to_numpy()
        F["ef_gt35"] = (ef > 35).to_numpy()
        F["ef_ge40"] = (ef >= 40).to_numpy()
        F["fx_comet_succinate"] = F.jdat_succ_w365_incl_index
        F["fx_comet_lvef35"] = F.ef_gt35
    if n in ("elite-ii", "valiant"):
        F["arni_w365_incl_index"] = drug_window(con, ARNI, -365, 0, "x").reindex(F.index).to_numpy()
        F["arni_index_day"] = drug_window(con, ARNI, 0, 0, "x").reindex(F.index).to_numpy()
        tokens(con, ["valsartan"], "vs")
        s = con.execute("""SELECT DISTINCT k.patient_key FROM k JOIN vs ON vs.person_id = k.person_id AND vs.d = k.idx
                           WHERE vs.src LIKE '%sacubitril%'""").df().patient_key
        F["sacval_string_index_day"] = F.index.isin(s)
        F["fx_arni"] = F.arni_w365_incl_index
    if n == "valiant":
        ef = latest_ef(con, 365, 0).reindex(F.index)  # index day included (auditor B)
        hf = set(any_cond_on_before(con, ["I50"]))
        F["ef_known_incl_index"] = ef.notna().to_numpy()
        F["ef_gt40_incl_index"] = (ef > 40).to_numpy()
        F["hf_code_on_before"] = F.index.isin(hf)
        F["ef_unknown_no_hf"] = (~F.ef_known_incl_index) & (~F.hf_code_on_before)
        F["fx_valiant_ef_hf"] = F.ef_unknown_no_hf | F.ef_gt40_incl_index
    if n in ("emperor-preserved-v2", "declare"):
        F["saxalo_w365_incl_index"] = drug_window(con, SAXALO, -365, 0, "x").reindex(F.index).to_numpy()
        F["saxalo_index_day"] = drug_window(con, SAXALO, 0, 0, "x").reindex(F.index).to_numpy()
        F["sitalina_index_day"] = drug_window(con, SITALINA, 0, 0, "x").reindex(F.index).to_numpy()
        F["index_dpp4_saxalo_only"] = F.saxalo_index_day & ~F.sitalina_index_day
        F["fx_saxalo"] = F.saxalo_w365_incl_index
    if n in OTHER_GLP1:
        F["other_glp1_w365_incl_index"] = drug_window(con, OTHER_GLP1[n], -365, 0, "x").reindex(F.index).to_numpy()
        F["other_glp1_prior365"] = drug_window(con, OTHER_GLP1[n], -365, -1, "x").reindex(F.index).to_numpy()
        F["fx_washout"] = F.other_glp1_w365_incl_index
    if n in OTHER_SGLT2:
        F["other_sglt2_w365_incl_index"] = drug_window(con, OTHER_SGLT2[n], -365, 0, "x").reindex(F.index).to_numpy()
        F["other_sglt2_prior365"] = drug_window(con, OTHER_SGLT2[n], -365, -1, "x").reindex(F.index).to_numpy()
        F["fx_washout"] = F.other_sglt2_w365_incl_index
    if n == "declare":
        F["fx_declare_both"] = F.fx_washout | F.fx_saxalo
    if n == "carolina":
        a = con.execute(f"""SELECT k.patient_key, date_diff('year', CAST(p.birth_datetime AS DATE), k.idx)
              - (CASE WHEN strftime(k.idx, '%m%d') < strftime(CAST(p.birth_datetime AS DATE), '%m%d') THEN 1 ELSE 0 END) age
            FROM k JOIN {rp(G, 'person')} p USING (person_id)""").df().set_index("patient_key").age.reindex(F.index)
        F["age_lt40"] = (a < 40).to_numpy()
        F["age_gt85"] = (a > 85).to_numpy()
        F["fx_carolina_age"] = F.age_lt40 | F.age_gt85
    if n == "laaos3":
        stays(con)
        st = con.execute("SELECT patient_key, stay_s FROM idxstay").df().set_index("patient_key").stay_s.reindex(F.index)
        fa = pd.to_datetime(cond_first(con, ["I48"]).reindex(F.index))
        st = pd.to_datetime(st)
        F["index_in_inpatient_stay"] = st.notna().to_numpy()
        anchor = st.fillna(idx)  # no stay containing the index date -> the index date
        F["first_af_in_index_stay"] = (fa >= anchor).to_numpy()
        F["first_af_ge_idx_minus1"] = (fa >= idx - pd.Timedelta(days=1)).to_numpy()
        F["fx_laaos3_postop_af"] = F.first_af_in_index_stay
    if n == "life":
        F = F.join(life_flags(con, D))
    if n == "cabana-v2":
        con.execute(f"""CREATE TEMP TABLE abl AS SELECT DISTINCT person_id, procedure_date d FROM {rp(G, 'procedure_occurrence')}
            WHERE person_id IN (SELECT person_id FROM k) AND procedure_date IS NOT NULL AND {code_like('upper(procedure_source_value)', AF_ABLATION)}""")
        H = int(round(HORIZON_MONTHS["cabana"] * 30.4375))
        q = lambda lo, hi: set(con.execute(f"""SELECT DISTINCT k.patient_key FROM k JOIN abl a USING (person_id)
            WHERE a.d BETWEEN k.idx + INTERVAL ({lo}) DAY AND k.idx + INTERVAL ({hi}) DAY""").df().patient_key)
        F["ablation_post_1_365"] = F.index.isin(q(1, 365))
        F["ablation_post_1_H"] = F.index.isin(q(1, H))
        F["ablation_post_any"] = F.index.isin(q(1, 100000))
        F["aad_prior365"] = drug_window(con, AAD, -365, -1, "x").reindex(F.index).to_numpy()
        F["aad_prior_ever"] = drug_window(con, AAD, -100000, -1, "x").reindex(F.index).to_numpy()
    if n == "transform-hf":
        stays(con)
        X = con.execute("""SELECT k.patient_key, x.stay_s IS NOT NULL in_stay,
              EXISTS (SELECT 1 FROM stays st WHERE st.person_id = k.person_id AND st.e < k.idx AND st.e >= k.idx - INTERVAL 30 DAY) post_dc_30
            FROM k JOIN idxstay x USING (patient_key)""").df().set_index("patient_key").reindex(F.index)
        F["index_in_inpatient_stay"] = X.in_stay.fillna(False).astype(bool).to_numpy()
        F["index_within_30d_after_discharge"] = (X.post_dc_30.fillna(False).astype(bool) & ~X.in_stay.fillna(False).astype(bool)).to_numpy()
    if n in ("amplify", "lodestar", "prove-it"):
        key = {"amplify": "amplify", "lodestar": "lodestar", "prove-it": "prove_it"}[n]
        O = pd.read_parquet(K.A / f"claude-{n}-outcomes-v1/restricted_outcomes.parquet").set_index("patient_key").reindex(F.index)
        Hd = int(round(HORIZON_MONTHS[key] * 30.4375))
        ok = O.t_primary.notna() & (O.exclude_phase2 == 0)
        tt = np.minimum(O.t_primary, Hd)
        ev = (O.e_primary == 1) & (O.t_primary <= Hd) & ok
        F["y_ok"], F["event_h"], F["t_h"] = ok.to_numpy(), ev.to_numpy(), tt.to_numpy()
        stays(con)
        if n == "amplify":
            F["event_le30d"] = (ev & (O.t_primary <= 30)).to_numpy()
            # event stay = first stay starting at idx + t (first_hosp); primary-billing VTE code within that stay?
            ed = (idx + pd.to_timedelta(O.t_primary.where(ev), unit="D")).rename("ed")
            con.register("ev0", ed.dropna().reset_index())
            pb = con.execute(f"""SELECT DISTINCT e.patient_key FROM ev0 e JOIN k USING (patient_key)
                JOIN stays st ON st.person_id = k.person_id AND st.s = CAST(e.ed AS DATE)
                JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = k.person_id AND c.condition_start_date BETWEEN st.s AND st.e
                WHERE c.condition_status_source_value = '{PRIMARY_BILLING}'
                  AND {code_like("upper(replace(c.condition_source_value, '.', ''))", VTE)}""").df().patient_key
            F["event_vte_primary_billing"] = F.index.isin(set(pb)) & F.event_h
            gap = con.execute("""SELECT e.patient_key, date_diff('day', x.idx_stay_end, CAST(e.ed AS DATE)) g FROM ev0 e
                JOIN idxstay x USING (patient_key)""").df().set_index("patient_key").g.reindex(F.index)
            F["event_le7d_after_index_stay"] = ((gap <= 7) & F.event_h).to_numpy()
        else:
            lo = "x.idx + INTERVAL 30 DAY" if n == "prove-it" else "x.idx_stay_end + INTERVAL 1 DAY"
            rv = con.execute(f"""SELECT x.patient_key, min(p.procedure_date) d FROM idxstay x JOIN {rp(G, 'procedure_occurrence')} p
                ON p.person_id = x.person_id WHERE p.procedure_date >= {lo}
                  AND {code_like('upper(p.procedure_source_value)', PCI_CODES + CABG_CODES)} GROUP BY 1""").df().set_index("patient_key").d
            rt = (pd.to_datetime(rv.reindex(F.index)) - idx).dt.days
            F["revasc_within_h"] = (ok & (rt <= Hd)).to_numpy()
            F["revasc_adds_event"] = (ok & ~ev & (rt <= tt)).to_numpy()   # no current event; revasc before censoring
            F["revasc_advances_event"] = (ev & (rt < O.t_primary)).to_numpy()
    F.index.name = "patient_key"
    F.insert(0, "treated", t.reindex(F.index).to_numpy())
    F.reset_index().to_parquet(K.OUT / "flags" / f"restricted_flags_{n}.parquet")
    # aggregates
    rows = []
    arms = D.drop_duplicates("treated").set_index("treated").treatment_arm.to_dict()
    for c in F.columns:
        if c in ("treated", "t_h") or F[c].dtype != bool:
            continue
        r = dict(trial=n, label=K.FLAGGED[n], flag=c, n_all=len(F), k_all=int(F[c].sum()))
        for a in (1, 0):
            m = F.treated == a
            r[f"arm{a}"] = arms.get(a)
            r[f"n_arm{a}"], r[f"k_arm{a}"] = int(m.sum()), int(F.loc[m, c].sum())
        rows.append(r)
    con.close()
    print(n, "done", flush=True)
    return rows


DROP = {"jdat_succ_prior365", "y_ok", "index_in_inpatient_stay_laaos3", "index_dpp4_saxalo_only", "sitalina_index_day",
        "other_glp1_prior365", "other_sglt2_prior365"}


def fmt(R):
    """suppressed, differencing-safe aggregate table: if an arm count is 1-10 the total is shown rounded to integer %.
    Redundant nested flags whose differences could reveal counts of 1-10 are dropped (DROP; tartrate/carvedilol bucket rows)."""
    out = []
    for r in R:
        f = r["flag"] + ("_laaos3" if r["trial"] == "laaos3" and r["flag"] == "index_in_inpatient_stay" else "")
        if f in DROP or r["flag"].startswith(("jdat_tart_", "jdat_carv_")):
            continue
        o = dict(trial=r["trial"], label=r["label"], flag=r["flag"], n_all=r["n_all"])
        o["all"] = K.cnt_pct(r["k_all"], r["n_all"])
        small = any(1 <= r[f"k_arm{a}"] < K.MIN_CELL for a in (1, 0))
        if small and r["k_all"] >= K.MIN_CELL and not (1 <= r["n_all"] - r["k_all"] < K.MIN_CELL):
            o["all"] = f"~{round(100 * r['k_all'] / r['n_all'])}% (arm cell <11)"
        for a in (1, 0):
            o[f"arm{a}"] = r[f"arm{a}"]
            o[f"arm{a}_affected"] = K.cnt_pct(r[f"k_arm{a}"], r[f"n_arm{a}"])
        out.append(o)
    return pd.DataFrame(out)


if __name__ == "__main__":
    K.umask()
    if sys.argv[1:] == ["format"]:
        T = fmt(pd.read_parquet(K.OUT / "flags" / "restricted_criteria_counts_raw.parquet").to_dict("records"))
        T.to_csv(K.OUT / "criteria_counts.csv", index=False)
        pd.set_option("display.width", 250)
        print(T.to_string(index=False))
        sys.exit()
    trials = sys.argv[1].split(",") if len(sys.argv) > 1 else list(K.FLAGGED)
    with Pool(min(9, len(trials))) as p:
        res = p.map(run, trials, chunksize=1)
    R = [x for r in res for x in r]
    fr = K.OUT / "flags" / "restricted_criteria_counts_raw.parquet"  # raw counts (restricted)
    RR = pd.DataFrame(R)
    if len(sys.argv) > 1 and fr.exists():
        o = pd.read_parquet(fr)
        RR = pd.concat([o[~o.trial.isin(trials)], RR], ignore_index=True)
    RR.to_parquet(fr)
    T = fmt(R)
    f = K.OUT / "criteria_counts.csv"
    if len(sys.argv) > 1 and f.exists():
        old = pd.read_csv(f)
        T = pd.concat([old[~old.trial.isin(trials)], T], ignore_index=True)
    T.to_csv(f, index=False)
    pd.set_option("display.width", 250)
    print(T.to_string(index=False))
