# Trial Config Schema

Each file in `configs/` (except this one) defines one trial.
Loaded by `cohort_utils.load_trial_config()`, validated by `cohort_utils.validate_config()`.

**Rules:** no absolute paths, clinical logic only. OMOP/local paths stay on the CLI.

---

## Top-level sections

```yaml
trial:          # trial identity
design:         # new-user design parameters
arms:           # ordered list, treated arm first
inclusion:      # inclusion criteria (stored as pool flags; Stage 3 applies thresholds)
exclusion:      # exclusion flags (ICD + drug)
covariates:     # pool-level covariate flags
endpoint:       # primary endpoint definition
ecg:            # ECG window parameters
feasibility:    # Stage 0 GO/NO-GO thresholds
```

---

## `trial`

```yaml
trial:
  key: comet                          # str, filename stem; used as output subdir
  name: COMET                         # display name
  full_name: "Carvedilol Or Metoprolol European Trial"
  citation: "Poole-Wilson et al., Lancet 2003"
  published_hr: 0.83
  published_hr_ci: [0.74, 0.93]
  rct_duplicate_success: true         # bool, was RCT-DUPLICATE emulation successful?
```

---

## `design`

```yaml
design:
  type: two_active_drug               # "two_active_drug" | "drug_vs_active_comparator"
                                      # NOTE: "drug_vs_no_drug" is NOT yet supported
  index_definition: first_ever_arm_dispense   # only supported value currently
  washout_days: 365                   # stored as prior_<arm>_days; Stage 3 sweeps
```

---

## `arms`

Ordered list — **first arm = treated**. Two arms minimum.

```yaml
arms:
  - name: carvedilol            # str; becomes arm column value and column-name prefix
    role: treated               # "treated" | "control"; exactly one "treated" required
    keywords: [CARVEDILOL]      # list[str]; matched case-insensitively on drug_upper
    formulation_filter:         # optional
      require: [TARTRATE]       # drug_upper must also contain one of these
      exclude: [SUCCINATE]      # drug_upper must NOT contain any of these
    stage3_alias: carv          # optional; adds first_carv_date / prior_carv_days aliases
                                # needed for backward compat with stage3_filter.py
  - name: metoprolol
    role: control
    keywords: [METOPROLOL]
    stage3_alias: meto
```

`keywords` may reference `KEYWORD_REGISTRY` constants by name:
```yaml
keywords: [ACEI_KEYWORDS, ARB_KEYWORDS]   # expanded by resolve_keywords()
```

---

## `inclusion`

```yaml
inclusion:
  age_min: 18               # float; stored as age_at_index in pool; Stage 3 enforces
  age_max: 80
  ef:
    threshold: 35.0         # float
    direction: "<="         # "<=" (HFrEF) | ">=" (HFpEF)
    source: echo_or_icd     # "echo_or_icd" | "echo_only" | "none"
    lookback_days: 1825
  required_icd:             # list; flags stored in pool; Stage 3 may apply
    - name: prior_hf_code_1yr
      codes: [I50]          # list of ICD-10 prefixes (without dot)
      lookback_days: 365
      char: 3               # 3 (default) | 4; controls ICD prefix length
  required_drug: []         # list of drug flags; same spec as exclusion.drug below
```

---

## `exclusion`

```yaml
exclusion:
  icd:
    - name: valvular_disease_5y       # str; column name in pool
      codes: [I05, I06, I07, I08, I09, I34, I35, I36, I37, I38, I39]
      lookback_days: 1825             # int; days before index date
      char: 3
    - name: av_block_2_3_24m
      codes: [I441, I442, I443]
      lookback_days: 730
      char: 4
  drug:
    - name: had_ccb_nondihydro_pm30d  # str; column name in pool
      keywords: [VERAPAMIL, DILTIAZEM]  # or keyword_const: CCB_NONDIHYDRO
      window_days: 30                 # int; ±window around index date
      mode: pm                        # "pm" = plus/minus (±window); "before" = lookback only
```

For `keyword_const`, use a string or list of registry names:
```yaml
keyword_const: OTHER_BB
# or
keyword_const: [ACEI_KEYWORDS, ARB_KEYWORDS]
```

---

## `covariates`

```yaml
covariates:
  comorbidities:                    # subset of COMORBIDITY_ICD keys; all = default
    - copd
    - htn
    - dm
    - cad_mi
    - afib
    - hyperlipidemia
    - stroke
  medications_90d:                  # 90-day lookback; adds {name}_90d columns
    - loop_diuretic                 # LOOP_DIURETICS keywords
    - acei_arb                      # ACEI_KEYWORDS + ARB_KEYWORDS
    - aldosterone_antag             # ALDOSTERONE_ANTAG keywords
    - digoxin                       # DIGOXIN keywords
    - statin                        # STATIN keywords
    - nitrate                       # NITRATE keywords
  condition_flags:                  # additional named ICD flags (same spec as exclusion.icd)
    - name: hfref_icd_5y
      codes: [I50]
      lookback_days: 1825
      char: 3
  extra_smd_cols: []                # covariates beyond the frozen SMD_COLS 37
                                    # (land in pool but NOT auto-balanced until Stage 3/4 refactor)
```

**Medication group names** recognized by `MEDICATION_KEYWORDS`:
`loop_diuretic`, `acei_arb`, `acei`, `arb`, `aldosterone_antag`, `digoxin`, `statin`,
`nitrate`, `sglt2i`, `beta_blocker`, `warfarin`, `doac`, `antiplatelet`,
`aspirin`, `p2y12`, `pcsk9i`, `statin_high`, `insulin`, `glp1ra`.

---

## `endpoint`

```yaml
endpoint:
  primary:
    name: all_cause_mortality         # str; informational label
    followup_days: 1825              # int; max follow-up; events after this are censored
    censor: administrative           # "administrative" = use death-table max or --censor-date
    components:                      # list; composite = OR, time-to-FIRST event
      - type: mortality              # death table (date-only; cause not available)
      # composite example:
      - type: inpatient_icd          # ICD code during inpatient visit
        codes: [I50]
        char: 3
        visit_concept_ids: [9201, 262]  # OMOP: 9201=inpatient, 262=ER-to-inpatient
      - type: condition_icd          # any ICD code occurrence (no visit gate)
        codes: [I21, I22]
        char: 3
      - type: procedure              # procedure code match
        concept_ids: []              # OMOP procedure_concept_id list
        source_prefixes: [3572, 3573]  # procedure_source_value prefix strings
  proxy_note: null                   # str; documents endpoint proxy limitations
```

**Component types:**
- `mortality` — OMOP `death` table. Date-only (no cause). CV death = ALL-CAUSE PROXY.
- `inpatient_icd` — ICD code during inpatient visit. Requires `visit_occurrence` data.
  Falls back to date-overlap if `visit_occurrence_id` absent in conditions.
- `condition_icd` — bare ICD code, any setting.
- `procedure` — `procedure_occurrence` match by concept_id or source_value prefix.

**Important:** The `death` table at Yale is date-only — no `cause_concept_id`.
For trials with CV-death endpoints, the proxy is all-cause death. This inflates the
mortality component with non-CV deaths. Document in `proxy_note`.

---

## `ecg`

```yaml
ecg:
  window_days: 89         # int; MUST be < 90 (validated). Nearest ECG on/before index.
  window_mode: before     # "before" = nearest on/before; "symmetric" = nearest ±window
  pool_window_days: 365   # int; breadth of ecg_candidates.parquet; Stage 3 narrows
```

---

## `feasibility`

```yaml
feasibility:
  min_n_per_arm: 200      # Stage 0 GO/NO-GO: both arms must have ≥ this many patients
```

---

## Keyword Registry constants (for `keywords` / `keyword_const` references)

| Name | Drugs |
|---|---|
| `CARVEDILOL` | carvedilol |
| `METOPROLOL` | metoprolol |
| `ACEI_KEYWORDS` | lisinopril, enalapril, ramipril, captopril, perindopril, quinapril, fosinopril, benazepril, trandolapril, moexipril |
| `ARB_KEYWORDS` | losartan, valsartan, candesartan, irbesartan, telmisartan, olmesartan, azilsartan, eprosartan |
| `CCB_NONDIHYDRO` | verapamil, diltiazem |
| `OTHER_BB` | bisoprolol, atenolol, propranolol, nebivolol, labetalol, acebutolol, pindolol, nadolol |
| `LOOP_DIURETICS` | furosemide, torsemide, bumetanide, ethacrynic |
| `ALDOSTERONE_ANTAG` | spironolactone, eplerenone |
| `DIGOXIN` | digoxin |
| `STATIN` | atorvastatin, rosuvastatin, simvastatin, pravastatin, lovastatin, fluvastatin, pitavastatin |
| `NITRATE` | nitroglycerin, isosorbide |
| `SGLT2I` | empagliflozin, dapagliflozin, canagliflozin, ertugliflozin, sotagliflozin, bexagliflozin |
| `WARFARIN` | warfarin |
| `DOAC` | apixaban, rivaroxaban, dabigatran, edoxaban |
| `APIXABAN` | apixaban |
| `RIVAROXABAN` | rivaroxaban |
| `DABIGATRAN` | dabigatran |
| `ANTIPLATELET` | clopidogrel, prasugrel, ticagrelor, aspirin |
| `P2Y12` | clopidogrel, prasugrel, ticagrelor |
| `ASPIRIN` | aspirin |
| `SACUBITRIL_VALSARTAN` | sacubitril, entresto |
| `IVABRADINE` | ivabradine |
| `EPLERENONE` | eplerenone |
| `SPIRONOLACTONE` | spironolactone |
| `GLP1RA` | semaglutide, liraglutide, dulaglutide, exenatide, albiglutide |
| `INSULIN` | insulin |
| `PCSK9I` | evolocumab, alirocumab |
| `EZETIMIBE` | ezetimibe |
| `TICAGRELOR` | ticagrelor |
| `CLOPIDOGREL` | clopidogrel |
| `PRASUGREL` | prasugrel |
| `BISOPROLOL` | bisoprolol |
| `AMIODARONE` | amiodarone |
| `DOFETILIDE` | dofetilide |
| `DRONEDARONE` | dronedarone |
| `RIOCIGUAT` | riociguat |
| `SACUBITRIL` | sacubitril |
| `VALSARTAN` | valsartan |
| `ENALAPRIL` | enalapril |
