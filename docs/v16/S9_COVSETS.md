# v1.6 S9: covariate sets (definitions; results pending)

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
