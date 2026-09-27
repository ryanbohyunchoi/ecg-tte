# v1.6 S9: covariate sets — where adding AI-ECG moves held-out covariates below |SMD| 0.1 (2026-09-27)

Exploratory. Plan: `docs/v16/S9_COVARIATE_SETS_PLAN.md` (committed before any S9 result). Script `scripts/v16/s9_covsets.py`; outputs `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s9-covsets/` (`results.csv`, `set_summary.csv`, `set_per_trial.csv`, `engine_summary.csv`, `domain_*.csv`, `var_*.parquet`). Set-3 selection: `docs/v16/selection_S9.json`. Aggregates only.

## Key findings

Units: "% < 0.1" = the per-trial percentage of a set's held-out covariates with |SMD| < 0.1, averaged over trials (primary metric). "Love count" = the number of the set's covariates whose median |SMD| across trials is < 0.1. d = ECG − base. Half B is the out-of-sample half for Set 3; the full cohort contains the Set-3 selection half.

**The four sets**

| set | how it was chosen | size |
|---|---|---|
| Set 1 | clinical ECG-relevant confounders, fixed from mechanism | 28 |
| Set 2 | literature core + common items | ~270 |
| Set 3 | top 25 by half-A ECG gain, confirmed in half B | 25 |
| FULL | 58-panel + expanded non-ECG-proximal panel from claude-v16-covars2b | ~400 |

1. **Headline: demo PS, 1:1 caliper 0.1, 18 trials.** ECG moves covariates below 0.1 in every set. Each set's result survives both placebos, comparator clustering, LOO and BH-FDR (36 tests per metric), and replicates in both halves.

   | set | % < 0.1, base → ECG (d, k, p) | love count, base → ECG | half B |
   |---|---|---|---|
   | Set 1 (clinical) | 43.6 → 55.1 (+11.6, 13/18, p = 0.001, q = 0.004) | 8 → 16 of 28 (p = 0.021) | +9.2 pp (p = 0.003); love 6 → 11 (p = 0.14) |
   | Set 2 (literature) | 55.8 → 61.9 (+6.1, 16/18, p < 0.001) | 160 → 193 of 268 (p < 0.001) | +5.7 pp (p < 0.001); love 146 → 176 (p = 0.005) |
   | Set 3 (split-sample) | 28.5 → 39.4 (+10.9, p < 0.001) | 2 → 7 of 25 (p = 0.098) | **+7.4 pp (13/18, p = 0.012, q = 0.031)**; vs shufECG p = 0.028, vs noise p = 0.018, cluster p = 0.025; love 2 → 4 (p = 0.31) |
   | FULL | 59.9 → 65.3 (+5.4, 17/18, p < 0.001) | 266 → 309 of 403 | +4.4 pp (p < 0.001); love 244 → 277 (p = 0.006) |

   Set 3 confirms out of sample on the per-trial metric, not on the love count. Its selected variables start badly balanced (base 28% < 0.1). ECG improves them in half B, but mostly not all the way below 0.1.

   Demo with caliper 0.2 gives the same picture: Set 1 +9.8 pp, love 10 → 17, half B p = 0.002.

2. **Minimal-7 and common-10 (18 trials): smaller gains, and not every set passes every check.**
   - **Minimal-7:**
     - Set 1: +11.8 pp (p = 0.001), love 7 → 19 of 28 (p = 0.001). Half B p = 0.019, but cluster p = 0.059.
     - Set 3, half B: +6.9 pp (p = 0.013); love 9 → 16 (p = 0.001).
     - Set 2 and FULL: significant in both halves.
   - **Common-10:**
     - Set 1: +7.9 pp (p = 0.030), half B p = 0.11, love 17 → 21 (p = 0.36).
     - Set 3, half B: +2.5 pp (p = 0.31). **Not confirmed.**
     - Set 2 and FULL: +3.5 to +3.7 pp (p ≤ 0.003).

3. **The 8 physiology trials: all positive, but underpowered.** With only 8 trials the smallest possible exact p is 0.008.
   - Set 1 is never significant in the full cohort (p = 0.12–0.19) despite gains of +9 to +12 pp.
   - Set 2 and FULL: p = 0.008–0.039.
   - Set 3, half B: not confirmed (p = 0.45 / 0.062 / 0.086).

4. **References.**
   - **Sparse PS:** the gain is small, and there is none on Set 1.
     - Set 1: 58.0 → 61.6 (p = 0.19), love 21 → 21 of 28.
     - Set 2: +2.9 pp (p = 0.026), love 203 → 205.
     - FULL: +2.7 pp (p = 0.029, half B p = 0.13).
     - Set 3: +7.6 pp full, but half B p = 0.097.
   - **hdPS200:** null on Set 2 and FULL (+0.3 / +0.7 pp). Set 1 is borderline: +5.1 pp (p = 0.073) and love 19 → 25 (p = 0.015), but half B p = 0.15.

5. **Where ECG helps and where it does not** (headline scenario; domain means over all domains):
   - **Largest gains:** the echo domains, the ECG-proximal codes, and vitals and core labs.

     | domain | mean \|SMD\|, base → ECG |
     |---|---|
     | LV function | 0.205 → 0.152 |
     | LV structure | 0.138 → 0.095 |
     | diastolic / LA | 0.136 → 0.094 |
     | RV | 0.134 → 0.104 |
     | ECG-proximal comorbidities | 0.125 → 0.089 |
     | ECG-proximal Charlson / Elixhauser | 0.195 → 0.132 and 0.227 → 0.165 |
     | vitals and core labs | 0.143 → 0.118 (18/18) |

   - **Smaller but significant gains:** the non-proximal expanded domains (comorbidity, labs, medications, Elixhauser, utilisation), d ≈ −0.007 to −0.018.
   - **No gain:**
     - valves / aorta (p = 0.29);
     - 58-panel other labs (p = 0.90);
     - preventive care, calendar;
     - BNP (ECG-proximal lab; p = 0.55);
     - eGFR and creatinine, which get slightly worse in Set 1.
   - **Hemoglobin** stays at 0.21.
   - **Under the sparse PS** only vitals / core labs, labs, comorbidity, device and Elixhauser/Charlson domains improve (q < 0.05). BNP gets worse with ECG (ECG worse than shufECG, p = 0.003).

6. **Placebos are null.** Over the 36 FDR-family rows (full cohort, % < 0.1):
   - shufECG − base averages −0.47 pp and noise − base +0.49 pp, with no row at p < 0.05 in either direction.
   - ECG − base averages +6.9 pp.
   - No set, scenario, half or metric shows ECG significantly worse than base.

7. **Survivor counts.**
   - **BH survivors, full cohort** (ECG better, q < 0.05, out of 36): % < 0.1 in 24, love count in 16, mean \|SMD\| in 33, % > 0.2 in 25.
   - **ECG-specific and replicated** on % < 0.1 (q < 0.05, both placebos p < 0.05, cluster and LOO p < 0.05, p < 0.05 in both halves): 12 rows.
     - demo / caliper 0.1: all four sets (18 trials) and FULL (physiology trials);
     - minimal-7: Set 2, Set 3, FULL;
     - common-10: FULL;
     - demo / caliper 0.2: Set 1, Set 2, FULL.
   - None are sparse or hdPS200.

8. **Trial emulation (engine metrics): no significant |Δlog HR| gain.** |Δlog HR| has q ≥ 0.17 in all 6 cells. z² falls in 5 of 6 cells (q = 0.022–0.042), but as in S8 this is generic shrinkage, not benchmark agreement.

**Bottom line.** With a demographic PS, adding the ECG embedding raises the share of the 28 pre-specified ECG-relevant confounders with |SMD| < 0.1 from 44% to 55% per trial, and moves the love count from 8 to 16 of 28. The result survives placebos, clustering, LOO and FDR, and replicates in both halves.

A split-sample, data-selected set confirms out of sample (+7.4 pp in half B). The gain is concentrated in echo, ECG-proximal and core-vital covariates. It is small to absent for valves, most labs and renal function, and with rich coded PSs (sparse, hdPS200).

## Set definitions (fixed before any S9 result)

### Set 1: plan item → variable (58-panel `p58:`, claude-v16-covars2b `x:`)

Every item is used when it is held out from the cell's PS and available in the trial (finite |SMD|). Loop diuretic is dropped automatically where it is the exposure (TRANSFORM-HF: status dropped_exposure) and by the PS-overlap rule where a PS contains it. LV mass is not in any available panel. `IVSd > 15 mm` (58-panel) is not listed in the plan and is not used.

| group | item | variables |
|---|---|---|
| LV function | LVEF (observed) | p58:smd_obs_lvef |
| LV function | echo EF | p58:pp_LVFUNC__ef |
| LV function | LV systolic grade | p58:pp_LVFUNC__lv_sys_grade |
| LV function | GLS | p58:pp_LVFUNC__gls |
| LV function | LV stroke volume index | p58:pp_LVFUNC__lvsvi |
| LV structure | LVIDd | p58:pp_LVSTRUCT__lvidd |
| LV structure | LVEDVi | p58:pp_LVSTRUCT__lvedvi |
| LV structure | LVESVi | p58:pp_LVSTRUCT__lvesvi |
| LV structure | IVSd | p58:pp_LVSTRUCT__ivsd |
| LV structure | LVPWd | p58:pp_LVSTRUCT__lvpwd |
| LV structure | wall-thickness grade | p58:pp_LVSTRUCT__wall_thickness_grade |
| LV structure | LV mass (if available) | not available |
| Diastolic and atrial | LA volume index | p58:pp_DIAST__lavi |
| Diastolic and atrial | LA size grade | p58:pp_DIAST__la_size_grade |
| Diastolic and atrial | E/e' | p58:pp_DIAST__e_eprime |
| Diastolic and atrial | diastolic grade | p58:pp_DIAST__diastolic_grade |
| RV and pulmonary | RVSP | p58:pp_RVPULM__rvsp |
| RV and pulmonary | TAPSE | p58:pp_RVPULM__tapse |
| RV and pulmonary | RV S' | p58:pp_RVPULM__rv_s |
| RV and pulmonary | RV systolic grade | p58:pp_RVPULM__rv_sys_grade |
| RV and pulmonary | pulmonary hypertension dx | x:pulmonary_hypertension |
| Neurohormonal and renal | NT-proBNP | p58:pp_BNP__ntprobnp |
| Neurohormonal and renal | eGFR | p58:pp_LAB__egfr |
| Neurohormonal and renal | creatinine | p58:smd_obs_creatinine |
| Neurohormonal and renal | BUN | p58:pp_LAB__bun |
| Neurohormonal and renal | hemoglobin | p58:smd_obs_hemoglobin |
| Clinical HF burden | prior HF hospitalisation (strict pre-index) | x:n_hf_hosp_365 |
| Clinical HF burden | cardiomyopathy dx | x:cardiomyopathy_any |
| Clinical HF burden | loop diuretic use (if not in the PS or the exposure) | x:rx_loop_diuretic_365 |

Set 1 = 28 variables.

### Set 2: literature core + common items (docs/v16/lit_covariates.json) → variables

Variables are the covars2 variables listed for the item in the COVARIATES2 literature cross-check (wildcards expanded on the covars2b dictionary), plus, for items the cross-check marks as already in an existing panel, the 58-panel (`p58:`) or claude-v16-covars (`v1:`) variable. Exposure leaks (per-trial status dropped_exposure / *leak* / exposure_leak) and non-pre-index variables are removed by the loader; per cell, variables in or overlapping the PS are removed. ECG-proximal variables are kept in Set 2 (a descriptive row, Set 2 non-proximal, drops them).

| id | item | priority | variables |
|---|---|---|---|
| 1 | age_at_index | core | none (in every PS (demo)) |
| 2 | sex | core | none (in every PS (demo)) |
| 3 | race | core | v1:race_black, v1:race_asian, v1:race_other_unknown |
| 4 | ethnicity_hispanic | core | v1:hispanic, v1:ethnicity_unknown |
| 5 | index_year | core | none (in every PS (demo)) |
| 6 | prior_observation_days | common | x:ehr_history_days |
| 7 | care_site_campus | common | x:campus_ynh_365, x:campus_bh_365, x:campus_src_365, x:campus_gh_365, x:campus_lmh_365, x:campus_wh_365 |
| 8 | index_setting_inpatient | common | none (index-day, not pre-index (excluded, AUDIT_V16_ROUND2)) |
| 9 | insurance_type | common | none (not in extract) |
| 10 | low_income_or_dual | common | none (not in extract) |
| 11 | area_deprivation_index | common | none (needs external ADI file) |
| 14 | smoking | core | v1:tobacco_current, v1:tobacco_ever |
| 15 | alcohol_use_disorder | common | x:alcohol_use_disorder, x:elx_alcohol |
| 16 | drug_use_disorder | common | x:drug_use_disorder_any, x:opioid_use_disorder, x:elx_drug_abuse |
| 17 | obesity_dx | core | x:elx_obesity, x:obesity_class1_2_bmi30_39, x:obesity_class3, x:overweight, v1:obesity |
| 18 | bmi | core | p58:smd_obs_bmi |
| 19 | heart_failure | core | x:hf_any_365, x:cci_chf, x:elx_chf |
| 20 | prior_hf_hospitalization | core | x:n_hf_hosp_365 |
| 21 | ischemic_heart_disease | core | x:angina_any, x:acs_365, x:cci_mi |
| 22 | prior_mi | core | x:prior_mi_ever, x:cci_mi |
| 23 | prior_pci | core | x:prior_pci_ever, x:prior_pci_365 |
| 24 | prior_cabg | core | x:prior_cabg_ever |
| 25 | atrial_fibrillation_flutter | core | x:atrial_flutter, x:af_persistent_permanent, x:elx_arrhythmia |
| 26 | other_arrhythmia | common | x:other_dysrhythmia, x:svt, x:ventricular_arrhythmia_ever, x:cardiac_arrest_ever |
| 27 | conduction_disorder | common | x:conduction_disease_any, x:av_block, x:bundle_branch_block, x:long_qt_wpw_other_conduction |
| 28 | cardiac_device | common | x:pacemaker_ever, x:icd_ever, x:crt_ever, x:cied_any_ever, x:loop_recorder_ever |
| 29 | valve_disease | common | x:elx_valvular, x:aortic_stenosis, x:mitral_regurgitation |
| 30 | prior_valve_procedure | common | x:prior_valve_procedure_ever |
| 31 | cardiomyopathy | common | x:cardiomyopathy_any, x:cm_dilated, x:cm_hypertrophic, x:cm_ischemic, x:cm_other_restrictive |
| 32 | hypertension | core | x:elx_htn_uncomplicated, x:elx_htn_complicated |
| 33 | pulmonary_hypertension | common | x:pulmonary_hypertension, x:elx_pulm_circ |
| 34 | hyperlipidemia | core | v1:hyperlipidemia |
| 35 | ischemic_stroke | core | x:ischemic_stroke_365, x:stroke_tia_history_ever |
| 36 | intracranial_hemorrhage | core | x:hemorrhagic_stroke_ever, x:intracranial_bleed_ever |
| 37 | tia | core | x:stroke_tia_history_ever, x:cci_cvd |
| 38 | peripheral_arterial_disease | core | x:pad_broad, x:cci_pvd |
| 39 | vte_history | common | x:vte_history_ever, x:vte_365 |
| 40 | cha2ds2_vasc | core | x:cha2ds2vasc, x:cha2ds2vasc_ge2 |
| 41 | has_bled_modified | core | x:hasbled, x:hasbled_nodrug |
| 42 | diabetes_any | core | x:cci_dm_uncomplicated, x:cci_dm_complicated, x:elx_dm_uncomplicated, x:elx_dm_complicated |
| 43 | t2d | common | v1:t2d |
| 44 | diabetes_complications_dcsi | common | x:dcsi_domains, x:dm_retinopathy, x:dm_neuropathy, x:dm_nephropathy |
| 45 | hypoglycemia | common | x:hypoglycemia |
| 46 | ckd_any | core | x:cci_renal, x:elx_renal |
| 47 | ckd_stage | common | x:ckd_stage3, x:ckd_stage4_5, x:esrd |
| 48 | eskd_dialysis_transplant | core | x:esrd, x:dialysis_365, x:kidney_transplant |
| 49 | acute_kidney_injury | common | x:aki_365 |
| 50 | hyperkalemia | common | x:hyperkalemia |
| 51 | fluid_electrolyte_disorder | common | x:elx_fluid_electrolyte, x:hyponatremia |
| 52 | thyroid_disease | common | x:hypothyroidism, x:hyperthyroidism, x:elx_hypothyroid |
| 53 | obstructive_sleep_apnea | common | x:sleep_apnea |
| 54 | copd | core | x:copd, x:cci_cpd |
| 55 | asthma | common | x:asthma |
| 56 | pneumonia_recent | common | x:pneumonia_365 |
| 57 | liver_disease | common | x:elx_liver, x:cci_mild_liver, x:cci_severe_liver, x:cirrhosis |
| 58 | gi_bleed | core | x:gi_bleed_365 |
| 59 | major_bleed_other | core | x:bleed_any_365 |
| 60 | anemia | common | x:anemia, x:iron_deficiency, x:elx_deficiency_anemia |
| 61 | coagulopathy_thrombocytopenia | common | x:elx_coagulopathy, x:thrombocytopenia |
| 62 | dementia | common | x:dementia, x:cci_dementia |
| 63 | depression | common | x:depression, x:elx_depression |
| 64 | anxiety | common | x:anxiety |
| 65 | serious_mental_illness | common | x:serious_mental_illness, x:elx_psychoses |
| 66 | falls | common | x:falls |
| 67 | gait_mobility_weakness | common | x:gait_abnormality, x:weakness_debility |
| 68 | malnutrition_weight_loss | common | x:malnutrition, x:cachexia_weight_loss, x:elx_weight_loss |
| 69 | osteoporosis_fracture | common | x:osteoporosis, x:hip_fracture, x:fracture_hip_spine_rib |
| 70 | cancer_any | common | x:cancer_365, x:cancer_history_ever |
| 71 | metastatic_cancer | common | x:metastatic_365 |
| 72 | rheumatologic_disease | common | x:elx_rheum, x:cci_rheum, x:rheumatoid_arthritis, x:lupus |
| 73 | charlson_index | core | x:charlson_score, x:charlson_age_score |
| 74 | elixhauser_index | common | x:elixhauser_count, x:elixhauser_vw |
| 75 | combined_comorbidity_score | core | x:gagne_ccs |
| 76 | claims_frailty_index_kim | common | v1:frailty_count |
| 79 | acei | core | x:rx_acei_365 |
| 80 | arb | core | x:rx_arb_365 |
| 81 | arni | core | x:rx_arni_365 |
| 82 | beta_blocker | core | x:rx_beta_blocker_365 |
| 83 | mra | core | x:rx_mra_365 |
| 84 | loop_diuretic | core | x:rx_loop_diuretic_365 |
| 85 | thiazide | common | x:rx_thiazide_365 |
| 86 | ccb_dhp | common | x:rx_ccb_dhp_365 |
| 87 | ccb_nondhp | common | x:rx_ccb_nondhp_365 |
| 88 | other_antihypertensive | common | x:rx_other_antihypertensive_365, x:rx_hydralazine_365 |
| 89 | nitrate | common | x:rx_nitrate_365 |
| 90 | digoxin | common | x:rx_digoxin_365 |
| 91 | antiarrhythmic | common | x:rx_antiarrhythmic_365 |
| 92 | statin | core | x:rx_statin_365 |
| 93 | nonstatin_lipid | common | x:rx_other_lipid_lowering_365 |
| 94 | aspirin | core | x:rx_aspirin_365 |
| 95 | p2y12 | core | x:rx_p2y12_inhibitor_365 |
| 96 | oral_anticoagulant | core | x:rx_oral_anticoagulant_365 |
| 97 | metformin | core | x:rx_metformin_365 |
| 98 | sulfonylurea | common | x:rx_sulfonylurea_365 |
| 99 | dpp4i | common | x:rx_dpp4_inhibitor_365 |
| 100 | glp1ra | core | x:rx_glp1_ra_365 |
| 101 | sglt2i | core | x:rx_sglt2_inhibitor_365 |
| 102 | insulin | core | x:rx_insulin_365 |
| 103 | nsaid | common | x:rx_nsaid_365 |
| 104 | ppi | common | x:rx_ppi_365 |
| 105 | oral_corticosteroid | common | x:rx_systemic_corticosteroid_365 |
| 106 | opioid | common | x:rx_opioid_365 |
| 107 | antidepressant | common | x:rx_antidepressant_365 |
| 108 | antipsychotic_or_hypnotic | common | x:rx_antipsychotic_365, x:rx_benzodiazepine_365, x:rx_z_drug_hypnotic_365 |
| 109 | copd_asthma_inhaler | common | x:rx_inhaled_respiratory_365 |
| 110 | n_distinct_drug_ingredients | core | x:n_distinct_drugs_365, x:n_med_classes_365 |
| 111 | n_inpatient_admissions | core | x:n_inpatient_stays_365 |
| 112 | inpatient_days | common | v1:inpatient_days_365 |
| 113 | recent_hospitalization_30d | common | x:recent_hosp_30d |
| 114 | n_ed_visits | core | x:n_ed_days_365 |
| 115 | n_outpatient_visits | core | x:n_outpatient_days_365, x:n_office_visits_365 |
| 116 | n_cardiology_visits | common | x:n_cardiology_visits_365 |
| 117 | n_pcp_visits | common | x:n_primary_care_visits_365 |
| 118 | n_ecgs | common | x:n_ecg_days_365 |
| 119 | n_echos | common | x:n_echo_days_365, x:tee_365 |
| 120 | ischemia_testing_or_cath | common | x:stress_test_365, x:cardiac_ct_mri_365, x:prior_cath_ever |
| 121 | lab_test_intensity | common | x:n_lab_results_365, x:n_lab_days_365, x:n_distinct_lab_tests_365, x:n_venipuncture_days_365 |
| 122 | influenza_vaccination | common | x:flu_vaccine_365 |
| 123 | cancer_screening | common | x:colonoscopy_10y, x:mammogram_2y, x:psa_test_2y, x:dxa_2y |
| 126 | sbp | core | x:sbp_mean_365, x:sbp_sd_365, p58:smd_obs_sbp |
| 127 | dbp | common | p58:smd_obs_dbp |
| 128 | heart_rate | common | p58:smd_obs_heart_rate |
| 129 | creatinine | core | p58:smd_obs_creatinine |
| 130 | egfr | core | x:egfr_lt30, p58:pp_LAB__egfr |
| 131 | potassium | common | p58:smd_obs_potassium |
| 132 | sodium | common | p58:smd_obs_sodium |
| 133 | bun | common | p58:pp_LAB__bun |
| 134 | hemoglobin | common | x:hb_lt10, x:lab_hematocrit, p58:smd_obs_hemoglobin |
| 135 | hba1c | core | x:hba1c_ge9, p58:pp_LAB__hba1c |
| 137 | ldl_c | common | x:ldl_lt70, p58:pp_LAB__ldl |
| 138 | hdl_tc_tg | common | x:lab_total_cholesterol, x:lab_hdl, x:lab_triglycerides, x:lab_non_hdl, x:lab_chol_hdl_ratio |
| 139 | natriuretic_peptide | core | x:lab_bnp, p58:pp_BNP__ntprobnp |
| 141 | albumin | common | p58:pp_LAB__albumin |
| 144 | inr | common | x:lab_inr |
| 145 | uacr | common | none (not in extract) |
| 146 | lab_measured_flags | common | x:lab_total_cholesterol_missing, x:lab_hdl_missing, x:lab_triglycerides_missing, x:lab_non_hdl_missing, x:lab_chol_hdl_ratio_missing, x:lab_alt_missing, x:lab_ast_missing, x:lab_alk_phos_missing, x:lab_bilirubin_total_missing, x:lab_bilirubin_direct_missing, x:lab_total_protein_missing, x:lab_globulin_missing, x:lab_inr_missing, x:lab_ptt_missing, x:lab_tsh_missing, x:lab_free_t4_missing, x:lab_uric_acid_missing, x:lab_calcium_missing, x:lab_chloride_missing, x:lab_bicarbonate_missing, x:lab_anion_gap_missing, x:lab_bun_creatinine_ratio_missing, x:lab_crp_missing, x:lab_hs_crp_missing, x:lab_bnp_missing, x:lab_troponin_i_missing, x:lab_troponin_hs_missing, x:lab_hematocrit_missing, x:lab_rdw_missing, x:lab_mcv_missing, x:lab_neutrophils_abs_missing, x:lab_lymphocytes_abs_missing, x:lab_lipoprotein_a_missing, x:lab_osmolality_missing, x:lab_spo2_missing, x:lab_resp_rate_missing, x:lab_temperature_missing, x:lab_weight_kg_missing, x:lab_height_cm_missing, x:lipid_panel_measured_365 |
| 147 | lvef | core | p58:smd_obs_lvef |
| 149 | nyha_class | core | none (notes NLP only) |
| 150 | empirical_hdps_codes | common | none (PS-only construct) |

Set 2 = 275 distinct variables before per-trial availability and PS exclusion.

### Set 3: split-sample selection (half A only; committed before half-B / full)

Rule: Half A only. For each scenario (cell x trial subset), candidates = 58-panel + claude-v16-covars2b non-ECG-proximal variables that are held out from that cell's PS and available (finite |SMD| in base and ECG) in at least half of the scenario's trials. Gain = trial-averaged |SMD| (base) - trial-averaged |SMD| (ECG) over the trials where the variable is available in both arms. Rank by gain (descending; ties by name); take the top 25.

Selection timestamp **2026-09-27 00:11:39 EDT**; halves present at selection: ['A']; pool 405 variables.

| scenario | candidates | selected (half-A gain in mean |SMD|) |
|---|---|---|
| demo / caliper 0.1 (18 trials) | 396 | Echo EF (+0.079), LVEF (+0.076), LVESVi (+0.074), lab weight kg (+0.064), n distinct procedures (+0.064), n distinct dx (+0.061), RV systolic grade (+0.060), elx fluid electrolyte (+0.059), LVIDd (+0.059), elx htn complicated (+0.056), LV systolic grade (+0.055), anemia (+0.053), major surgery anesthesia (+0.050), lab ptt missing (+0.050), n med classes (+0.049), LA volume index (+0.049), LVEDVi (+0.049), n echo days (+0.048), rx potassium supplement (+0.048), bleed any (+0.047), lab neutrophils abs missing (+0.046), BMI (+0.046), e' lateral (+0.045), lab lymphocytes abs missing (+0.045), rx insulin (+0.045) |
| demo / caliper 0.1 (8 physiology trials) | 397 | lab crp (+0.102), AR grade (+0.099), LVIDd (+0.093), LVEF (+0.089), Echo EF (+0.087), lab weight kg (+0.084), elx fluid electrolyte (+0.079), n distinct dx (+0.077), e' lateral (+0.076), LVESVi (+0.073), n distinct procedures (+0.073), LV systolic grade (+0.071), rx potassium supplement (+0.070), elx htn complicated (+0.069), sepsis (+0.069), E/A (+0.067), lab hs crp (+0.066), pneumonia (+0.066), RA pressure (+0.066), rx antibiotic any (+0.066), rx systemic corticosteroid (+0.065), elx obesity (+0.065), Global longitudinal strain (+0.061), BMI (+0.061), RVSP (+0.061) |
| minimal-7 (18 trials) | 385 | LVESVi (+0.072), LVIDd (+0.063), Diastolic grade (+0.063), LVEDVi (+0.063), LVEF (+0.055), lab hs crp (+0.054), Wall-thickness grade (+0.051), Echo EF (+0.050), Mod/severe MR (+0.048), RVSP (+0.046), MR grade (+0.045), TAPSE (+0.036), RA pressure (+0.036), RV size grade (+0.035), pneumonia (+0.035), TR grade (+0.034), sepsis (+0.034), LV diastolic dysfunction (+0.034), elx valvular (+0.033), underweight bmi lt20 (+0.032), mitral regurgitation (+0.032), malnutrition (+0.031), elx weight loss (+0.031), TR peak gradient (+0.031), lab weight kg (+0.030) |
| minimal-7 (8 physiology trials) | 386 | lab hs crp (+0.095), AS grade (+0.088), LVIDd (+0.086), LVEDVi (+0.086), LVESVi (+0.078), RV size grade (+0.071), Diastolic grade (+0.070), lab neutrophils abs (+0.069), AV mean gradient (+0.064), Mod/severe MR (+0.063), TR grade (+0.061), n distinct drugs (+0.058), sepsis (+0.055), n med classes (+0.054), lab temperature (+0.054), LV systolic grade (+0.050), rx systemic corticosteroid (+0.047), rx sedating antihistamine (+0.047), elx weight loss (+0.046), LVEF (+0.046), pneumonia (+0.046), rx antipsychotic (+0.046), MR grade (+0.044), RVSP (+0.043), underweight bmi lt20 (+0.042) |
| common-10 (18 trials) | 371 | lab crp (+0.118), lab troponin i (+0.057), lab hs crp (+0.054), LVIDd (+0.053), Echo EF (+0.048), LV systolic grade (+0.047), LVEF (+0.046), BMI (+0.040), LVESVi (+0.039), lab weight kg (+0.039), pneumonia (+0.038), IVSd (+0.036), LVEDVi (+0.035), sepsis (+0.034), LVPWd (+0.032), pressure ulcer (+0.032), elx other neuro (+0.031), n distinct procedures (+0.030), major surgery anesthesia (+0.030), Diastolic grade (+0.030), NT-proBNP (+0.030), Wall-thickness grade (+0.030), bleed any (+0.029), n distinct drugs (+0.028), RV S' (+0.028) |
| common-10 (8 physiology trials) | 372 | lab crp (+0.219), lab hs crp (+0.107), pneumonia (+0.071), LVIDd (+0.070), hs-Troponin T (+0.065), sepsis (+0.062), lab total protein (+0.062), palliative care (+0.060), hb lt10 (+0.055), lab neutrophils abs (+0.053), RV diameter (+0.053), elx other neuro (+0.052), BMI (+0.052), depression (+0.051), elx depression (+0.051), dnr status (+0.051), pressure ulcer (+0.049), cognitive symptoms (+0.049), lab globulin (+0.049), RV S' (+0.048), LVPWd (+0.047), LVEF (+0.045), bleed any (+0.044), lab weight kg (+0.044), rx h2 blocker (+0.044) |
| sparse (18 trials) | 364 | lab osmolality (+0.075), LVIDd (+0.048), lab weight kg (+0.044), bleed any (+0.042), LA size grade (+0.039), lab troponin hs (+0.038), lab total protein (+0.036), Echo EF (+0.036), elx fluid electrolyte (+0.036), BMI (+0.034), lab ast (+0.034), sepsis (+0.033), lab crp (+0.033), underweight bmi lt20 (+0.032), lab hematocrit (+0.031), LVEF (+0.031), lab bilirubin total (+0.030), pneumonia (+0.030), lab bilirubin direct (+0.030), palliative care (+0.029), tobacco counseling or history (+0.027), RV systolic grade (+0.026), rx potassium supplement (+0.026), intracranial bleed ever (+0.025), n cardiology visits (+0.025) |
| demo (18 trials) | 396 | Echo EF (+0.072), LVEF (+0.070), n distinct procedures (+0.059), lab weight kg (+0.059), elx htn complicated (+0.059), n distinct dx (+0.059), RV systolic grade (+0.058), LVESVi (+0.058), elx fluid electrolyte (+0.057), anemia (+0.052), rx potassium supplement (+0.050), AR grade (+0.049), n echo days (+0.049), LA volume index (+0.048), major surgery anesthesia (+0.047), LVIDd (+0.047), pressure ulcer (+0.047), cci dm uncomplicated (+0.046), n distinct drugs (+0.046), rx insulin (+0.045), lab ptt missing (+0.044), BMI (+0.044), RVSP (+0.043), lab neutrophils abs missing (+0.043), n med classes (+0.042) |
| hdPS200 (18 trials) | 354 | LVIDd (+0.044), lab troponin hs (+0.041), Diastolic grade (+0.033), Mod/severe MR (+0.033), Sodium (+0.029), lab anion gap (+0.028), TAPSE (+0.028), lab non hdl (+0.027), lab uric acid (+0.026), LVEF (+0.026), LV diastolic dysfunction (+0.026), Echo EF (+0.026), e' lateral (+0.024), LDL (+0.024), HbA1c (+0.023), lab lymphocytes abs (+0.023), BMI (+0.023), Diastolic BP (+0.023), AV mean gradient (+0.023), Hemoglobin (+0.022), LVESVi (+0.022), LA volume index (+0.021), lab troponin i (+0.021), lab weight kg (+0.021), Platelets (+0.021) |
| sparse (8 physiology trials) | 365 | LV systolic grade (+0.091), lab osmolality (+0.080), elx fluid electrolyte (+0.079), sepsis (+0.068), lab bilirubin direct (+0.068), lab hematocrit (+0.065), bleed any (+0.064), lab total protein (+0.064), lab calcium (+0.061), LV diastolic dysfunction (+0.060), lab bilirubin total (+0.059), pneumonia (+0.054), rx potassium supplement (+0.054), lab weight kg (+0.051), n distinct drugs (+0.051), BMI (+0.049), hb lt10 (+0.049), elx other neuro (+0.048), LVIDd (+0.047), rx h2 blocker (+0.047), LA size grade (+0.047), underweight bmi lt20 (+0.047), Hemoglobin (+0.046), delirium (+0.045), n cardiology visits (+0.045) |
| demo (8 physiology trials) | 397 | AR grade (+0.119), lab hs crp (+0.092), lab weight kg (+0.089), elx fluid electrolyte (+0.089), n distinct dx (+0.081), LVEF (+0.080), LVIDd (+0.078), e' septal (+0.078), n distinct procedures (+0.077), Echo EF (+0.076), elx htn complicated (+0.073), RA pressure (+0.072), pneumonia (+0.071), rx antibiotic any (+0.069), e' lateral (+0.068), Diastolic grade (+0.066), BMI (+0.065), rx potassium supplement (+0.065), n distinct drugs (+0.064), E/A (+0.063), cci dm uncomplicated (+0.062), n venipuncture days (+0.061), obesity class3 (+0.061), lab crp (+0.060), rx systemic corticosteroid (+0.060) |
| hdPS200 (8 physiology trials) | 354 | Diastolic grade (+0.087), LV diastolic dysfunction (+0.074), lab non hdl (+0.065), lab hs crp (+0.061), TAPSE (+0.058), lab anion gap (+0.057), AV mean gradient (+0.051), lab uric acid (+0.050), e' lateral (+0.044), LVIDd (+0.043), lab osmolality (+0.042), IVSd (+0.041), Platelets (+0.038), LA volume index (+0.038), lab bilirubin direct (+0.037), LDL (+0.037), Diastolic BP (+0.036), lab lymphocytes abs (+0.035), hb lt10 (+0.035), parkinsonism (+0.033), e' septal (+0.033), malnutrition (+0.033), E/A (+0.032), lab troponin i (+0.032), Mod/severe MR (+0.032) |

FULL = the 58-panel plus every claude-v16-covars2b non-ECG-proximal variable held out from the cell's PS (the Set-3 pool).

## Results by scenario

Per trial: % of the set's available variables with |SMD| < 0.1 (primary), mean |SMD|, % > 0.2; averaged over trials. d = ECG − base (pp for %; k = trials improved); p = exact sign-flip over trials; placebo columns: ECG − shufECG / ECG − noise and placebo − base; cluster = sign-flip over comparator clusters; LOO = max p leaving one trial out. Love = number of set variables whose median |SMD| across trials is < 0.1 (p: trial-level arm-swap permutation). q = BH over 9 scenarios × 4 sets × 4 metrics within half. Unmatched values use the same held-out variables as the cell. Set 3 in the full cohort includes half A (the selection sample); half B is the out-of-sample confirmation.

### demo / caliper 0.1 (18 trials)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 41.6 / 43.6 → 55.1 | +11.6 (13/18), 0.001 | +15.2 (<0.001) / +12.0 (<0.001) | -3.6 / -0.4 | 0.008 (8/10) / 0.003 | 12 / 8 → 16 of 28 (0.021) | 9 / 10 | 0.167 → 0.124 (<0.001) | 30.7 → 19.5 (<0.001) | 0.004 / 0.035 / <0.001 / 0.002 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 40.1 / 38.8 → 51.6 | +12.8 (15/18), 0.002 | +13.8 (<0.001) / +10.2 (0.003) | -1.0 / +2.6 | 0.006 (9/10) / 0.005 | 7 / 6 → 17 of 28 (0.004) | 7 / 7 | 0.178 → 0.143 (0.002) | 33.3 → 25.7 (0.031) | 0.007 / 0.011 / 0.005 / 0.042 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 39.3 / 38.4 → 47.6 | +9.2 (14/18), 0.003 | +8.4 (0.012) / +7.4 (0.030) | +0.8 / +1.8 | 0.004 (10/10) / 0.005 | 8 / 6 → 11 of 28 (0.136) | 7 / 8 | 0.179 → 0.143 (<0.001) | 32.7 → 22.1 (<0.001) | 0.010 / 0.180 / 0.002 / 0.004 |
| Set 2: literature core+common | full | 273 (262) | 57.0 / 55.8 → 61.9 | +6.1 (16/18), <0.001 | +7.2 (<0.001) / +6.4 (<0.001) | -1.0 / -0.3 | 0.012 (9/10) / <0.001 | 158 / 160 → 193 of 268 (<0.001) | 154 / 160 | 0.121 → 0.102 (<0.001) | 18.3 → 13.5 (<0.001) | 0.001 / 0.002 / <0.001 / <0.001 |
| Set 2: literature core+common | A | 273 (262) | 55.7 / 52.8 → 60.4 | +7.6 (18/18), <0.001 | +7.0 (<0.001) / +6.7 (<0.001) | +0.6 / +0.8 | 0.002 (10/10) / <0.001 | 161 / 150 → 192 of 268 (<0.001) | 152 / 153 | 0.126 → 0.106 (<0.001) | 19.3 → 14.1 (<0.001) | <0.001 / <0.001 / <0.001 / <0.001 |
| Set 2: literature core+common | B | 273 (262) | 55.3 / 52.2 → 57.9 | +5.7 (16/18), <0.001 | +4.9 (<0.001) / +5.4 (<0.001) | +0.9 / +0.3 | 0.002 (10/10) / <0.001 | 160 / 146 → 176 of 268 (0.005) | 152 / 150 | 0.129 → 0.110 (<0.001) | 20.5 → 15.0 (<0.001) | <0.001 / 0.017 / <0.001 / 0.001 |
| Set 3: split-sample top 25 | full | 25 (25) | 30.2 / 28.5 → 39.4 | +10.9 (14/18), <0.001 | +11.8 (0.005) / +10.7 (<0.001) | -0.9 / +0.2 | 0.008 (9/10) / 0.001 | 3 / 2 → 7 of 25 (0.098) | 3 / 3 | 0.207 → 0.161 (<0.001) | 41.2 → 29.6 (<0.001) | 0.002 / 0.118 / <0.001 / <0.001 |
| Set 3: split-sample top 25 | A | 25 (25) | 32.7 / 28.9 → 41.6 | +12.7 (14/18), 0.004 | +12.9 (<0.001) / +12.3 (0.001) | -0.2 / +0.4 | 0.016 (8/10) / 0.008 | 2 / 2 → 10 of 25 (<0.001) | 2 / 4 | 0.214 → 0.159 (<0.001) | 45.7 → 31.2 (<0.001) | 0.011 / <0.001 / <0.001 / <0.001 |
| Set 3: split-sample top 25 | B | 25 (25) | 29.1 / 28.7 → 36.1 | +7.4 (13/18), 0.012 | +6.0 (0.028) / +7.8 (0.018) | +1.3 / -0.4 | 0.025 (8/10) / 0.023 | 2 / 2 → 4 of 25 (0.310) | 3 / 3 | 0.215 → 0.170 (<0.001) | 43.9 → 34.5 (0.002) | 0.031 / 0.357 / 0.001 / 0.010 |
| Full panel (58 + expanded non-proximal) | full | 405 (388) | 60.6 / 59.9 → 65.3 | +5.4 (17/18), <0.001 | +6.3 (<0.001) / +5.2 (<0.001) | -0.9 / +0.2 | 0.004 (9/10) / <0.001 | 267 / 266 → 309 of 403 (<0.001) | 258 / 269 | 0.111 → 0.096 (<0.001) | 15.3 → 11.6 (<0.001) | <0.001 / <0.001 / <0.001 / <0.001 |
| Full panel (58 + expanded non-proximal) | A | 405 (388) | 59.0 / 56.3 → 62.8 | +6.4 (16/18), <0.001 | +6.3 (<0.001) / +5.8 (<0.001) | +0.1 / +0.6 | 0.004 (9/10) / <0.001 | 267 / 245 → 307 of 403 (<0.001) | 240 / 252 | 0.117 → 0.102 (<0.001) | 16.5 → 12.9 (<0.001) | <0.001 / <0.001 / <0.001 / 0.001 |
| Full panel (58 + expanded non-proximal) | B | 405 (388) | 57.9 / 55.6 → 60.0 | +4.4 (14/18), <0.001 | +3.7 (0.004) / +4.4 (0.003) | +0.6 / -0.0 | 0.006 (9/10) / <0.001 | 262 / 244 → 277 of 403 (0.006) | 245 / 245 | 0.120 → 0.106 (<0.001) | 17.5 → 13.5 (<0.001) | 0.004 / 0.020 / 0.001 / 0.004 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (219) | 58.7 / 57.7 → 62.7 | +5.0 (15/18), <0.001 | +6.1 (<0.001) / +5.5 (<0.001) | -1.1 / -0.4 | 0.021 (9/10) / 0.002 | 138 / 141 → 166 of 224 (0.002) | 136 / 141 | 0.115 → 0.100 (<0.001) | 16.7 → 12.9 (<0.001) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (219) | 57.4 / 54.1 → 61.2 | +7.1 (17/18), <0.001 | +6.5 (<0.001) / +6.1 (0.002) | +0.7 / +1.1 | 0.002 (10/10) / <0.001 | 144 / 130 → 166 of 224 (<0.001) | 132 / 137 | 0.121 → 0.104 (<0.001) | 17.3 → 13.5 (<0.001) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (219) | 56.8 / 53.8 → 58.8 | +5.0 (14/18), <0.001 | +4.2 (0.002) / +4.8 (0.001) | +0.7 / +0.1 | 0.008 (8/10) / 0.001 | 143 / 131 → 150 of 224 (0.028) | 133 / 132 | 0.124 → 0.109 (<0.001) | 19.0 → 14.4 (0.001) | — |

### demo / caliper 0.1 (8 physiology trials)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 44.1 / 46.8 → 57.6 | +10.8 (5/8), 0.125 | +18.0 (0.039) / +14.0 (0.023) | -7.2 / -3.2 | 0.250 (4/7) / 0.250 | 14 / 8 → 15 of 28 (0.203) | 9 / 10 | 0.162 → 0.117 (0.008) | 28.4 → 17.6 (0.016) | 0.145 / 0.225 / 0.016 / 0.027 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 42.7 / 38.2 → 54.5 | +16.3 (7/8), 0.031 | +18.9 (0.008) / +13.1 (0.086) | -2.7 / +3.1 | 0.062 (6/7) / 0.062 | 9 / 6 → 16 of 28 (0.109) | 5 / 10 | 0.177 → 0.136 (0.039) | 31.2 → 25.3 (0.227) | 0.042 / 0.123 / 0.050 / 0.243 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 40.5 / 36.0 → 49.1 | +13.1 (6/8), 0.031 | +12.2 (0.094) / +9.9 (0.125) | +0.9 / +3.2 | 0.062 (5/7) / 0.062 | 11 / 8 → 12 of 28 (0.258) | 8 / 8 | 0.190 → 0.141 (0.016) | 32.4 → 21.6 (0.062) | 0.057 / 0.315 / 0.034 / 0.100 |
| Set 2: literature core+common | full | 273 (263) | 56.3 / 56.1 → 63.2 | +7.1 (7/8), 0.039 | +7.7 (0.023) / +7.0 (0.016) | -0.6 / +0.1 | 0.078 (6/7) / 0.078 | 165 / 165 → 204 of 268 (0.016) | 167 / 170 | 0.120 → 0.100 (0.008) | 18.7 → 13.6 (0.008) | 0.056 / 0.027 / 0.016 / 0.016 |
| Set 2: literature core+common | A | 273 (263) | 54.1 / 52.8 → 61.0 | +8.2 (8/8), 0.008 | +8.4 (0.031) / +7.9 (0.008) | -0.2 / +0.2 | 0.016 (7/7) / 0.016 | 163 / 148 → 196 of 268 (0.039) | 145 / 151 | 0.127 → 0.105 (0.008) | 19.7 → 13.7 (0.016) | 0.015 / 0.050 / 0.015 / 0.026 |
| Set 2: literature core+common | B | 273 (263) | 53.7 / 51.1 → 57.4 | +6.2 (8/8), 0.008 | +5.9 (0.016) / +4.5 (0.102) | +0.4 / +1.8 | 0.016 (7/7) / 0.016 | 140 / 133 → 178 of 268 (0.008) | 135 / 148 | 0.132 → 0.110 (0.008) | 21.0 → 15.7 (0.031) | 0.021 / 0.021 / 0.021 / 0.057 |
| Set 3: split-sample top 25 | full | 25 (25) | 30.0 / 31.0 → 45.0 | +14.0 (8/8), 0.008 | +13.0 (0.062) / +13.5 (0.008) | +1.0 / +0.5 | 0.016 (7/7) / 0.016 | 3 / 3 → 10 of 25 (0.102) | 5 / 4 | 0.196 → 0.145 (0.008) | 36.5 → 24.0 (0.008) | 0.016 / 0.121 / 0.016 / 0.016 |
| Set 3: split-sample top 25 | A | 25 (25) | 30.0 / 26.5 → 50.0 | +23.5 (7/8), 0.031 | +20.0 (0.016) / +19.5 (0.016) | +3.5 / +4.0 | 0.047 (6/7) / 0.062 | 2 / 2 → 14 of 25 (0.016) | 2 / 4 | 0.212 → 0.138 (0.016) | 42.5 → 24.0 (0.016) | 0.042 / 0.026 / 0.026 / 0.026 |
| Set 3: split-sample top 25 | B | 25 (25) | 26.5 / 28.0 → 33.5 | +5.5 (4/8), 0.453 | +6.0 (0.188) / +4.0 (0.453) | -0.5 / +1.5 | 0.438 (4/7) / 0.906 | 3 / 4 → 4 of 25 (1.000) | 4 / 4 | 0.226 → 0.178 (0.023) | 41.0 → 29.0 (0.062) | 0.498 / 1.000 / 0.046 / 0.100 |
| Full panel (58 + expanded non-proximal) | full | 405 (394) | 59.7 / 59.6 → 66.0 | +6.4 (8/8), 0.008 | +7.0 (0.008) / +5.7 (0.008) | -0.6 / +0.7 | 0.016 (7/7) / 0.016 | 276 / 265 → 320 of 403 (0.008) | 273 / 278 | 0.113 → 0.095 (0.008) | 16.2 → 11.8 (0.008) | 0.016 / 0.016 / 0.016 / 0.016 |
| Full panel (58 + expanded non-proximal) | A | 405 (394) | 57.5 / 55.6 → 62.3 | +6.6 (6/8), 0.031 | +7.3 (0.016) / +6.7 (0.008) | -0.6 / -0.1 | 0.062 (5/7) / 0.062 | 270 / 245 → 300 of 403 (0.055) | 236 / 251 | 0.120 → 0.104 (0.023) | 17.7 → 13.5 (0.031) | 0.042 / 0.067 / 0.034 / 0.042 |
| Full panel (58 + expanded non-proximal) | B | 405 (394) | 55.7 / 54.2 → 58.4 | +4.2 (6/8), 0.031 | +4.0 (0.055) / +3.8 (0.164) | +0.3 / +0.4 | 0.062 (5/7) / 0.062 | 235 / 227 → 280 of 403 (0.008) | 231 / 239 | 0.125 → 0.109 (0.016) | 18.7 → 14.4 (0.039) | 0.057 / 0.021 / 0.034 / 0.069 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (222) | 58.8 / 59.0 → 64.8 | +5.8 (7/8), 0.039 | +6.1 (0.039) / +5.6 (0.023) | -0.3 / +0.2 | 0.078 (6/7) / 0.078 | 150 / 146 → 178 of 224 (0.023) | 154 / 152 | 0.112 → 0.096 (0.016) | 16.7 → 12.6 (0.016) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (222) | 56.9 / 55.1 → 62.6 | +7.5 (8/8), 0.008 | +7.7 (0.031) / +6.9 (0.008) | -0.2 / +0.7 | 0.016 (7/7) / 0.016 | 150 / 133 → 172 of 224 (0.109) | 131 / 139 | 0.119 → 0.102 (0.039) | 17.2 → 12.9 (0.016) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (222) | 55.9 / 53.7 → 58.8 | +5.1 (7/8), 0.016 | +5.0 (0.023) / +4.0 (0.141) | +0.1 / +1.2 | 0.031 (6/7) / 0.031 | 126 / 121 → 155 of 224 (0.031) | 120 / 134 | 0.124 → 0.107 (0.016) | 18.8 → 14.8 (0.094) | — |

### minimal-7 (18 trials)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 41.6 / 43.2 → 54.9 | +11.8 (13/18), 0.001 | +9.9 (0.007) / +9.4 (0.002) | +1.8 / +2.4 | 0.059 (7/10) / 0.003 | 12 / 7 → 19 of 28 (0.001) | 12 / 12 | 0.153 → 0.125 (<0.001) | 26.3 → 19.1 (<0.001) | 0.004 / 0.004 / <0.001 / <0.001 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 40.1 / 41.5 → 50.7 | +9.2 (12/18), 0.003 | +10.4 (<0.001) / +9.6 (0.002) | -1.2 / -0.4 | 0.047 (7/10) / 0.006 | 7 / 5 → 18 of 28 (0.003) | 5 / 6 | 0.166 → 0.144 (0.002) | 30.1 → 23.9 (0.021) | 0.009 / 0.008 / 0.007 / 0.033 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 39.3 / 43.6 → 52.0 | +8.4 (10/18), 0.019 | +11.4 (<0.001) / +11.4 (<0.001) | -3.0 / -3.0 | 0.031 (7/10) / 0.039 | 8 / 12 → 18 of 28 (0.128) | 10 / 10 | 0.166 → 0.136 (<0.001) | 29.3 → 22.5 (0.003) | 0.042 / 0.175 / 0.004 / 0.013 |
| Set 2: literature core+common | full | 273 (237) | 57.1 / 63.6 → 68.0 | +4.4 (17/18), <0.001 | +3.9 (<0.001) / +3.5 (<0.001) | +0.5 / +0.9 | 0.002 (10/10) / <0.001 | 144 / 173 → 195 of 243 (<0.001) | 181 / 178 | 0.100 → 0.089 (<0.001) | 12.8 → 9.4 (<0.001) | <0.001 / 0.001 / <0.001 / <0.001 |
| Set 2: literature core+common | A | 273 (237) | 56.1 / 62.4 → 65.5 | +3.0 (12/18), 0.019 | +4.1 (0.001) / +2.7 (0.001) | -1.1 / +0.3 | 0.076 (8/10) / 0.037 | 147 / 174 → 190 of 243 (0.037) | 173 / 178 | 0.103 → 0.094 (<0.001) | 13.1 → 10.4 (0.002) | 0.030 / 0.048 / 0.002 / 0.007 |
| Set 2: literature core+common | B | 273 (236) | 55.3 / 60.7 → 63.7 | +3.0 (13/18), 0.008 | +3.7 (0.003) / +3.0 (0.003) | -0.7 / -0.0 | 0.027 (7/10) / 0.015 | 144 / 171 → 180 of 243 (0.061) | 167 / 175 | 0.105 → 0.096 (<0.001) | 13.6 → 11.5 (0.016) | 0.021 / 0.100 / 0.002 / 0.034 |
| Set 3: split-sample top 25 | full | 25 (25) | 41.8 / 45.1 → 54.7 | +9.6 (14/18), 0.004 | +11.8 (<0.001) / +8.4 (0.018) | -2.2 / +1.1 | 0.047 (7/10) / 0.008 | 8 / 8 → 17 of 25 (0.016) | 8 / 12 | 0.140 → 0.111 (<0.001) | 22.7 → 14.2 (<0.001) | 0.011 / 0.028 / <0.001 / 0.001 |
| Set 3: split-sample top 25 | A | 25 (25) | 40.2 / 40.7 → 57.3 | +16.7 (17/18), <0.001 | +18.7 (<0.001) / +16.0 (<0.001) | -2.0 / +0.7 | 0.004 (9/10) / <0.001 | 5 / 5 → 20 of 25 (<0.001) | 2 / 6 | 0.157 → 0.114 (<0.001) | 27.3 → 17.6 (<0.001) | <0.001 / <0.001 / <0.001 / <0.001 |
| Set 3: split-sample top 25 | B | 25 (25) | 38.9 / 44.4 → 51.3 | +6.9 (11/18), 0.013 | +5.8 (0.053) / +10.7 (0.001) | +1.1 / -3.8 | 0.008 (8/10) / 0.027 | 8 / 9 → 16 of 25 (0.001) | 11 / 8 | 0.143 → 0.120 (0.002) | 23.6 → 16.2 (0.025) | 0.034 / 0.008 / 0.010 / 0.048 |
| Full panel (58 + expanded non-proximal) | full | 405 (377) | 60.7 / 66.2 → 70.0 | +3.9 (17/18), <0.001 | +3.7 (<0.001) / +3.2 (<0.001) | +0.2 / +0.7 | 0.002 (10/10) / <0.001 | 260 / 286 → 314 of 392 (<0.001) | 300 / 300 | 0.095 → 0.085 (<0.001) | 11.5 → 8.6 (<0.001) | <0.001 / <0.001 / <0.001 / <0.001 |
| Full panel (58 + expanded non-proximal) | A | 405 (377) | 59.1 / 64.3 → 66.5 | +2.3 (13/18), 0.015 | +3.7 (<0.001) / +2.8 (<0.001) | -1.4 / -0.6 | 0.061 (8/10) / 0.030 | 259 / 282 → 312 of 392 (0.001) | 279 / 285 | 0.101 → 0.093 (<0.001) | 12.5 → 10.3 (<0.001) | 0.026 / 0.004 / <0.001 / <0.001 |
| Full panel (58 + expanded non-proximal) | B | 405 (377) | 57.8 / 62.3 → 65.5 | +3.2 (13/18), 0.003 | +3.3 (0.002) / +3.1 (0.006) | -0.1 / +0.1 | 0.016 (8/10) / 0.005 | 252 / 278 → 300 of 392 (<0.001) | 275 / 284 | 0.104 → 0.095 (<0.001) | 12.9 → 10.7 (0.007) | 0.010 / 0.004 / 0.004 / 0.021 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (202) | 58.1 / 64.5 → 67.9 | +3.4 (14/18), <0.001 | +3.0 (0.002) / +2.7 (0.002) | +0.4 / +0.7 | 0.002 (10/10) / 0.002 | 125 / 152 → 165 of 207 (0.003) | 157 / 156 | 0.098 → 0.089 (<0.001) | 12.2 → 9.2 (<0.001) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (202) | 57.0 / 63.2 → 65.5 | +2.4 (12/18), 0.051 | +3.7 (0.003) / +2.2 (0.003) | -1.3 / +0.1 | 0.121 (8/10) / 0.099 | 131 / 152 → 162 of 207 (0.101) | 150 / 155 | 0.101 → 0.094 (0.001) | 12.3 → 10.2 (0.006) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (202) | 56.1 / 61.1 → 63.6 | +2.5 (11/18), 0.031 | +2.8 (0.018) / +2.5 (0.011) | -0.3 / +0.0 | 0.084 (7/10) / 0.062 | 128 / 147 → 154 of 207 (0.079) | 146 / 150 | 0.104 → 0.096 (0.001) | 13.0 → 11.4 (0.075) | — |

### minimal-7 (8 physiology trials)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 44.1 / 47.3 → 56.6 | +9.4 (5/8), 0.188 | +11.1 (0.125) / +9.9 (0.031) | -1.8 / -0.5 | 0.344 (4/7) / 0.375 | 14 / 12 → 15 of 28 (0.648) | 12 / 14 | 0.148 → 0.116 (0.008) | 24.3 → 18.0 (0.031) | 0.211 / 0.667 / 0.016 / 0.046 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 42.7 / 39.1 → 49.5 | +10.3 (5/8), 0.094 | +9.9 (0.078) / +5.9 (0.188) | +0.4 / +4.4 | 0.188 (4/7) / 0.188 | 9 / 4 → 13 of 28 (0.164) | 7 / 9 | 0.166 → 0.142 (0.008) | 29.3 → 24.9 (0.250) | 0.109 / 0.180 / 0.015 / 0.267 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 40.5 / 43.2 → 51.4 | +8.2 (4/8), 0.188 | +10.4 (0.086) / +10.0 (0.078) | -2.2 / -1.7 | 0.250 (3/7) / 0.375 | 11 / 11 → 15 of 28 (0.125) | 12 / 11 | 0.176 → 0.130 (0.055) | 32.5 → 21.7 (0.023) | 0.239 / 0.173 / 0.093 / 0.046 |
| Set 2: literature core+common | full | 273 (238) | 56.0 / 61.0 → 66.7 | +5.7 (7/8), 0.016 | +5.6 (0.008) / +4.9 (0.008) | +0.1 / +0.8 | 0.031 (6/7) / 0.031 | 147 / 169 → 194 of 243 (0.031) | 172 / 174 | 0.108 → 0.091 (0.008) | 15.4 → 10.6 (0.031) | 0.027 / 0.046 / 0.016 / 0.046 |
| Set 2: literature core+common | A | 273 (238) | 54.1 / 59.5 → 63.1 | +3.6 (6/8), 0.172 | +5.9 (0.023) / +2.9 (0.070) | -2.3 / +0.7 | 0.203 (5/7) / 0.344 | 148 / 159 → 188 of 243 (0.039) | 151 / 169 | 0.112 → 0.100 (0.070) | 15.5 → 12.6 (0.086) | 0.188 / 0.050 / 0.085 / 0.102 |
| Set 2: literature core+common | B | 273 (238) | 53.2 / 55.6 → 61.2 | +5.7 (7/8), 0.016 | +5.3 (0.062) / +4.7 (0.039) | +0.4 / +1.0 | 0.031 (6/7) / 0.031 | 123 / 132 → 178 of 243 (0.008) | 138 / 147 | 0.117 → 0.102 (0.023) | 17.3 → 13.0 (0.023) | 0.034 / 0.021 / 0.046 / 0.046 |
| Set 3: split-sample top 25 | full | 25 (25) | 36.0 / 37.0 → 46.5 | +9.5 (5/8), 0.062 | +11.0 (0.031) / +9.0 (0.156) | -1.5 / +0.5 | 0.125 (4/7) / 0.125 | 8 / 6 → 9 of 25 (0.297) | 6 / 8 | 0.183 → 0.147 (0.023) | 36.0 → 26.5 (0.031) | 0.082 / 0.319 / 0.038 / 0.046 |
| Set 3: split-sample top 25 | A | 25 (25) | 35.0 / 34.0 → 52.0 | +18.0 (7/8), 0.016 | +19.5 (0.008) / +17.5 (0.031) | -1.5 / +0.5 | 0.031 (6/7) / 0.031 | 8 / 3 → 15 of 25 (0.023) | 2 / 5 | 0.198 → 0.138 (0.008) | 36.5 → 22.5 (0.008) | 0.026 / 0.034 / 0.015 / 0.015 |
| Set 3: split-sample top 25 | B | 25 (25) | 30.5 / 32.5 → 40.0 | +7.5 (6/8), 0.062 | +4.5 (0.391) / +6.0 (0.281) | +3.0 / +1.5 | 0.125 (5/7) / 0.125 | 4 / 5 → 8 of 25 (0.188) | 7 / 3 | 0.201 → 0.167 (0.070) | 39.0 → 29.5 (0.062) | 0.100 / 0.239 / 0.110 / 0.100 |
| Full panel (58 + expanded non-proximal) | full | 405 (384) | 59.6 / 63.8 → 68.8 | +5.0 (7/8), 0.016 | +5.1 (0.016) / +4.9 (0.008) | -0.1 / +0.2 | 0.031 (6/7) / 0.031 | 266 / 293 → 317 of 392 (0.062) | 288 / 298 | 0.102 → 0.088 (0.008) | 13.3 → 9.4 (0.031) | 0.027 / 0.082 / 0.016 / 0.046 |
| Full panel (58 + expanded non-proximal) | A | 405 (384) | 57.3 / 61.0 → 64.2 | +3.2 (6/8), 0.094 | +5.4 (0.016) / +3.2 (0.008) | -2.2 / -0.0 | 0.141 (5/7) / 0.188 | 262 / 265 → 307 of 392 (0.016) | 258 / 277 | 0.109 → 0.098 (0.008) | 14.6 → 11.8 (0.008) | 0.109 / 0.026 / 0.015 / 0.015 |
| Full panel (58 + expanded non-proximal) | B | 405 (384) | 55.4 / 56.9 → 62.5 | +5.6 (6/8), 0.031 | +4.7 (0.055) / +4.3 (0.109) | +0.9 / +1.3 | 0.062 (5/7) / 0.062 | 226 / 236 → 286 of 392 (0.023) | 244 / 250 | 0.115 → 0.100 (0.039) | 15.8 → 11.8 (0.016) | 0.057 / 0.046 / 0.069 / 0.034 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (204) | 58.0 / 63.1 → 67.9 | +4.7 (7/8), 0.023 | +4.9 (0.008) / +4.2 (0.016) | -0.2 / +0.5 | 0.031 (6/7) / 0.047 | 135 / 156 → 170 of 207 (0.031) | 154 / 158 | 0.103 → 0.089 (0.008) | 14.2 → 9.8 (0.031) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (204) | 56.2 / 61.4 → 64.3 | +2.9 (6/8), 0.188 | +5.6 (0.031) / +2.2 (0.078) | -2.7 / +0.7 | 0.234 (5/7) / 0.375 | 137 / 145 → 167 of 207 (0.039) | 137 / 154 | 0.107 → 0.097 (0.070) | 13.9 → 11.7 (0.250) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (204) | 54.9 / 56.3 → 61.6 | +5.3 (7/8), 0.016 | +4.1 (0.109) / +4.1 (0.078) | +1.2 / +1.2 | 0.031 (6/7) / 0.031 | 112 / 116 → 153 of 207 (0.008) | 125 / 130 | 0.113 → 0.100 (0.016) | 16.1 → 12.0 (0.023) | — |

### common-10 (18 trials)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 41.6 / 52.9 → 60.8 | +7.9 (10/18), 0.030 | +7.0 (0.035) / +6.0 (0.033) | +0.8 / +1.9 | 0.078 (7/10) / 0.061 | 12 / 17 → 21 of 28 (0.358) | 16 / 17 | 0.128 → 0.110 (0.023) | 18.5 → 16.2 (0.344) | 0.046 / 0.376 / 0.038 / 0.367 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 40.1 / 51.2 → 57.7 | +6.6 (12/18), 0.030 | +6.3 (0.022) / +4.1 (0.192) | +0.2 / +2.4 | 0.029 (8/10) / 0.060 | 7 / 16 → 21 of 28 (0.099) | 16 / 17 | 0.146 → 0.126 (0.002) | 22.7 → 19.1 (0.044) | 0.042 / 0.114 / 0.006 / 0.056 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 39.3 / 48.2 → 53.0 | +4.8 (11/18), 0.106 | +5.3 (0.017) / +5.7 (0.066) | -0.5 / -0.9 | 0.043 (8/10) / 0.207 | 8 / 11 → 18 of 28 (0.006) | 12 / 11 | 0.137 → 0.121 (0.051) | 20.6 → 19.2 (0.503) | 0.152 / 0.020 / 0.088 / 0.545 |
| Set 2: literature core+common | full | 273 (227) | 58.5 / 69.8 → 73.3 | +3.5 (12/18), 0.003 | +2.2 (0.066) / +2.8 (0.009) | +1.2 / +0.6 | 0.018 (8/10) / 0.007 | 144 / 200 → 208 of 233 (0.161) | 195 / 202 | 0.083 → 0.076 (<0.001) | 7.6 → 6.1 (0.086) | 0.009 / 0.183 / 0.002 / 0.105 |
| Set 2: literature core+common | A | 273 (227) | 57.3 / 67.2 → 72.2 | +4.9 (17/18), <0.001 | +5.3 (<0.001) / +4.3 (<0.001) | -0.4 / +0.7 | 0.002 (10/10) / <0.001 | 146 / 201 → 213 of 233 (0.021) | 198 / 202 | 0.090 → 0.081 (<0.001) | 9.3 → 6.6 (0.001) | <0.001 / 0.033 / <0.001 / 0.004 |
| Set 2: literature core+common | B | 273 (226) | 56.5 / 65.5 → 70.0 | +4.5 (15/18), 0.001 | +4.8 (<0.001) / +3.0 (0.023) | -0.3 / +1.5 | 0.002 (10/10) / 0.002 | 144 / 183 → 205 of 233 (<0.001) | 186 / 192 | 0.091 → 0.083 (0.002) | 9.5 → 7.5 (0.002) | 0.006 / 0.004 / 0.010 / 0.008 |
| Set 3: split-sample top 25 | full | 25 (25) | 38.8 / 46.2 → 53.0 | +6.8 (11/18), 0.036 | +6.5 (0.016) / +6.5 (0.012) | +0.2 / +0.2 | 0.021 (9/10) / 0.072 | 8 / 10 → 13 of 25 (0.245) | 9 / 10 | 0.141 → 0.120 (0.005) | 19.3 → 17.5 (0.291) | 0.053 / 0.267 / 0.012 / 0.315 |
| Set 3: split-sample top 25 | A | 25 (25) | 38.8 / 41.3 → 53.6 | +12.3 (15/18), <0.001 | +10.6 (<0.001) / +6.0 (0.010) | +1.7 / +6.3 | 0.004 (9/10) / <0.001 | 7 / 9 → 14 of 25 (0.013) | 8 / 10 | 0.159 → 0.118 (<0.001) | 25.3 → 16.8 (<0.001) | <0.001 / 0.024 / <0.001 / 0.001 |
| Set 3: split-sample top 25 | B | 25 (25) | 34.8 / 42.7 → 45.2 | +2.5 (9/18), 0.309 | +5.0 (0.084) / +3.6 (0.199) | -2.5 / -1.1 | 0.184 (7/10) / 0.592 | 6 / 8 → 11 of 25 (0.030) | 7 / 7 | 0.147 → 0.135 (0.112) | 24.7 → 21.3 (0.117) | 0.357 / 0.057 / 0.159 / 0.163 |
| Full panel (58 + expanded non-proximal) | full | 405 (363) | 61.1 / 69.7 → 73.4 | +3.7 (15/18), <0.001 | +2.7 (0.023) / +2.9 (0.014) | +1.0 / +0.9 | 0.008 (8/10) / <0.001 | 255 / 313 → 331 of 378 (0.046) | 313 / 319 | 0.084 → 0.077 (0.002) | 7.7 → 6.2 (0.063) | 0.001 / 0.065 / 0.005 / 0.082 |
| Full panel (58 + expanded non-proximal) | A | 405 (363) | 59.5 / 66.8 → 71.3 | +4.5 (16/18), <0.001 | +4.8 (<0.001) / +3.7 (<0.001) | -0.3 / +0.8 | 0.002 (10/10) / <0.001 | 253 / 313 → 331 of 378 (0.006) | 306 / 315 | 0.092 → 0.084 (<0.001) | 9.6 → 7.6 (0.003) | <0.001 / 0.015 / <0.001 / 0.008 |
| Full panel (58 + expanded non-proximal) | B | 405 (363) | 58.2 / 64.9 → 68.9 | +4.0 (16/18), 0.002 | +3.7 (0.003) / +2.6 (0.022) | +0.2 / +1.4 | 0.004 (9/10) / 0.005 | 247 / 285 → 313 of 378 (0.001) | 293 / 295 | 0.094 → 0.087 (0.022) | 9.9 → 8.5 (0.082) | 0.010 / 0.007 / 0.046 / 0.124 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (195) | 59.5 / 70.0 → 72.9 | +2.9 (12/18), 0.012 | +1.6 (0.209) / +2.1 (0.056) | +1.3 / +0.8 | 0.021 (8/10) / 0.024 | 127 / 174 → 178 of 200 (0.393) | 170 / 176 | 0.083 → 0.076 (0.002) | 7.2 → 6.1 (0.214) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (195) | 58.3 / 67.6 → 72.2 | +4.6 (16/18), <0.001 | +5.0 (<0.001) / +3.8 (<0.001) | -0.4 / +0.8 | 0.002 (10/10) / <0.001 | 131 / 172 → 183 of 200 (0.009) | 170 / 173 | 0.088 → 0.081 (<0.001) | 8.7 → 6.5 (0.004) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (195) | 57.4 / 65.3 → 69.7 | +4.4 (15/18), 0.002 | +4.2 (0.003) / +2.5 (0.066) | +0.2 / +1.9 | 0.004 (9/10) / 0.003 | 129 / 157 → 175 of 200 (0.003) | 161 / 165 | 0.091 → 0.084 (0.005) | 9.4 → 7.8 (0.007) | — |

### common-10 (8 physiology trials)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 44.1 / 50.8 → 63.1 | +12.3 (6/8), 0.117 | +15.0 (0.047) / +5.9 (0.406) | -2.7 / +6.4 | 0.188 (5/7) / 0.234 | 14 / 13 → 22 of 28 (0.055) | 13 / 16 | 0.136 → 0.102 (0.047) | 19.9 → 13.5 (0.156) | 0.138 / 0.075 / 0.065 / 0.179 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 42.7 / 48.6 → 58.4 | +9.9 (6/8), 0.047 | +6.7 (0.094) / +7.2 (0.156) | +3.2 / +2.7 | 0.094 (5/7) / 0.094 | 9 / 10 → 19 of 28 (0.008) | 12 / 13 | 0.147 → 0.122 (0.008) | 22.6 → 18.6 (0.109) | 0.059 / 0.015 / 0.015 / 0.123 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 40.5 / 41.4 → 52.2 | +10.8 (6/8), 0.055 | +7.7 (0.094) / +8.6 (0.203) | +3.1 / +2.2 | 0.109 (5/7) / 0.109 | 11 / 11 → 14 of 28 (0.297) | 12 / 13 | 0.152 → 0.124 (0.070) | 22.1 → 20.3 (0.625) | 0.093 / 0.353 / 0.110 / 0.652 |
| Set 2: literature core+common | full | 273 (228) | 57.0 / 64.5 → 70.7 | +6.2 (6/8), 0.031 | +4.0 (0.148) / +5.0 (0.047) | +2.2 / +1.2 | 0.031 (6/7) / 0.062 | 141 / 186 → 198 of 233 (0.211) | 185 / 181 | 0.095 → 0.081 (0.016) | 11.0 → 7.5 (0.047) | 0.046 / 0.232 / 0.027 / 0.065 |
| Set 2: literature core+common | A | 273 (228) | 55.2 / 63.0 → 67.6 | +4.6 (8/8), 0.008 | +5.1 (0.016) / +4.4 (0.008) | -0.5 / +0.2 | 0.016 (7/7) / 0.016 | 144 / 176 → 199 of 233 (0.016) | 179 / 179 | 0.100 → 0.088 (0.008) | 12.8 → 8.6 (0.008) | 0.015 / 0.026 / 0.015 / 0.015 |
| Set 2: literature core+common | B | 273 (228) | 54.2 / 58.3 → 65.8 | +7.6 (8/8), 0.008 | +7.8 (0.016) / +5.3 (0.062) | -0.2 / +2.2 | 0.016 (7/7) / 0.016 | 120 / 143 → 193 of 233 (0.016) | 142 / 172 | 0.107 → 0.091 (0.016) | 13.2 → 10.0 (0.016) | 0.021 / 0.034 / 0.034 / 0.034 |
| Set 3: split-sample top 25 | full | 25 (25) | 43.6 / 39.7 → 51.3 | +11.6 (5/8), 0.062 | +12.2 (0.109) / +10.6 (0.094) | -0.6 / +1.0 | 0.094 (5/7) / 0.125 | 11 / 9 → 14 of 25 (0.148) | 8 / 11 | 0.155 → 0.121 (0.008) | 23.6 → 16.1 (0.016) | 0.082 / 0.171 / 0.016 / 0.027 |
| Set 3: split-sample top 25 | A | 25 (25) | 42.1 / 31.2 → 51.8 | +20.6 (8/8), 0.008 | +13.1 (0.031) / +11.6 (0.016) | +7.5 / +9.0 | 0.016 (7/7) / 0.016 | 10 / 6 → 13 of 25 (0.023) | 9 / 9 | 0.178 → 0.116 (0.008) | 29.6 → 15.5 (0.023) | 0.015 / 0.034 / 0.015 / 0.034 |
| Set 3: split-sample top 25 | B | 25 (25) | 37.7 / 33.6 → 43.8 | +10.1 (6/8), 0.086 | +12.2 (0.094) / +7.1 (0.273) | -2.0 / +3.0 | 0.062 (6/7) / 0.172 | 9 / 7 → 10 of 25 (0.453) | 4 / 8 | 0.172 → 0.141 (0.008) | 33.1 → 24.1 (0.016) | 0.128 / 0.498 / 0.021 / 0.034 |
| Full panel (58 + expanded non-proximal) | full | 405 (370) | 59.7 / 64.3 → 71.0 | +6.7 (7/8), 0.016 | +5.0 (0.055) / +5.0 (0.047) | +1.7 / +1.7 | 0.031 (6/7) / 0.031 | 255 / 288 → 319 of 378 (0.023) | 292 / 297 | 0.096 → 0.081 (0.016) | 10.9 → 7.3 (0.016) | 0.027 / 0.038 / 0.027 / 0.027 |
| Full panel (58 + expanded non-proximal) | A | 405 (370) | 57.6 / 62.3 → 67.6 | +5.3 (8/8), 0.008 | +5.4 (0.008) / +5.1 (0.023) | -0.1 / +0.2 | 0.016 (7/7) / 0.016 | 254 / 274 → 309 of 378 (0.008) | 285 / 282 | 0.102 → 0.090 (0.008) | 12.3 → 9.4 (0.023) | 0.015 / 0.015 / 0.015 / 0.034 |
| Full panel (58 + expanded non-proximal) | B | 405 (370) | 55.6 / 57.0 → 64.5 | +7.5 (8/8), 0.008 | +6.7 (0.023) / +4.6 (0.070) | +0.8 / +3.0 | 0.016 (7/7) / 0.016 | 218 / 230 → 293 of 378 (0.008) | 244 / 275 | 0.111 → 0.094 (0.008) | 13.9 → 10.6 (0.016) | 0.021 / 0.021 / 0.021 / 0.034 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (198) | 58.9 / 65.8 → 71.3 | +5.6 (6/8), 0.039 | +3.4 (0.203) / +4.5 (0.047) | +2.2 / +1.0 | 0.031 (6/7) / 0.078 | 130 / 166 → 173 of 200 (0.438) | 165 / 162 | 0.092 → 0.079 (0.016) | 10.0 → 7.0 (0.031) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (198) | 57.2 / 64.3 → 68.5 | +4.2 (7/8), 0.016 | +4.8 (0.023) / +3.8 (0.062) | -0.6 / +0.4 | 0.016 (7/7) / 0.031 | 134 / 158 → 174 of 200 (0.062) | 159 / 164 | 0.096 → 0.086 (0.008) | 11.4 → 8.1 (0.023) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (198) | 55.9 / 58.1 → 66.0 | +7.9 (8/8), 0.008 | +7.1 (0.023) / +4.5 (0.125) | +0.8 / +3.4 | 0.016 (7/7) / 0.016 | 110 / 120 → 168 of 200 (0.016) | 128 / 156 | 0.106 → 0.090 (0.008) | 12.7 → 9.9 (0.031) | — |

### sparse (18 trials) (reference)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 41.6 / 58.0 → 61.6 | +3.6 (11/18), 0.193 | +4.4 (0.119) / +2.8 (0.421) | -0.8 / +0.8 | 0.070 (6/10) / 0.371 | 12 / 21 → 21 of 28 (1.000) | 19 / 19 | 0.119 → 0.108 (0.098) | 18.3 → 15.1 (0.045) | 0.215 / 1.000 / 0.118 / 0.064 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 40.1 / 54.5 → 56.6 | +2.1 (10/18), 0.289 | +4.4 (0.117) / +2.4 (0.371) | -2.4 / -0.4 | 0.674 (7/10) / 0.525 | 7 / 17 → 21 of 28 (0.276) | 16 / 18 | 0.131 → 0.120 (0.083) | 19.9 → 18.9 (0.517) | 0.303 / 0.292 / 0.100 / 0.535 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 39.3 / 53.1 → 54.4 | +1.2 (7/18), 0.621 | +3.2 (0.310) / +4.2 (0.066) | -2.0 / -3.0 | 0.688 (5/10) / 0.991 | 8 / 16 → 15 of 28 (0.840) | 15 / 12 | 0.135 → 0.124 (0.105) | 21.1 → 18.7 (0.208) | 0.652 / 0.858 / 0.151 / 0.261 |
| Set 2: literature core+common | full | 273 (212) | 58.4 / 72.2 → 75.1 | +2.9 (12/18), 0.026 | +2.7 (0.010) / +2.5 (0.014) | +0.2 / +0.4 | 0.041 (7/10) / 0.052 | 138 / 203 → 205 of 227 (0.576) | 205 / 204 | 0.080 → 0.072 (<0.001) | 6.9 → 5.0 (0.011) | 0.041 / 0.601 / 0.002 / 0.022 |
| Set 2: literature core+common | A | 273 (212) | 57.1 / 70.5 → 72.9 | +2.4 (15/18), 0.012 | +3.7 (0.003) / +2.6 (0.020) | -1.3 / -0.2 | 0.094 (9/10) / 0.023 | 142 / 200 → 208 of 227 (0.102) | 203 / 199 | 0.083 → 0.077 (0.005) | 7.2 → 5.9 (0.033) | 0.022 / 0.117 / 0.015 / 0.044 |
| Set 2: literature core+common | B | 273 (212) | 56.7 / 68.5 → 70.5 | +1.9 (10/18), 0.237 | +3.1 (0.061) / +2.1 (0.157) | -1.2 / -0.2 | 0.436 (6/10) / 0.471 | 139 / 196 → 199 of 227 (0.648) | 194 / 191 | 0.085 → 0.081 (0.133) | 7.7 → 7.0 (0.262) | 0.294 / 0.671 / 0.179 / 0.317 |
| Set 3: split-sample top 25 | full | 25 (25) | 42.1 / 53.3 → 60.9 | +7.6 (14/18), 0.012 | +10.0 (<0.001) / +8.1 (0.002) | -2.4 / -0.5 | 0.023 (8/10) / 0.024 | 9 / 14 → 19 of 25 (0.007) | 14 / 13 | 0.122 → 0.102 (<0.001) | 17.4 → 11.7 (0.001) | 0.024 / 0.016 / 0.002 / 0.004 |
| Set 3: split-sample top 25 | A | 25 (25) | 41.7 / 47.3 → 60.7 | +13.3 (17/18), <0.001 | +15.7 (<0.001) / +13.9 (<0.001) | -2.4 / -0.6 | 0.004 (9/10) / <0.001 | 7 / 11 → 18 of 25 (0.055) | 12 / 11 | 0.141 → 0.107 (<0.001) | 19.6 → 13.7 (0.007) | <0.001 / 0.067 / <0.001 / 0.015 |
| Set 3: split-sample top 25 | B | 25 (25) | 39.9 / 48.8 → 53.9 | +5.1 (12/18), 0.097 | +2.3 (0.469) / +4.9 (0.144) | +2.7 / +0.1 | 0.164 (7/10) / 0.180 | 8 / 11 → 14 of 25 (0.285) | 13 / 11 | 0.132 → 0.119 (0.036) | 18.7 → 16.7 (0.309) | 0.142 / 0.342 / 0.064 / 0.357 |
| Full panel (58 + expanded non-proximal) | full | 405 (354) | 60.9 / 72.7 → 75.3 | +2.7 (12/18), 0.029 | +2.9 (0.003) / +2.7 (0.004) | -0.2 / -0.1 | 0.061 (7/10) / 0.058 | 248 / 325 → 328 of 371 (0.608) | 321 / 322 | 0.081 → 0.074 (<0.001) | 7.3 → 5.5 (0.003) | 0.046 / 0.630 / 0.003 / 0.008 |
| Full panel (58 + expanded non-proximal) | A | 405 (354) | 59.3 / 69.3 → 72.3 | +2.9 (15/18), 0.005 | +3.8 (0.003) / +3.0 (0.015) | -0.9 / -0.1 | 0.049 (9/10) / 0.009 | 246 / 311 → 333 of 371 (0.011) | 314 / 311 | 0.087 → 0.082 (0.023) | 8.1 → 7.2 (0.149) | 0.012 / 0.020 / 0.034 / 0.167 |
| Full panel (58 + expanded non-proximal) | B | 405 (354) | 58.2 / 68.0 → 70.0 | +2.1 (10/18), 0.133 | +3.1 (0.059) / +2.5 (0.044) | -1.0 / -0.4 | 0.283 (6/10) / 0.259 | 242 / 307 → 312 of 371 (0.543) | 304 / 293 | 0.088 → 0.084 (0.076) | 8.2 → 7.7 (0.373) | 0.179 / 0.584 / 0.116 / 0.423 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (188) | 59.1 / 72.0 → 74.8 | +2.9 (12/18), 0.034 | +2.6 (0.012) / +2.5 (0.012) | +0.3 / +0.4 | 0.051 (7/10) / 0.068 | 121 / 172 → 175 of 194 (0.348) | 174 / 173 | 0.079 → 0.072 (<0.001) | 6.5 → 4.8 (0.006) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (188) | 57.8 / 70.3 → 72.7 | +2.3 (15/18), 0.017 | +3.6 (0.006) / +2.3 (0.042) | -1.3 / -0.0 | 0.117 (9/10) / 0.031 | 125 / 169 → 177 of 194 (0.101) | 173 / 168 | 0.082 → 0.077 (0.015) | 6.8 → 5.9 (0.110) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (188) | 57.3 / 68.0 → 69.9 | +1.9 (9/18), 0.248 | +3.1 (0.066) / +2.2 (0.164) | -1.2 / -0.3 | 0.463 (6/10) / 0.494 | 124 / 168 → 169 of 194 (0.916) | 163 / 161 | 0.085 → 0.082 (0.221) | 7.4 → 7.2 (0.657) | — |

### demo (18 trials) (reference)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 41.6 / 43.8 → 53.6 | +9.8 (13/18), 0.003 | +12.4 (0.001) / +9.8 (0.002) | -2.6 / +0.0 | 0.010 (8/10) / 0.005 | 12 / 10 → 17 of 28 (0.021) | 8 / 10 | 0.166 → 0.126 (<0.001) | 30.7 → 19.7 (<0.001) | 0.008 / 0.035 / <0.001 / <0.001 |
| Set 1: clinical ECG-relevant | A | 28 (28) | 40.1 / 40.5 → 51.2 | +10.6 (14/18), 0.013 | +12.2 (<0.001) / +10.6 (<0.001) | -1.6 / -0.0 | 0.018 (9/10) / 0.025 | 7 / 6 → 15 of 28 (0.033) | 7 / 7 | 0.177 → 0.145 (0.002) | 32.7 → 27.3 (0.030) | 0.023 / 0.044 / 0.007 / 0.042 |
| Set 1: clinical ECG-relevant | B | 28 (28) | 39.3 / 37.8 → 47.6 | +9.8 (15/18), 0.002 | +9.6 (0.004) / +6.0 (0.073) | +0.2 / +3.8 | 0.004 (9/10) / 0.004 | 8 / 6 → 11 of 28 (0.192) | 7 / 8 | 0.182 → 0.145 (<0.001) | 33.3 → 22.9 (0.002) | 0.010 / 0.242 / 0.003 / 0.008 |
| Set 2: literature core+common | full | 273 (262) | 57.0 / 55.9 → 61.9 | +6.0 (16/18), <0.001 | +7.0 (<0.001) / +5.8 (<0.001) | -1.0 / +0.2 | 0.012 (9/10) / <0.001 | 158 / 162 → 191 of 268 (0.001) | 156 / 162 | 0.120 → 0.102 (<0.001) | 18.0 → 13.4 (<0.001) | 0.001 / 0.004 / <0.001 / <0.001 |
| Set 2: literature core+common | A | 273 (262) | 55.7 / 53.8 → 60.8 | +7.0 (18/18), <0.001 | +7.5 (<0.001) / +6.5 (<0.001) | -0.6 / +0.5 | 0.002 (10/10) / <0.001 | 161 / 154 → 188 of 268 (0.006) | 149 / 163 | 0.124 → 0.105 (<0.001) | 18.5 → 14.0 (<0.001) | <0.001 / 0.015 / <0.001 / <0.001 |
| Set 2: literature core+common | B | 273 (262) | 55.3 / 52.6 → 58.5 | +6.0 (16/18), <0.001 | +4.6 (<0.001) / +5.1 (<0.001) | +1.4 / +0.8 | 0.004 (9/10) / <0.001 | 160 / 145 → 184 of 268 (<0.001) | 151 / 152 | 0.128 → 0.109 (<0.001) | 20.0 → 14.7 (<0.001) | <0.001 / 0.001 / <0.001 / <0.001 |
| Set 3: split-sample top 25 | full | 25 (25) | 33.5 / 31.9 → 40.2 | +8.3 (13/18), 0.012 | +8.5 (0.005) / +9.2 (0.001) | -0.2 / -0.9 | 0.061 (8/10) / 0.024 | 6 / 6 → 10 of 25 (0.082) | 6 / 6 | 0.198 → 0.156 (<0.001) | 38.4 → 27.2 (<0.001) | 0.024 / 0.101 / <0.001 / <0.001 |
| Set 3: split-sample top 25 | A | 25 (25) | 34.4 / 32.6 → 43.8 | +11.2 (14/18), <0.001 | +12.2 (<0.001) / +11.9 (<0.001) | -0.9 / -0.7 | 0.004 (9/10) / <0.001 | 3 / 4 → 10 of 25 (0.015) | 4 / 5 | 0.204 → 0.153 (<0.001) | 43.0 → 29.9 (<0.001) | 0.001 / 0.026 / <0.001 / <0.001 |
| Set 3: split-sample top 25 | B | 25 (25) | 32.2 / 31.9 → 39.2 | +7.2 (13/18), 0.009 | +6.1 (<0.001) / +7.4 (0.010) | +1.1 / -0.2 | 0.031 (7/10) / 0.019 | 5 / 6 → 6 of 25 (1.000) | 6 / 6 | 0.203 → 0.163 (<0.001) | 39.6 → 31.0 (0.003) | 0.025 / 1.000 / 0.002 / 0.010 |
| Full panel (58 + expanded non-proximal) | full | 405 (388) | 60.6 / 59.8 → 65.3 | +5.5 (17/18), <0.001 | +6.0 (<0.001) / +5.0 (<0.001) | -0.5 / +0.5 | 0.002 (10/10) / <0.001 | 267 / 268 → 306 of 403 (<0.001) | 260 / 271 | 0.110 → 0.096 (<0.001) | 15.2 → 11.4 (<0.001) | <0.001 / 0.001 / <0.001 / <0.001 |
| Full panel (58 + expanded non-proximal) | A | 405 (388) | 59.0 / 57.5 → 63.2 | +5.7 (16/18), <0.001 | +6.8 (<0.001) / +6.2 (<0.001) | -1.1 / -0.5 | 0.004 (9/10) / <0.001 | 267 / 253 → 300 of 403 (0.001) | 243 / 259 | 0.116 → 0.102 (<0.001) | 15.9 → 12.8 (<0.001) | <0.001 / 0.005 / <0.001 / 0.001 |
| Full panel (58 + expanded non-proximal) | B | 405 (388) | 57.9 / 56.0 → 60.6 | +4.5 (17/18), <0.001 | +3.8 (<0.001) / +4.3 (0.001) | +0.7 / +0.2 | 0.004 (9/10) / <0.001 | 262 / 246 → 284 of 403 (0.001) | 249 / 248 | 0.120 → 0.106 (<0.001) | 17.2 → 13.2 (<0.001) | 0.001 / 0.008 / <0.001 / 0.003 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (219) | 58.7 / 57.6 → 62.7 | +5.1 (15/18), <0.001 | +5.8 (<0.001) / +5.0 (<0.001) | -0.7 / +0.1 | 0.025 (9/10) / 0.002 | 138 / 143 → 165 of 224 (0.006) | 139 / 143 | 0.115 → 0.100 (<0.001) | 16.5 → 12.6 (<0.001) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (219) | 57.4 / 55.1 → 61.4 | +6.2 (17/18), <0.001 | +6.8 (<0.001) / +5.6 (<0.001) | -0.6 / +0.6 | 0.002 (10/10) / <0.001 | 144 / 133 → 160 of 224 (0.020) | 130 / 143 | 0.119 → 0.104 (<0.001) | 16.5 → 13.3 (0.003) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (219) | 56.8 / 54.2 → 59.5 | +5.3 (17/18), <0.001 | +4.0 (<0.001) / +4.5 (0.002) | +1.3 / +0.8 | 0.004 (9/10) / <0.001 | 143 / 132 → 160 of 224 (<0.001) | 133 / 133 | 0.123 → 0.107 (<0.001) | 18.6 → 14.2 (<0.001) | — |

### hdPS200 (18 trials) (reference)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (27) | 42.0 / 62.6 → 67.7 | +5.1 (11/18), 0.073 | +2.5 (0.344) / +4.5 (0.061) | +2.6 / +0.6 | 0.072 (7/10) / 0.141 | 13 / 19 → 25 of 28 (0.015) | 23 / 22 | 0.101 → 0.090 (0.010) | 11.3 → 10.9 (0.906) | 0.092 / 0.027 / 0.020 / 0.913 |
| Set 1: clinical ECG-relevant | A | 28 (27) | 40.8 / 57.3 → 57.7 | +0.4 (7/18), 0.865 | +0.8 (0.763) / -0.9 (0.641) | -0.4 / +1.3 | 0.309 (5/10) / 1.000 | 8 / 17 → 21 of 28 (0.176) | 20 / 18 | 0.125 → 0.117 (0.089) | 19.5 → 18.6 (0.678) | 0.877 / 0.190 / 0.105 / 0.697 |
| Set 1: clinical ECG-relevant | B | 28 (27) | 39.6 / 59.2 → 63.0 | +3.7 (10/18), 0.151 | +6.7 (0.044) / +5.5 (0.135) | -3.0 / -1.8 | 0.238 (8/10) / 0.297 | 8 / 22 → 24 of 28 (0.556) | 18 / 19 | 0.114 → 0.107 (0.307) | 15.6 → 12.4 (0.079) | 0.198 / 0.593 / 0.357 / 0.119 |
| Set 2: literature core+common | full | 273 (185) | 61.0 / 87.4 → 87.7 | +0.3 (9/18), 0.688 | +0.8 (0.184) / +0.3 (0.698) | -0.5 / -0.1 | 0.760 (6/10) / 0.900 | 154 / 223 → 222 of 226 (0.743) | 222 / 222 | 0.050 → 0.049 (0.059) | 2.1 → 1.7 (0.055) | 0.702 / 0.754 / 0.079 / 0.075 |
| Set 2: literature core+common | A | 273 (186) | 59.9 / 83.6 → 83.7 | +0.1 (11/18), 0.902 | +1.3 (0.136) / +0.8 (0.178) | -1.1 / -0.7 | 0.816 (6/10) / 0.986 | 150 / 222 → 223 of 226 (0.830) | 221 / 222 | 0.059 → 0.057 (0.051) | 3.4 → 2.9 (0.023) | 0.908 / 0.847 / 0.063 / 0.034 |
| Set 2: literature core+common | B | 273 (184) | 59.6 / 83.3 → 84.4 | +1.0 (8/18), 0.425 | +2.2 (0.095) / +1.7 (0.086) | -1.2 / -0.7 | 0.330 (5/10) / 0.805 | 150 / 218 → 220 of 225 (0.483) | 218 / 219 | 0.060 → 0.059 (0.253) | 3.8 → 3.6 (0.329) | 0.475 / 0.527 / 0.312 / 0.376 |
| Set 3: split-sample top 25 | full | 25 (25) | 47.0 / 63.7 → 68.3 | +4.7 (10/18), 0.081 | +3.4 (0.153) / +6.0 (0.013) | +1.3 / -1.3 | 0.021 (8/10) / 0.153 | 10 / 18 → 21 of 25 (0.354) | 19 / 16 | 0.099 → 0.085 (<0.001) | 12.5 → 9.1 (0.121) | 0.101 / 0.375 / 0.002 / 0.141 |
| Set 3: split-sample top 25 | A | 25 (25) | 47.2 / 54.7 → 62.5 | +7.8 (14/18), <0.001 | +3.4 (0.190) / +2.9 (0.085) | +4.5 / +4.9 | 0.004 (9/10) / <0.001 | 9 / 15 → 19 of 25 (0.034) | 16 / 17 | 0.132 → 0.106 (<0.001) | 20.8 → 14.7 (0.007) | 0.001 / 0.045 / <0.001 / 0.015 |
| Set 3: split-sample top 25 | B | 25 (25) | 43.4 / 59.2 → 62.8 | +3.6 (10/18), 0.073 | +4.0 (0.090) / +2.9 (0.119) | -0.5 / +0.7 | 0.176 (6/10) / 0.145 | 9 / 20 → 20 of 25 (1.000) | 17 / 17 | 0.123 → 0.116 (0.183) | 17.1 → 14.7 (0.105) | 0.114 / 1.000 / 0.238 / 0.151 |
| Full panel (58 + expanded non-proximal) | full | 405 (322) | 62.8 / 86.1 → 86.8 | +0.7 (13/18), 0.083 | +0.7 (0.154) / +0.5 (0.222) | -0.0 / +0.2 | 0.025 (9/10) / 0.160 | 263 / 352 → 358 of 368 (0.077) | 357 / 353 | 0.053 → 0.051 (<0.001) | 2.9 → 2.5 (0.064) | 0.102 / 0.097 / 0.003 / 0.082 |
| Full panel (58 + expanded non-proximal) | A | 405 (323) | 61.1 / 81.0 → 81.0 | +0.0 (10/18), 0.991 | +0.2 (0.715) / -0.1 (0.856) | -0.2 / +0.1 | 0.805 (6/10) / 0.990 | 252 / 344 → 348 of 368 (0.401) | 346 / 347 | 0.066 → 0.064 (0.031) | 5.3 → 4.9 (0.156) | 0.991 / 0.418 / 0.042 / 0.173 |
| Full panel (58 + expanded non-proximal) | B | 405 (318) | 60.3 / 81.3 → 82.3 | +1.1 (12/18), 0.136 | +1.8 (0.055) / +1.3 (0.063) | -0.7 / -0.3 | 0.084 (7/10) / 0.267 | 252 / 350 → 352 of 367 (0.742) | 344 / 345 | 0.065 → 0.065 (0.579) | 5.0 → 4.8 (0.384) | 0.180 / 0.763 / 0.613 / 0.432 |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (166) | 61.4 / 87.8 → 87.8 | +0.1 (8/18), 0.921 | +0.7 (0.233) / +0.2 (0.843) | -0.6 / -0.1 | 0.930 (5/10) / 0.999 | 133 / 191 → 192 of 193 (0.700) | 191 / 191 | 0.049 → 0.048 (0.195) | 1.6 → 1.4 (0.115) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (166) | 60.3 / 83.9 → 83.7 | -0.2 (9/18), 0.807 | +0.9 (0.318) / +0.4 (0.562) | -1.2 / -0.7 | 0.781 (5/10) / 0.934 | 129 / 190 → 191 of 193 (0.830) | 189 / 190 | 0.058 → 0.056 (0.152) | 2.9 → 2.6 (0.078) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (164) | 60.0 / 83.7 → 84.5 | +0.8 (8/18), 0.539 | +2.3 (0.092) / +1.3 (0.198) | -1.5 / -0.6 | 0.465 (4/10) / 0.957 | 132 / 187 → 189 of 192 (0.483) | 187 / 188 | 0.059 → 0.059 (0.653) | 3.5 → 3.5 (0.791) | — |

### sparse (8 physiology trials) (descriptive; not in the FDR family)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 44.1 / 57.6 → 65.3 | +7.7 (6/8), 0.086 | +7.7 (0.141) / +8.2 (0.211) | +0.0 / -0.5 | 0.078 (6/7) / 0.172 | 14 / 19 → 20 of 28 (0.859) | 18 / 15 | 0.125 → 0.103 (0.086) | 18.1 → 14.0 (0.250) | — |
| Set 1: clinical ECG-relevant | A | 28 (28) | 42.7 / 50.8 → 54.0 | +3.2 (4/8), 0.297 | +3.2 (0.469) / +4.5 (0.375) | -0.0 / -1.3 | 0.281 (4/7) / 0.594 | 9 / 15 → 17 of 28 (0.719) | 12 / 14 | 0.137 → 0.119 (0.125) | 20.4 → 19.0 (0.703) | — |
| Set 1: clinical ECG-relevant | B | 28 (28) | 40.5 / 49.9 → 54.9 | +5.0 (5/8), 0.203 | +9.0 (0.062) / +7.2 (0.031) | -4.1 / -2.2 | 0.125 (5/7) / 0.406 | 11 / 14 → 15 of 28 (0.875) | 14 / 13 | 0.146 → 0.120 (0.062) | 22.6 → 17.6 (0.031) | — |
| Set 2: literature core+common | full | 273 (222) | 56.6 / 65.1 → 70.3 | +5.2 (6/8), 0.078 | +5.0 (0.016) / +4.7 (0.039) | +0.2 / +0.5 | 0.109 (6/7) / 0.156 | 136 / 175 → 193 of 227 (0.008) | 177 / 175 | 0.094 → 0.082 (0.016) | 11.4 → 7.7 (0.047) | — |
| Set 2: literature core+common | A | 273 (222) | 54.8 / 64.8 → 68.4 | +3.6 (7/8), 0.016 | +4.7 (0.023) / +4.4 (0.062) | -1.1 / -0.8 | 0.016 (7/7) / 0.031 | 138 / 177 → 193 of 227 (0.047) | 160 / 175 | 0.096 → 0.087 (0.008) | 11.6 → 8.7 (0.031) | — |
| Set 2: literature core+common | B | 273 (222) | 54.3 / 61.1 → 64.9 | +3.8 (6/8), 0.281 | +6.2 (0.062) / +4.2 (0.164) | -2.4 / -0.4 | 0.297 (5/7) / 0.562 | 115 / 160 → 186 of 227 (0.133) | 154 / 163 | 0.101 → 0.091 (0.062) | 12.2 → 10.2 (0.070) | — |
| Set 3: split-sample top 25 | full | 25 (25) | 37.0 / 38.5 → 49.0 | +10.5 (6/8), 0.078 | +11.5 (0.086) / +15.0 (0.023) | -1.0 / -4.5 | 0.094 (6/7) / 0.156 | 8 / 9 → 12 of 25 (0.453) | 8 / 7 | 0.160 → 0.131 (0.031) | 27.5 → 16.5 (0.016) | — |
| Set 3: split-sample top 25 | A | 25 (25) | 37.5 / 31.5 → 53.0 | +21.5 (8/8), 0.008 | +16.0 (0.078) / +19.0 (0.023) | +5.5 / +2.5 | 0.016 (7/7) / 0.016 | 8 / 4 → 12 of 25 (0.117) | 4 / 5 | 0.181 → 0.124 (0.008) | 28.5 → 16.5 (0.016) | — |
| Set 3: split-sample top 25 | B | 25 (25) | 35.0 / 31.5 → 39.5 | +8.0 (5/8), 0.062 | +5.0 (0.320) / +4.0 (0.438) | +3.0 / +4.0 | 0.062 (5/7) / 0.125 | 6 / 5 → 9 of 25 (0.141) | 7 / 6 | 0.171 → 0.144 (0.008) | 28.0 → 23.5 (0.219) | — |
| Full panel (58 + expanded non-proximal) | full | 405 (363) | 59.5 / 66.4 → 71.4 | +5.0 (7/8), 0.047 | +5.0 (0.008) / +4.9 (0.031) | +0.0 / +0.1 | 0.078 (6/7) / 0.094 | 250 / 296 → 314 of 371 (0.055) | 294 / 291 | 0.094 → 0.082 (0.016) | 10.8 → 7.3 (0.031) | — |
| Full panel (58 + expanded non-proximal) | A | 405 (363) | 57.3 / 63.6 → 68.5 | +5.0 (8/8), 0.008 | +4.8 (0.023) / +5.4 (0.047) | +0.1 / -0.4 | 0.016 (7/7) / 0.016 | 247 / 271 → 306 of 371 (0.031) | 261 / 277 | 0.098 → 0.089 (0.016) | 11.3 → 9.3 (0.078) | — |
| Full panel (58 + expanded non-proximal) | B | 405 (363) | 55.6 / 61.1 → 65.4 | +4.2 (6/8), 0.133 | +6.6 (0.047) / +4.9 (0.031) | -2.4 / -0.7 | 0.188 (5/7) / 0.266 | 213 / 267 → 302 of 371 (0.094) | 250 / 260 | 0.103 → 0.092 (0.062) | 11.6 → 10.2 (0.219) | — |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (192) | 58.4 / 66.2 → 71.2 | +5.0 (6/8), 0.086 | +4.7 (0.016) / +4.5 (0.047) | +0.3 / +0.5 | 0.109 (6/7) / 0.172 | 125 / 157 → 170 of 194 (0.062) | 157 / 157 | 0.091 → 0.080 (0.023) | 10.1 → 6.9 (0.047) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (192) | 56.7 / 66.1 → 69.4 | +3.3 (7/8), 0.016 | +4.4 (0.039) / +4.0 (0.078) | -1.0 / -0.7 | 0.016 (7/7) / 0.031 | 128 / 156 → 169 of 194 (0.062) | 141 / 157 | 0.091 → 0.084 (0.031) | 10.3 → 8.2 (0.062) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (192) | 55.8 / 61.7 → 64.8 | +3.2 (5/8), 0.375 | +5.6 (0.117) / +3.7 (0.258) | -2.4 / -0.5 | 0.375 (5/7) / 0.750 | 105 / 141 → 164 of 194 (0.203) | 136 / 144 | 0.098 → 0.091 (0.117) | 11.0 → 10.0 (0.328) | — |

### demo (8 physiology trials) (descriptive; not in the FDR family)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (28) | 44.1 / 46.8 → 57.6 | +10.8 (6/8), 0.094 | +15.8 (0.078) / +11.8 (0.047) | -5.0 / -0.9 | 0.188 (5/7) / 0.188 | 14 / 9 → 14 of 28 (0.352) | 9 / 10 | 0.158 → 0.117 (0.008) | 28.0 → 17.2 (0.016) | — |
| Set 1: clinical ECG-relevant | A | 28 (28) | 42.7 / 42.2 → 54.0 | +11.8 (6/8), 0.156 | +15.8 (0.016) / +14.0 (0.062) | -4.0 / -2.2 | 0.281 (5/7) / 0.281 | 9 / 8 → 16 of 28 (0.180) | 5 / 10 | 0.172 → 0.140 (0.078) | 31.1 → 27.1 (0.266) | — |
| Set 1: clinical ECG-relevant | B | 28 (28) | 40.5 / 36.5 → 49.5 | +13.0 (6/8), 0.086 | +15.8 (0.016) / +9.9 (0.148) | -2.7 / +3.2 | 0.109 (5/7) / 0.172 | 11 / 10 → 13 of 28 (0.531) | 6 / 7 | 0.191 → 0.144 (0.031) | 33.3 → 23.0 (0.086) | — |
| Set 2: literature core+common | full | 273 (263) | 56.3 / 56.5 → 63.3 | +6.8 (7/8), 0.039 | +7.6 (0.016) / +6.4 (0.031) | -0.8 / +0.4 | 0.078 (6/7) / 0.078 | 165 / 165 → 202 of 268 (0.039) | 163 / 171 | 0.119 → 0.099 (0.008) | 18.1 → 13.3 (0.008) | — |
| Set 2: literature core+common | A | 273 (263) | 54.1 / 52.3 → 61.1 | +8.8 (8/8), 0.008 | +9.7 (0.008) / +7.9 (0.008) | -0.9 / +0.9 | 0.016 (7/7) / 0.016 | 163 / 145 → 201 of 268 (0.008) | 132 / 159 | 0.127 → 0.105 (0.008) | 19.1 → 13.7 (0.016) | — |
| Set 2: literature core+common | B | 273 (263) | 53.7 / 51.7 → 57.5 | +5.8 (7/8), 0.016 | +5.1 (0.016) / +4.8 (0.062) | +0.6 / +1.0 | 0.031 (6/7) / 0.031 | 140 / 142 → 181 of 268 (0.023) | 140 / 149 | 0.131 → 0.109 (0.008) | 20.8 → 15.2 (0.023) | — |
| Set 3: split-sample top 25 | full | 25 (25) | 34.0 / 36.5 → 45.0 | +8.5 (7/8), 0.031 | +10.0 (0.031) / +8.0 (0.062) | -1.5 / +0.5 | 0.062 (6/7) / 0.062 | 5 / 4 → 11 of 25 (0.133) | 6 / 5 | 0.188 → 0.143 (0.008) | 34.0 → 23.5 (0.008) | — |
| Set 3: split-sample top 25 | A | 25 (25) | 34.0 / 30.5 → 52.5 | +22.0 (8/8), 0.008 | +23.0 (0.008) / +18.0 (0.008) | -1.0 / +4.0 | 0.016 (7/7) / 0.016 | 4 / 3 → 16 of 25 (0.031) | 3 / 5 | 0.203 → 0.129 (0.008) | 40.5 → 21.5 (0.016) | — |
| Set 3: split-sample top 25 | B | 25 (25) | 31.5 / 32.0 → 40.0 | +8.0 (5/8), 0.125 | +8.5 (0.055) / +4.0 (0.500) | -0.5 / +4.0 | 0.094 (5/7) / 0.250 | 4 / 4 → 9 of 25 (0.023) | 4 / 6 | 0.206 → 0.163 (0.023) | 39.0 → 28.5 (0.062) | — |
| Full panel (58 + expanded non-proximal) | full | 405 (394) | 59.7 / 59.9 → 66.4 | +6.6 (8/8), 0.008 | +7.1 (0.008) / +5.8 (0.016) | -0.6 / +0.7 | 0.016 (7/7) / 0.016 | 276 / 266 → 321 of 403 (0.008) | 270 / 282 | 0.112 → 0.094 (0.008) | 15.7 → 11.7 (0.008) | — |
| Full panel (58 + expanded non-proximal) | A | 405 (394) | 57.5 / 56.1 → 62.8 | +6.7 (6/8), 0.031 | +9.0 (0.008) / +7.1 (0.016) | -2.3 / -0.4 | 0.062 (5/7) / 0.062 | 270 / 245 → 309 of 403 (0.008) | 224 / 253 | 0.119 → 0.103 (0.016) | 17.2 → 13.3 (0.047) | — |
| Full panel (58 + expanded non-proximal) | B | 405 (394) | 55.7 / 55.0 → 58.7 | +3.7 (7/8), 0.031 | +3.7 (0.039) / +3.9 (0.125) | -0.0 / -0.2 | 0.062 (6/7) / 0.062 | 235 / 237 → 282 of 403 (0.008) | 235 / 243 | 0.124 → 0.108 (0.016) | 18.3 → 13.8 (0.031) | — |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (222) | 58.8 / 59.2 → 65.1 | +5.9 (7/8), 0.047 | +6.0 (0.047) / +5.6 (0.039) | -0.1 / +0.3 | 0.094 (6/7) / 0.094 | 150 / 146 → 176 of 224 (0.047) | 151 / 153 | 0.112 → 0.095 (0.016) | 16.1 → 12.3 (0.016) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (222) | 56.9 / 54.5 → 62.5 | +8.0 (8/8), 0.008 | +9.1 (0.008) / +6.6 (0.016) | -1.1 / +1.4 | 0.016 (7/7) / 0.016 | 150 / 130 → 176 of 224 (0.023) | 119 / 146 | 0.119 → 0.101 (0.031) | 16.6 → 13.0 (0.094) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (222) | 55.9 / 54.3 → 59.0 | +4.7 (8/8), 0.008 | +4.0 (0.039) / +3.8 (0.156) | +0.7 / +0.9 | 0.016 (7/7) / 0.016 | 126 / 128 → 158 of 224 (0.031) | 127 / 135 | 0.122 → 0.106 (0.008) | 18.7 → 14.4 (0.062) | — |

### hdPS200 (8 physiology trials) (descriptive; not in the FDR family)

| set | half | vars (median avail.) | % <0.1 unm / base → ECG | d (k), p | vs shuf / noise d (p) | shuf−base / noise−base | cluster p (k) / LOO | love <0.1 unm / base → ECG (p) | love shuf / noise | mean |SMD| base → ECG (p) | % >0.2 base → ECG (p) | q (%<0.1 / love / mean / >0.2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Set 1: clinical ECG-relevant | full | 28 (27) | 44.6 / 64.5 → 74.2 | +9.7 (6/8), 0.062 | +3.7 (0.250) / +6.4 (0.031) | +6.0 / +3.2 | 0.047 (6/7) / 0.125 | 15 / 18 → 25 of 28 (0.062) | 23 / 22 | 0.102 → 0.082 (0.031) | 11.6 → 8.3 (0.250) | — |
| Set 1: clinical ECG-relevant | A | 28 (27) | 43.3 / 53.4 → 55.7 | +2.4 (3/8), 0.578 | -1.9 (0.609) / -0.9 (0.844) | +4.2 / +3.3 | 0.438 (3/7) / 0.906 | 10 / 15 → 17 of 28 (0.680) | 19 / 17 | 0.132 → 0.120 (0.227) | 21.7 → 21.6 (0.969) | — |
| Set 1: clinical ECG-relevant | B | 28 (28) | 41.1 / 60.2 → 61.5 | +1.3 (4/8), 0.758 | +1.9 (0.578) / +5.0 (0.367) | -0.5 / -3.7 | 0.938 (3/7) / 0.969 | 11 / 21 → 21 of 28 (1.000) | 21 / 20 | 0.114 → 0.106 (0.703) | 15.9 → 11.0 (0.156) | — |
| Set 2: literature core+common | full | 273 (188) | 59.5 / 82.7 → 84.2 | +1.5 (7/8), 0.242 | +0.9 (0.453) / +0.8 (0.766) | +0.6 / +0.6 | 0.281 (6/7) / 0.484 | 145 / 212 → 217 of 225 (0.250) | 211 / 212 | 0.058 → 0.056 (0.008) | 2.7 → 2.3 (0.344) | — |
| Set 2: literature core+common | A | 273 (191) | 57.9 / 79.2 → 79.4 | +0.2 (4/8), 0.859 | +1.6 (0.258) / -0.4 (0.742) | -1.4 / +0.6 | 1.000 (3/7) / 1.000 | 142 / 211 → 216 of 225 (0.352) | 207 / 216 | 0.069 → 0.066 (0.039) | 5.0 → 4.4 (0.062) | — |
| Set 2: literature core+common | B | 273 (190) | 57.0 / 78.8 → 80.2 | +1.4 (3/8), 0.609 | +3.8 (0.242) / +2.3 (0.266) | -2.3 / -0.9 | 0.594 (3/7) / 0.844 | 127 / 206 → 209 of 224 (0.531) | 200 / 204 | 0.069 → 0.069 (0.945) | 4.5 → 4.3 (0.688) | — |
| Set 3: split-sample top 25 | full | 25 (24) | 54.4 / 63.2 → 68.4 | +5.2 (4/8), 0.297 | -0.3 (0.984) / +1.6 (0.688) | +5.5 / +3.6 | 0.250 (3/7) / 0.594 | 14 / 17 → 21 of 25 (0.016) | 22 / 20 | 0.097 → 0.083 (0.016) | 13.0 → 5.2 (0.047) | — |
| Set 3: split-sample top 25 | A | 25 (24) | 48.2 / 49.2 → 66.2 | +17.0 (7/8), 0.016 | +6.1 (0.234) / +5.5 (0.094) | +11.0 / +11.5 | 0.031 (6/7) / 0.031 | 11 / 14 → 18 of 25 (0.242) | 18 / 17 | 0.147 → 0.102 (0.008) | 21.7 → 14.0 (0.031) | — |
| Set 3: split-sample top 25 | B | 25 (24) | 46.5 / 57.7 → 59.2 | +1.5 (5/8), 0.672 | +0.9 (0.906) / -2.2 (0.484) | +0.6 / +3.6 | 0.344 (5/7) / 0.906 | 9 / 16 → 18 of 25 (0.742) | 15 / 18 | 0.127 → 0.120 (0.398) | 22.5 → 18.3 (0.125) | — |
| Full panel (58 + expanded non-proximal) | full | 405 (330) | 61.4 / 82.4 → 84.3 | +1.9 (8/8), 0.008 | +0.5 (0.594) / +0.8 (0.359) | +1.4 / +1.1 | 0.016 (7/7) / 0.016 | 257 / 345 → 353 of 368 (0.133) | 350 / 347 | 0.060 → 0.057 (0.008) | 3.1 → 2.4 (0.031) | — |
| Full panel (58 + expanded non-proximal) | A | 405 (328) | 59.4 / 76.8 → 77.4 | +0.6 (4/8), 0.547 | +0.0 (0.969) / -1.0 (0.203) | +0.5 / +1.6 | 0.625 (3/7) / 0.984 | 248 / 329 → 334 of 368 (0.586) | 335 / 334 | 0.075 → 0.071 (0.055) | 6.4 → 5.8 (0.305) | — |
| Full panel (58 + expanded non-proximal) | B | 405 (324) | 57.3 / 77.3 → 77.7 | +0.3 (4/8), 0.789 | +1.4 (0.422) / +0.9 (0.469) | -1.1 / -0.6 | 0.688 (3/7) / 0.938 | 224 / 333 → 335 of 366 (0.859) | 331 / 333 | 0.072 → 0.074 (0.562) | 5.9 → 5.7 (0.750) | — |
| Set 2, non-ECG-proximal part (descriptive) | full | 226 (168) | 60.6 / 84.1 → 85.2 | +1.1 (6/8), 0.406 | +0.7 (0.523) / +0.4 (0.953) | +0.4 / +0.7 | 0.438 (5/7) / 0.781 | 129 / 185 → 189 of 192 (0.164) | 184 / 185 | 0.055 → 0.053 (0.039) | 1.7 → 1.5 (0.500) | — |
| Set 2, non-ECG-proximal part (descriptive) | A | 226 (168) | 59.5 / 80.5 → 80.1 | -0.4 (3/8), 0.797 | +1.1 (0.438) / -1.2 (0.281) | -1.4 / +0.9 | 0.703 (3/7) / 1.000 | 130 / 184 → 186 of 192 (0.852) | 179 / 186 | 0.065 → 0.064 (0.211) | 4.0 → 3.7 (0.250) | — |
| Set 2, non-ECG-proximal part (descriptive) | B | 226 (164) | 58.1 / 80.3 → 81.0 | +0.7 (3/8), 0.766 | +3.8 (0.227) / +1.9 (0.398) | -3.1 / -1.2 | 0.750 (3/7) / 0.984 | 113 / 182 → 181 of 191 (0.844) | 175 / 179 | 0.065 → 0.067 (0.547) | 3.5 → 3.9 (0.469) | — |

## Domain-level balance: Headline scenario (demo, caliper 0.1, 18 trials)

Domain mean |SMD| per trial (mean over the domain's available variables), then over trials; paired sign-flip ECG − base; BH over domains.

| domain | vars | mean |SMD| unm / base → ECG | d (k) | p | q (domains) | vs shuf / noise p | love <0.1 unm / base → ECG |
|---|---|---|---|---|---|---|---|
| 58: Coded record | 4 | 0.142 / 0.130 → 0.115 | -0.0156 (15/18) | 0.019 | 0.024 | 0.014 / 0.011 | 0 / 2 → 2 |
| 58: Echo: LV function | 4 | 0.205 / 0.205 → 0.152 | -0.0537 (15/18) | 0.002 | 0.003 | <0.001 / <0.001 | 1 / 1 → 2 |
| 58: Echo: LV structure | 7 | 0.144 / 0.138 → 0.095 | -0.0428 (16/18) | <0.001 | <0.001 | <0.001 / <0.001 | 4 / 4 → 5 |
| 58: Echo: RV / pulmonary | 7 | 0.123 / 0.134 → 0.104 | -0.0296 (15/18) | 0.003 | 0.005 | 0.016 / 0.063 | 4 / 2 → 5 |
| 58: Echo: diastolic / LA | 8 | 0.131 / 0.136 → 0.094 | -0.0422 (15/18) | <0.001 | 0.001 | 0.001 / <0.001 | 6 / 1 → 8 |
| 58: Echo: valves / aorta | 9 | 0.170 / 0.164 → 0.154 | -0.0104 (12/18) | 0.287 | 0.337 | 0.047 / 0.124 | 4 / 4 → 5 |
| 58: Other labs | 10 | 0.095 / 0.077 → 0.076 | -0.0006 (10/18) | 0.900 | 0.900 | 0.248 / 0.742 | 9 / 9 → 9 |
| 58: Vitals & core labs | 9 | 0.145 / 0.143 → 0.118 | -0.0251 (18/18) | <0.001 | <0.001 | <0.001 / <0.001 | 5 / 6 → 7 |
| covars v1 (race, tobacco, obesity, lipids, T2D, frailty, inpatient days) | 12 | 0.102 / 0.110 → 0.093 | -0.0170 (16/18) | <0.001 | <0.001 | <0.001 / <0.001 | 10 / 8 → 9 |
| expanded: calendar | 2 | 0.030 / 0.045 → 0.048 | +0.0033 (7/18) | 0.494 | 0.556 | 0.912 / 0.031 | 2 / 2 → 2 |
| expanded: charlson | 15 | 0.092 / 0.097 → 0.085 | -0.0121 (14/18) | 0.004 | 0.007 | 0.014 / <0.001 | 12 / 12 → 13 |
| expanded: charlson [ECG-proximal] | 2 | 0.191 / 0.195 → 0.132 | -0.0633 (16/18) | <0.001 | <0.001 | <0.001 / <0.001 | 0 / 0 → 1 |
| expanded: comorbidity | 103 | 0.090 / 0.097 → 0.085 | -0.0121 (16/18) | <0.001 | 0.002 | <0.001 / <0.001 | 82 / 78 → 85 |
| expanded: comorbidity [ECG-proximal] | 30 | 0.125 / 0.125 → 0.089 | -0.0360 (18/18) | <0.001 | <0.001 | <0.001 / <0.001 | 17 / 16 → 21 |
| expanded: device_procedure | 12 | 0.158 / 0.170 → 0.152 | -0.0183 (15/18) | <0.001 | 0.001 | <0.001 / <0.001 | 3 / 3 → 6 |
| expanded: device_procedure [ECG-proximal] | 10 | 0.103 / 0.094 → 0.072 | -0.0221 (15/18) | 0.006 | 0.009 | 0.004 / 0.002 | 6 / 10 → 10 |
| expanded: elixhauser | 29 | 0.104 / 0.114 → 0.097 | -0.0162 (15/18) | <0.001 | 0.002 | <0.001 / <0.001 | 22 / 21 → 21 |
| expanded: elixhauser [ECG-proximal] | 2 | 0.225 / 0.227 → 0.165 | -0.0618 (17/18) | <0.001 | <0.001 | <0.001 / <0.001 | 0 / 0 → 0 |
| expanded: lab_vital | 82 | 0.121 / 0.123 → 0.105 | -0.0180 (17/18) | <0.001 | <0.001 | <0.001 / <0.001 | 41 / 45 → 57 |
| expanded: lab_vital [ECG-proximal] | 2 | 0.184 / 0.182 → 0.158 | -0.0231 (6/12) | 0.549 | 0.570 | 0.323 / 0.518 | 1 / 1 → 1 |
| expanded: medication | 49 | 0.091 / 0.092 → 0.080 | -0.0120 (13/18) | <0.001 | 0.002 | <0.001 / 0.006 | 34 / 36 → 41 |
| expanded: medication [ECG-proximal] | 7 | 0.122 / 0.121 → 0.096 | -0.0250 (15/18) | <0.001 | <0.001 | <0.001 / <0.001 | 4 / 3 → 6 |
| expanded: preventive | 9 | 0.066 / 0.049 → 0.047 | -0.0015 (12/18) | 0.542 | 0.570 | 0.290 / 0.231 | 9 / 9 → 9 |
| expanded: score | 3 | 0.224 / 0.218 → 0.183 | -0.0348 (12/18) | 0.004 | 0.007 | <0.001 / 0.021 | 0 / 0 → 0 |
| expanded: score [ECG-proximal] | 6 | 0.239 / 0.259 → 0.218 | -0.0409 (15/18) | 0.008 | 0.011 | 0.021 / 0.002 | 0 / 0 → 0 |
| expanded: utilisation | 41 | 0.108 / 0.102 → 0.094 | -0.0074 (15/18) | 0.040 | 0.049 | 0.006 / <0.001 | 29 / 31 → 32 |
| expanded: utilisation [ECG-proximal] | 2 | 0.169 / 0.178 → 0.155 | -0.0232 (13/18) | 0.011 | 0.015 | 0.002 / 0.022 | 0 / 0 → 0 |

## Domain-level balance: Sparse reference (18 trials)

Domain mean |SMD| per trial (mean over the domain's available variables), then over trials; paired sign-flip ECG − base; BH over domains.

| domain | vars | mean |SMD| unm / base → ECG | d (k) | p | q (domains) | vs shuf / noise p | love <0.1 unm / base → ECG |
|---|---|---|---|---|---|---|---|
| 58: Coded record | 4 | 0.142 / 0.087 → 0.081 | -0.0062 (13/18) | 0.052 | 0.104 | 0.130 / 0.039 | 0 / 4 → 4 |
| 58: Echo: LV function | 4 | 0.205 / 0.166 → 0.160 | -0.0056 (9/18) | 0.783 | 0.885 | 0.831 / 0.407 | 1 / 1 → 2 |
| 58: Echo: LV structure | 7 | 0.144 / 0.111 → 0.100 | -0.0108 (13/18) | 0.289 | 0.396 | 0.069 / 0.071 | 4 / 6 → 5 |
| 58: Echo: RV / pulmonary | 7 | 0.123 / 0.106 → 0.095 | -0.0108 (12/18) | 0.071 | 0.132 | 0.124 / 0.002 | 4 / 6 → 5 |
| 58: Echo: diastolic / LA | 8 | 0.131 / 0.097 → 0.091 | -0.0061 (13/18) | 0.442 | 0.547 | 0.594 / 0.218 | 6 / 8 → 8 |
| 58: Echo: valves / aorta | 9 | 0.170 / 0.143 → 0.142 | -0.0008 (8/18) | 0.896 | 0.932 | 0.650 / 0.421 | 4 / 6 → 6 |
| 58: Other labs | 10 | 0.095 / 0.060 → 0.059 | -0.0014 (8/18) | 0.709 | 0.838 | 0.970 / 0.927 | 9 / 10 → 9 |
| 58: Vitals & core labs | 9 | 0.145 / 0.115 → 0.102 | -0.0128 (15/18) | 0.002 | 0.012 | <0.001 / <0.001 | 5 / 7 → 8 |
| covars v1 (race, tobacco, obesity, lipids, T2D, frailty, inpatient days) | 11 | 0.101 / 0.076 → 0.069 | -0.0069 (14/18) | 0.002 | 0.012 | 0.055 / 0.006 | 9 / 8 → 9 |
| expanded: calendar | 2 | 0.030 / 0.056 → 0.052 | -0.0038 (11/18) | 0.367 | 0.477 | 0.856 / 0.238 | 2 / 2 → 2 |
| expanded: charlson | 9 | 0.068 / 0.061 → 0.051 | -0.0105 (12/18) | 0.011 | 0.042 | 0.102 / 0.026 | 8 / 9 → 9 |
| expanded: charlson [ECG-proximal] | 1 | 0.201 / 0.145 → 0.114 | -0.0307 (7/9) | 0.082 | 0.133 | 0.574 / 0.309 | 0 / 1 → 1 |
| expanded: comorbidity | 87 | 0.089 / 0.068 → 0.061 | -0.0074 (15/18) | 0.002 | 0.012 | 0.025 / 0.003 | 71 / 81 → 82 |
| expanded: comorbidity [ECG-proximal] | 24 | 0.114 / 0.071 → 0.062 | -0.0087 (13/18) | 0.036 | 0.084 | 0.058 / 0.010 | 15 / 20 → 20 |
| expanded: device_procedure | 10 | 0.156 / 0.111 → 0.103 | -0.0079 (13/18) | 0.002 | 0.012 | 0.018 / 0.015 | 3 / 7 → 6 |
| expanded: device_procedure [ECG-proximal] | 10 | 0.103 / 0.077 → 0.063 | -0.0139 (12/18) | 0.039 | 0.084 | 0.011 / 0.031 | 6 / 10 → 9 |
| expanded: elixhauser | 21 | 0.089 / 0.072 → 0.065 | -0.0077 (13/18) | 0.011 | 0.042 | 0.082 / 0.016 | 18 / 20 → 20 |
| expanded: elixhauser [ECG-proximal] | 1 | 0.201 / 0.145 → 0.114 | -0.0307 (7/9) | 0.082 | 0.133 | 0.574 / 0.309 | 0 / 1 → 1 |
| expanded: lab_vital | 82 | 0.121 / 0.090 → 0.081 | -0.0090 (15/18) | <0.001 | 0.012 | <0.001 / <0.001 | 41 / 67 → 70 |
| expanded: lab_vital [ECG-proximal] | 2 | 0.184 / 0.146 → 0.159 | +0.0136 (2/12) | 0.868 | 0.932 | 0.003 / 0.023 | 1 / 1 → 1 |
| expanded: medication | 49 | 0.091 / 0.066 → 0.063 | -0.0028 (12/18) | 0.262 | 0.378 | 0.004 / 0.027 | 34 / 45 → 45 |
| expanded: medication [ECG-proximal] | 7 | 0.122 / 0.077 → 0.072 | -0.0055 (12/18) | 0.171 | 0.261 | 0.087 / 0.169 | 4 / 7 → 7 |
| expanded: preventive | 9 | 0.066 / 0.047 → 0.043 | -0.0044 (14/18) | 0.028 | 0.072 | 0.219 / 0.221 | 9 / 9 → 9 |
| expanded: score | 3 | 0.224 / 0.118 → 0.118 | -0.0003 (9/18) | 0.973 | 0.973 | 0.043 / 0.116 | 0 / 2 → 2 |
| expanded: utilisation | 41 | 0.108 / 0.073 → 0.068 | -0.0056 (14/18) | 0.019 | 0.057 | 0.261 / 0.099 | 29 / 35 → 36 |
| expanded: utilisation [ECG-proximal] | 2 | 0.169 / 0.091 → 0.082 | -0.0091 (13/18) | 0.020 | 0.057 | 0.921 / 0.594 | 0 / 2 → 2 |

## Engine metrics (standard sweep summary; ECG vs base, 18 trials)

E.summarize_pairs; negative d = ECG better; q = BH over the 6 cells (full). Heat map `docs/v16/S9_COVSETS_heatmap.png` (left: these metrics; right: set % < 0.1 across scenarios × sets × halves).

| cell | absd d (k, p) | z2 d (k, p) | mean_smd d (k, p) | cstat d (k, p) | absd A p | z2 A p | mean_smd A p | cstat A p | absd B p | z2 B p | mean_smd B p | cstat B p | q |Δ| / z² / SMD / C | vs shufECG p (|Δ|, SMD) | vs noise p (|Δ|, SMD) | consistency % base→ECG | φ base→ECG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo / caliper 0.1 | -0.046 (12/18, 0.087) | -3.51 (12/18, 0.007) | -0.0249 (17/18, <0.001) | -0.022 (15/18, <0.001) | 0.045 | 0.026 | 0.002 | 0.009 | 0.152 | 0.069 | <0.001 | 0.001 | 0.173 / 0.022 / <0.001 / 0.003 | 0.082, <0.001 | 0.094, <0.001 | 56→61 | 9.86→6.16 |
| minimal-7 | -0.038 (11/18, 0.058) | -2.73 (11/18, 0.033) | -0.0162 (16/18, <0.001) | -0.016 (17/18, <0.001) | 0.269 | 0.073 | 0.002 | 0.017 | 0.805 | 0.188 | 0.003 | <0.001 | 0.173 / 0.042 / 0.001 / <0.001 | 0.101, <0.001 | 0.007, 0.003 | 56→61 | 8.17→5.13 |
| common-10 | -0.016 (10/18, 0.520) | -2.25 (10/18, 0.035) | -0.0131 (15/18, 0.014) | -0.014 (15/18, 0.049) | 0.177 | 0.029 | 0.002 | 0.125 | 0.081 | 0.021 | 0.031 | 0.047 | 0.624 / 0.042 / 0.017 / 0.049 | 0.928, 0.002 | 0.422, 0.004 | 61→72 | 6.52→4.04 |
| sparse | -0.020 (14/18, 0.264) | -1.40 (14/18, 0.024) | -0.0067 (14/18, 0.026) | -0.013 (15/18, 0.023) | 0.042 | 0.013 | 0.504 | <0.001 | 0.231 | 0.030 | 0.033 | 0.055 | 0.397 / 0.042 / 0.026 / 0.035 | 0.088, 0.059 | 0.053, 0.004 | 61→78 | 4.70→3.41 |
| demo | -0.057 (14/18, 0.033) | -3.66 (14/18, 0.006) | -0.0233 (17/18, <0.001) | -0.018 (15/18, 0.003) | 0.106 | 0.032 | 0.003 | 0.091 | 0.125 | 0.083 | <0.001 | <0.001 | 0.173 / 0.022 / <0.001 / 0.006 | 0.083, <0.001 | 0.120, <0.001 | 56→61 | 9.76→6.08 |
| hdPS200 | -0.002 (10/18, 0.918) | -0.56 (10/18, 0.242) | -0.0097 (15/18, 0.003) | -0.007 (12/18, 0.048) | 0.159 | 0.120 | 0.032 | 0.954 | 0.079 | 0.067 | 0.285 | 0.028 | 0.918 / 0.242 / 0.004 / 0.049 | 0.678, 0.087 | 0.493, <0.001 | 56→72 | 3.28→2.71 |

## Figures

- `docs/v16/S9_COVSETS_heatmap.png`
- `docs/v16/S9_DOMAINS_demo_cal01.png`
- `docs/v16/S9_DOMAINS_sparse.png`
- `docs/v16/S9_LOVE_SET1_demo_cal01.png`
- `docs/v16/S9_LOVE_SET2_demo_cal01.png`
- `docs/v16/S9_LOVE_SET3_demo_cal01.png`
- `docs/v16/S9_LOVE_SET1_sparse.png`
- `docs/v16/S9_LOVE_SET2_sparse.png`
- `docs/v16/S9_LOVE_SET3_sparse.png`

## Audit

**(1) Reproduction of engine validation** (full cohort, 18 trials; max |S9 − ENGINE_VALIDATION| over trials; the only non-zero row, sparse, is ALLHAT, the known floating-point near-tie in greedy matching documented in ENGINE_VALIDATION.md):

| arm | d_loghr | d_mean_smd | d_pairs | d_cstat |
|---|---|---|---|---|
| hdPS200 | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |
| hdPS200+ECG | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |
| sparse | 0.00003983 | 0.00020563 | 0.00000000 | 0.00013741 |
| sparse+ECG | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |
| unmatched | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |

**(2) Pair counts** (matching cells, full cohort; arm pairs / base pairs): ECG median 0.999 (5th–95th pct 0.888–1.020); shufECG median 1.000 (5th–95th pct 0.968–1.014); noise median 1.000 (5th–95th pct 0.972–1.020).


**(3) Pre-run 2-trial check (half A; LIFE, CAROLINA; 50 arm rows).** The base, ECG, shufECG, noise and unmatched arms reproduce S8's half-A rows exactly: max |Δ| is 0 for log HR, mean |SMD|, pair count and C. The per-cell universe sizes are sensible. The table gives the mean number of extra + v1 variables kept per trial, with the number dropped for PS overlap in parentheses:

| cell | kept (PS-overlap drops) |
|---|---|
| demo | 384 (6) |
| minimal-7 | 357 (34) |
| common-10 | 346 (45) |
| sparse | 335 (56) |
| hdPS200 | 296 (94, of which 39 are hdPS-code overlaps) |
| unmatched | 390 |

The placebo arms' mean per-variable |SMD| was within ±0.007 of base.

**(4) Input fingerprint.** The MD5 over the covars2b parquet files, dictionary, status file and `s6_balance.py` is 04c617bd… for both production runs (half A; full + B) and at report time. The 2-trial test ran 2 minutes earlier with a different fingerprint (e7f634ed…), because `s6_balance.py` was still being edited by the covars2b fix agent. The test is used only for the reproduction check above.

**Placebo − base over the 36 family rows** (full, % < 0.1): shufECG − base mean -0.47 pp (p<0.05: better 0, worse 0); noise − base +0.49 pp (better 0, worse 0); ECG − base +6.87 pp.

## Deviations from the plan and clarifications

1. **Expanded panel = claude-v16-covars2b** (corrected build, READY 2026-09-27T03:59Z; fingerprint of the 18 parquet files + dictionary + status + `s6_balance.py` logged in the run logs). The v2b status/timing corrections (index-day and current-address variables excluded; utilisation counts exclude the index admission; HFRS cut-point excluded; composites tagged for PS overlap; extended ECG-proximal block) replace S8's ad-hoc covars2 exclusions. S8's `EXTRA_PROX` list is still unioned into the ECG-proximal block, so the "non-proximal" panel is at least as strict as S8's.
2. **Scenarios.** The plan names "the S8-selected headline scenarios plus sparse and demo". As instructed by the caller, the headline scenarios are demo / caliper 0.1, minimal-7 and common-10, each in all 18 trials and in the 8 physiology trials. The references are sparse, demo (caliper 0.2) and hdPS200 (added) in 18 trials. The references' physiology-subset rows are descriptive only and not in the FDR family.
3. **Set 1 mapping.** LV mass is not in any available panel, so Set 1 has 28 of the 29 listed items. Prior HF hospitalisation is `n_hf_hosp_365` (covars2b; inpatient stays ending ≤ index − 1 with an I50 code). Loop diuretic (`rx_loop_diuretic_365`) is dropped where it is the exposure (TRANSFORM-HF) and wherever a PS contains or overlaps it. Several Set-1 items are ECG-proximal by construction (HF burden, cardiomyopathy, loop diuretic). That is the plan's intent: Set 1 is "what an ECG plausibly reflects".
4. **Set 2 mapping.** The plan says only "core + common items, available, not in the cell's PS, no exposure leaks". Two decisions were needed:
   - Variables come from the COVARIATES2 literature cross-check. Items already in an existing panel map to the 58-panel or claude-v16-covars (v1).
   - Age, sex and index year are in every PS, so they never enter.
   
   ECG-proximal variables are not excluded (the plan does not exclude them). A descriptive "Set 2 non-proximal" row is added. Item 146 (lab-measured flags) contributes 40 `lab_*_missing` indicators, as in the cross-check.
5. **Set 3 details not fixed by the plan.**
   - A candidate must be available in both arms in at least half of the scenario's trials.
   - The gain is averaged over the trials where the variable is available.
   - A selection was made for every scenario, including the descriptive ones.
   
   Selection used half A only. `docs/v16/selection_S9.json` was committed and pushed at 2026-09-27 00:11:45 EDT (commit 60ed1c6) before the full / half-B run started. The full-cohort Set-3 rows contain half A (the selection sample), so **half B is the only out-of-sample confirmation**.
6. **Love-count inference.** The love count is a single number per scenario (the median across trials), so the per-trial sign-flip cannot be applied to it. Its tests use swap permutations instead:
   - **Main p:** swap the two arms' per-trial |SMD| vectors within trial. Exact when there are ≤ 12 trials, else 20,000 draws.
   - **Placebos:** the same permutation with 5,000 draws.
   - **Cluster p:** swap whole comparator clusters (exact).
   - **LOO:** max p over leave-one-trial-out, 2,000 draws; family rows in the full cohort only.
7. **Metrics.**
   - % > 0.2 is added, as requested.
   - **BH-FDR family:** 9 scenarios × 4 sets (Set 1, Set 2, Set 3, FULL) × 4 metrics (% < 0.1, love count, mean |SMD|, % > 0.2), within each half.
   - The engine metrics (|Δlog HR|, z², 58-variable mean |SMD|, C) are reported in their own table and heat map, with BH over the 6 cells.
8. **hdPS200 exclusion.** At hdPS200, the corrected S6 rule is applied: drop extra variables whose codes overlap the top-200 hdPS codes. The claude-v16-covars dx variables (tobacco, obesity, hyperlipidemia, t2d, frailty_count) use hand-coded ICD prefixes (`V1_KEYS`).
9. **Audit test run.** The 2-trial pre-run check used half A only (LIFE, CAROLINA), not the full cohort, so that no half-B rows were computed before the Set-3 commit. The engine-validation reproduction (full cohort) is therefore reported after the full run (Audit section).
