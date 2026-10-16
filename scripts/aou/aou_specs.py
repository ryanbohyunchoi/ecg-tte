"""AoU adaptation of the declared Yale trial specifications (scripts/trial_specs.py), user decisions of 2026-10-08:

1. Coded proxies, flagged, for criteria that need Yale-only data (structured echo EF, MUSE ECG text). AoU has neither.
   Every adapted trial is listed in PROXY with the replaced criterion and the proxy; a sensitivity drops them.
2. All-cause death replaces CV death and CHD death in every composite (AoU has almost no cause-of-death data; Yale's
   "no cause record = CV" rule already makes CV death equal all-cause death when causes are missing).
3. Index window: start no earlier than ICD10_ERA_START (the 365-day look-back is entirely ICD-10-CM; AoU sites send
   ICD-9-CM before 2015-10-01 and the specs are ICD-10 prefixes), end no later than the AoU EHR cutoff.

The adapted spec is a copy; trial_specs.py is never modified. Any criterion that is still Yale-only after the adaptation,
or any spec key this adapter does not know, stops the trial with a structured reason (AGENTS.md: no silent changes).
"""
from __future__ import annotations

import copy

from aou_common import ICD10_ERA_START

HFREF = ["I502", "I504"]  # systolic / combined systolic-diastolic heart failure (ICD-10-CM I50.2x, I50.4x)
PROXY = {
    # trial key: (replaced criterion, proxy, note)
    "paradigm_hf_seq": (["lvef_gt"], {"ef_unknown_require_codes": HFREF}, "EF > 40 exclusion -> HFrEF code (I50.2x/I50.4x) required"),
    "elite_ii": (["lvef_gt"], {"ef_unknown_require_codes": HFREF}, "EF > 40 exclusion -> HFrEF code required"),
    "af_chf": (["lvef_gt"], {"ef_unknown_require_codes": HFREF}, "EF > 35 exclusion -> HFrEF code required"),
    "paradise_mi": (["lvef_gt"], {"ef_unknown_require_codes": ["I50"]}, "post-MI EF <= 40 or congestion -> any HF code required"),
    "valiant": (["lvef_gt"], {"ef_unknown_require_codes": ["I50"]}, "post-MI LV dysfunction or HF -> any HF code required"),
    "emperor_preserved": (["lvef_lt"], {}, "EF < 41 exclusion dropped; the spec's EF-unknown rule (I50.3x required) is the proxy"),
    "life": (["gate.ecg_text_365d"], {"gate.require_all": [["I517"]]}, "ECG-LVH text -> LVH/cardiomegaly code (I51.7) on or before index"),
    "comet": ([], {"ef_unknown_require_codes": HFREF}, "COMET EF <= 35 (spec-v2 fix; Yale used the JDAT roster) -> HFrEF code required"),
}
YALE_ONLY_EXCLUSIONS = {"lvef_gt", "lvef_lt"}
YALE_ONLY_GATES = {"ecg_text_365d"}
KNOWN_GATES = {"any_before_or_on_index", "window_30d", "require_all", "first_dx_within", "ecg_text_365d", "pci_30d",
               "procedure_1d", "require_drugs_365d"}
KNOWN_EXCLUSIONS = {"ever_codes", "codes_window", "lvef_gt", "lvef_lt", "hfpef_code_only", "ef_unknown_require_codes", "egfr_lt",
                    "potassium_gt", "sbp_lt", "anticoag_30d", "other_anticoag_365d", "other_drugs_365d",
                    "concomitant_procedure_codes"}
KNOWN_TOP = {"add_on", "arm0_procedure", "arms", "design", "drugs_90d", "exclusions", "extra_dx", "gate", "index_end",
             "index_event_pci", "index_start", "max_age", "min_age", "name", "note", "prior_class", "prognostic", "published_hr",
             "report_covariates", "role", "seq_ratio", "seq_window_days", "spec_version", "washout_arms"}
KNOWN_DESIGNS = {None, "new_user", "switch", "switch_seq", "procedure", "proc_vs_drug"}
DEATH_SUBST = {"cv_death": "death", "chd_death": "death"}


class Unsupported(Exception):
    """Mandatory requirement that AoU data cannot support; the trial stops with this reason."""


def adapt(key: str, spec: dict, ehr_cutoff: str, index_floor: str = ICD10_ERA_START, proxies: bool = True) -> tuple[dict, dict]:
    """(adapted spec, record of every change). proxies=False: the trial is stopped if it needs a proxy (sensitivity)."""
    s = copy.deepcopy(spec)
    rec = dict(key=key, spec_version=spec.get("spec_version"), changes=[])
    unknown = set(s) - KNOWN_TOP
    if unknown:
        raise Unsupported(f"unknown_spec_keys:{sorted(unknown)}")
    if s.get("design") not in KNOWN_DESIGNS:
        raise Unsupported(f"unknown_design:{s.get('design')}")
    g, ex = s["gate"], s["exclusions"]
    if set(g) - KNOWN_GATES or set(ex) - KNOWN_EXCLUSIONS:
        raise Unsupported(f"unknown_criteria:{sorted((set(g) - KNOWN_GATES) | (set(ex) - KNOWN_EXCLUSIONS))}")
    if key in PROXY:
        drop, add, note = PROXY[key]
        if not proxies:
            raise Unsupported(f"needs_coded_proxy:{note}")
        for d in drop:
            tgt, k = (g, d.split(".", 1)[1]) if d.startswith("gate.") else (ex, d)
            if k in tgt:
                rec["changes"].append(dict(kind="proxy_drop", criterion=d, value=tgt.pop(k)))
        for a, v in add.items():
            tgt, k = (g, a.split(".", 1)[1]) if a.startswith("gate.") else (ex, a)
            if k == "require_all":
                tgt[k] = list(tgt.get(k, [])) + v
            elif k in tgt and tgt[k] != v:
                raise Unsupported(f"proxy_conflict:{a}")
            else:
                tgt[k] = v
            rec["changes"].append(dict(kind="proxy_add", criterion=a, value=v, note=note))
    left = (set(g) & YALE_ONLY_GATES) | (set(ex) & YALE_ONLY_EXCLUSIONS)
    if left:
        raise Unsupported(f"yale_only_criteria_without_proxy:{sorted(left)}")
    s0, s1 = s["index_start"], s["index_end"]
    s["index_start"], s["index_end"] = max(s0, index_floor), min(s1, ehr_cutoff)
    if s["index_start"] >= s["index_end"]:
        raise Unsupported("empty_index_window")
    if (s0, s1) != (s["index_start"], s["index_end"]):
        rec["changes"].append(dict(kind="index_window", yale=[s0, s1], aou=[s["index_start"], s["index_end"]]))
    s["spec_version"] = f"{spec.get('spec_version')}+aou1"
    rec["aou_spec_version"] = s["spec_version"]
    return s, rec


def adapt_outcome(key: str, comps: list) -> tuple[list, list]:
    """Outcome components with CV / CHD death -> all-cause death (deduplicated, order kept)."""
    out, changes = [], []
    for c in comps:
        c2 = DEATH_SUBST.get(c, c) if isinstance(c, str) else c
        if c2 != c:
            changes.append(dict(kind="death_substitute", yale=c, aou=c2))
        if c2 not in out:
            out.append(c2)
    return out, changes


def adapt_all(ehr_cutoff: str, proxies: bool = True) -> dict:
    """registry name -> dict(spec, outcome, record) or dict(stopped=reason)."""
    from aou_common import registry
    from trial_specs import OUTCOMES, TRIALS
    res = {}
    for n, k in registry().items():
        try:
            s, rec = adapt(k, TRIALS[k], ehr_cutoff, proxies=proxies)
            if k not in OUTCOMES:
                raise Unsupported("no_outcome_definition")
            o, oc = adapt_outcome(k, OUTCOMES[k])
            rec["changes"] += oc
            res[n] = dict(key=k, spec=s, outcome=o, record=rec)
        except Unsupported as e:
            res[n] = dict(key=k, stopped=str(e))
    return res
