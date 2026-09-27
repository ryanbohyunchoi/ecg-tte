# v1.7 blinded trial-selection rule (no results viewed)

Rater: independent blinded agent, 2026-09-27. The rule text below was fixed before any trial was scored. The second pass (15 new v1.7 trials) applied it unchanged.

## 1. Rule (defined before scoring)

```
BLINDED v1.7 TRIAL-SELECTION RULE (written before scoring any trial; design-level information only).
Layer 1, emulation fidelity. Core design flags, each 0/1:
F1 in-hospital start not mirrored: the RCT randomizes during, or at discharge from, an index hospitalisation at a fixed protocol moment, and the emulation's time zero for at least one arm is plausibly moved from that moment, by more than 7 days or by setting (e.g. an inpatient IV order vs an oral discharge strategy). EHR inpatient orders are visible, so this is not flagged when standard care starts both arms' drugs within the index admission (P2Y12 inhibitors in ACS/PCI).
F2 responder/tolerability run-in: an active run-in on a study drug removed intolerant or non-responding patients before randomization. Placebo-only, adherence or washout run-ins are not flagged.
F3 randomization combined with discontinuation or switching of baseline therapy, not mirrored: the RCT protocol had a substantial share of patients stop or replace an ongoing drug of the same therapeutic purpose at randomization, and the emulation's new-user/washout design neither reproduces nor requires that switch. Sequential switch designs that mirror it are not flagged.
F4 delayed effect over long follow-up: the trial-matched horizon (HORIZON_MONTHS) is >= 48 months. The initiator (ITT-like) estimand is then diluted by real-world discontinuation, and effects that accrue over years cannot be reproduced.
F5 other time-zero misalignment: the comparator's time zero needs future information or is otherwise undefined (e.g. prevalent 'continuer' comparators with no sampled time zero). Hernan & Robins; Franklin 2021.
Comparator fidelity: good = the same agent(s) or procedure as the RCT. Moderate = class adaptation of one or both arms, a strategy approximated by initiation of its first drug, or formulation/dose not identifiable where the RCT hypothesis does not hinge on it. Poor = a placebo-controlled RCT emulated with an active-comparator proxy (the estimand changes from X vs placebo to X vs Y), or an agent/formulation/strategy mismatch widely held to change the tested hypothesis.
Outcome fidelity: good = all-cause death and/or hard events with high-PPV inpatient codes (stroke/systemic embolism, MI), with no cause-of-death attribution needed. Moderate = composites needing CV/CHD death from listed causes and/or HF hospitalisation from any-position codes, or with a minor component not capturable. Poor = the primary endpoint is not ascertainable in the EHR (e.g. AF recurrence needing rhythm monitoring), or a dominant component is missing.
Record-only items (do not enter the rule): dose titration protocol (forced titration to target doses) and placebo proxy (already scored through comparator = poor).
INCLUSION: fidelity_include = (F1+F2+F3+F4+F5 <= 1) AND comparator >= moderate AND outcome >= moderate.
Strict sensitivity (S_fid_strict) = zero flags AND the same comparator and outcome conditions (the RCT-DUPLICATE 'close emulation' notion).
The rater viewed no counts, so no feasibility or precision threshold is applied here. The pipeline's pre-registered design-stage sufficiency rule (>= 400 clinical-PS pairs, protocol v1 4c) is applied separately and mechanically.
Layer 2, ECG-mechanism relevance (a priori). Two questions:
(T) Is treatment assignment between the two arms in practice plausibly driven by cardiac structure, function or rhythm that a 12-lead ECG reflects (LV dysfunction/QRS, LVH, atrial disease/AF, conduction/heart rate, ischemic burden/STEMI/Q waves)?
(P) Is the population defined by a cardiac substrate (HF, AF, ACS/established CAD, LVH, valve disease), so that prognosis for the primary endpoint is plausibly ECG-reflected?
high = T and P; medium = exactly one of T or P; low = neither. Hypertension or diabetes primary-prevention populations do not count as a cardiac substrate for P.
Subsets: S_fid = fidelity_include; S_ecg = relevance high or medium; S_both = S_fid AND S_ecg. Also reported: S_fid_strict and S_both_high (S_fid AND relevance high).
```

## 2. Threshold justification

Why these thresholds:
- The items and their weight come from RCT-DUPLICATE. Wang et al. (JAMA 2023;329:1376) found that agreement between RWE and RCT was much stronger in the subset of trials that could be emulated closely. The emulation differences that degraded agreement were in-hospital start, run-in, discontinuation of baseline therapy at randomization, delayed effect over long follow-up, and placebo-comparator proxies.
- Heyard et al. (BMJ Med 2024) re-analysed the same 32 pairs. They showed that the design differences act roughly additively on disagreement. Allowing at most one flag is therefore a pragmatic cut: it keeps enough trials for a sign-flip test while excluding trials with compounded design deviation. The zero-flag cut is reported as a strict sensitivity.
- Franklin et al. (Circulation 2021;143:1002) showed that emulations with poor comparator or outcome proxies (placebo-to-active proxies, soft outcomes) agreed worst. That is why comparator and outcome each need to be at least moderate, and a placebo proxy is disqualifying.
- The 48-month horizon cut marks when a large majority of real-world initiators have discontinued or switched. Beyond it, an ITT-like initiator estimate can no longer represent an adherent RCT arm's long-run effect.

## 3. Per-trial scores

Flags: F1 in-hospital start, F2 responder run-in, F3 discontinuation/switch, F4 delayed effect (horizon >= 48 mo), F5 other time-zero problem. Tit = dose-titration protocol (recorded only). Set: v1.6 = existing key; v1.7 = new confirmation trial.

| Trial | Set | F1 | F2 | F3 | F4 | F5 | n flags | Comparator | Outcome | Tit | Fidelity | Strict | ECG relevance | Cluster |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| comet | v1.6 | 0 | 0 | 0 | 1 | 0 | 1 | poor | good | 1 | **exclude** | exclude | high | C_SINGLE_comet |
| paradigm_hf | v1.6 | 0 | 1 | 1 | 0 | 0 | 2 | moderate | moderate | 1 | **exclude** | exclude | high | C_ARNI |
| paradigm_hf_switch | v1.6 | 0 | 1 | 0 | 0 | 1 | 2 | moderate | moderate | 1 | **exclude** | exclude | high | C_ARNI |
| paradigm_hf_seq | v1.6 | 0 | 1 | 0 | 0 | 0 | 1 | moderate | moderate | 1 | **include** | exclude | high | C_ARNI |
| paragon_hf | v1.6 | 0 | 1 | 1 | 0 | 0 | 2 | good | moderate | 1 | **exclude** | exclude | high | C_ARNI |
| paragon_hf_switch | v1.6 | 0 | 1 | 0 | 0 | 1 | 2 | good | moderate | 1 | **exclude** | exclude | high | C_ARNI |
| transform_hf | v1.6 | 1 | 0 | 1 | 0 | 0 | 2 | moderate | good | 0 | **exclude** | exclude | medium | C_SINGLE_transform_hf |
| elite_ii | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | moderate | good | 1 | **include** | include | medium | C_ARB_VS_ACEI |
| life | v1.6 | 0 | 0 | 1 | 1 | 0 | 2 | moderate | moderate | 0 | **exclude** | exclude | high | C_HTN_ANTIHYPERTENSIVE |
| dionysos | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | poor | 0 | **exclude** | exclude | high | C_AF_RHYTHM_AAD |
| allhat | v1.6 | 0 | 0 | 1 | 1 | 0 | 2 | moderate | moderate | 0 | **exclude** | exclude | low | C_HTN_ANTIHYPERTENSIVE |
| plato | v1.6 | 0 | 0 | 1 | 0 | 0 | 1 | good | moderate | 0 | **include** | exclude | medium | C_P2Y12_ACS |
| triton | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | moderate | 0 | **include** | include | medium | C_P2Y12_ACS |
| aristotle | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | good | 0 | **include** | include | medium | C_AF_OAC_VS_WARFARIN |
| rocket_af | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | good | 0 | **include** | include | medium | C_AF_OAC_VS_WARFARIN |
| rely | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | good | 0 | **include** | include | medium | C_AF_OAC_VS_WARFARIN |
| dapa_hf | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | high | C_DPP4I_PROXY |
| partner | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | moderate | 0 | **include** | include | medium | C_SINGLE_partner |
| emperor_preserved | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | high | C_DPP4I_PROXY |
| east_afnet4 | v1.6 | 0 | 0 | 0 | 1 | 0 | 1 | moderate | moderate | 0 | **include** | exclude | high | C_AF_RHYTHM_AAD |
| cabana | v1.6 | 0 | 0 | 0 | 1 | 0 | 1 | moderate | moderate | 0 | **include** | exclude | high | C_AF_RHYTHM_AAD |
| castle_af | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | high | C_AF_RHYTHM_AAD |
| paradise_mi | v1.6 | 1 | 0 | 1 | 0 | 0 | 2 | moderate | moderate | 1 | **exclude** | exclude | high | C_ARNI |
| dcp | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | moderate | 0 | **include** | include | low | C_HTN_ANTIHYPERTENSIVE |
| ontarget | v1.6 | 0 | 1 | 1 | 1 | 0 | 3 | moderate | moderate | 1 | **exclude** | exclude | medium | C_ARB_VS_ACEI |
| value | v1.6 | 0 | 0 | 1 | 1 | 0 | 2 | moderate | moderate | 0 | **exclude** | exclude | low | C_HTN_ANTIHYPERTENSIVE |
| ascot | v1.6 | 0 | 0 | 1 | 1 | 0 | 2 | moderate | moderate | 0 | **exclude** | exclude | medium | C_HTN_ANTIHYPERTENSIVE |
| empa_reg | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | medium | C_DPP4I_PROXY |
| carolina | v1.6 | 0 | 0 | 0 | 1 | 0 | 1 | good | moderate | 0 | **include** | exclude | low | C_DPP4I_VS_SU |
| invest | v1.6 | 0 | 0 | 1 | 0 | 0 | 1 | moderate | good | 0 | **include** | exclude | high | C_HTN_ANTIHYPERTENSIVE |
| engage_af | v1.6 | 0 | 0 | 0 | 0 | 0 | 0 | good | good | 0 | **include** | include | medium | C_AF_OAC_VS_WARFARIN |
| leader | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | medium | C_DPP4I_PROXY |
| sustain6 | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | medium | C_DPP4I_PROXY |
| rewind | v1.7 | 0 | 0 | 0 | 1 | 0 | 1 | poor | moderate | 0 | **exclude** | exclude | low | C_DPP4I_PROXY |
| declare | v1.7 | 0 | 0 | 0 | 1 | 0 | 1 | poor | moderate | 0 | **exclude** | exclude | low | C_DPP4I_PROXY |
| canvas | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | low | C_DPP4I_PROXY |
| tecos | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | medium | C_DPP4I_VS_SU |
| carmelina | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | poor | moderate | 0 | **exclude** | exclude | low | C_DPP4I_VS_SU |
| valiant | v1.7 | 0 | 0 | 1 | 0 | 0 | 1 | moderate | good | 1 | **include** | exclude | medium | C_ARB_VS_ACEI |
| insight | v1.7 | 0 | 0 | 1 | 0 | 0 | 1 | moderate | moderate | 0 | **include** | exclude | low | C_HTN_ANTIHYPERTENSIVE |
| affirm | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | moderate | good | 0 | **include** | include | high | C_AF_RHYTHM_AAD |
| af_chf | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | moderate | moderate | 0 | **include** | include | high | C_AF_RHYTHM_AAD |
| precision | v1.7 | 0 | 0 | 1 | 0 | 0 | 1 | good | moderate | 1 | **include** | exclude | low | C_SINGLE_precision |
| amplify | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | good | poor | 0 | **exclude** | exclude | low | C_SINGLE_amplify |
| lodestar | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | good | poor | 1 | **exclude** | exclude | medium | C_STATIN_CAD |
| prove_it | v1.7 | 0 | 0 | 0 | 0 | 0 | 0 | moderate | poor | 1 | **exclude** | exclude | medium | C_STATIN_CAD |

## 4. Rationale and sources

- **comet**. Fidelity: 58-mo horizon (F4). The metoprolol token cannot separate tartrate (the RCT arm) from succinate, the dominant US HF formulation, and COMET's hypothesis hinges on tartrate at 50 mg bid. Comparator poor. ECG: HFrEF. The beta-blocker choice depends on heart rate/conduction and LV dysfunction severity; prognosis is LV-driven. *Source: Poole-Wilson Lancet 2003.*
- **paradigm_hf**. Fidelity: Sequential enalapril-then-ARNI active run-in (F2). All RCT patients switched from ACEi/ARB, whereas the new-user design compares ARNI starters (often ARB switchers) with ACEi-naive starters (F3). ACEi class for enalapril. ECG: HFrEF. ARNI vs ACEi choice follows HF severity/EF and specialist care (QRS, LBBB, LV dysfunction); prognosis is LV-driven. *Source: McMurray NEJM 2014; EJHF 2014 baseline.*
- **paradigm_hf_switch**. Fidelity: Active run-in (F2). The prevalent 'continuer' comparator has no time zero defined without future information (F5; this design was superseded by the sequential one). ECG: As PARADIGM-HF. *Source: McMurray NEJM 2014.*
- **paradigm_hf_seq**. Fidelity: Active run-in (F2). The ACEi/ARB-to-ARNI switch is mirrored by sequential sampling at the switch date. ACEi class for enalapril. ECG: As PARADIGM-HF. *Source: McMurray NEJM 2014.*
- **paragon_hf**. Fidelity: Valsartan-then-ARNI active run-in (F2). RCT patients switched from ACEi/ARB; the new-user design does not mirror this (F3). The endpoint is total events vs first event in the emulation. ECG: HFpEF. ARNI use concentrates in the lower-EF/more structurally abnormal range (LVH, LA enlargement, AF); prognosis is structure-driven. *Source: Solomon NEJM 2019.*
- **paragon_hf_switch**. Fidelity: Active run-in (F2). The continuer comparator has no future-free time zero (F5). ECG: As PARAGON-HF. *Source: Solomon NEJM 2019.*
- **transform_hf**. Fidelity: Randomized in hospital to an oral discharge strategy. The furosemide token also captures inpatient IV diuresis, which moves time zero (F1). Most RCT patients were on a prior loop diuretic replaced at randomization; the emulation requires first-ever use with a washout of the other arm (F3). ECG: Prognosis is LV-driven (HF), but the torsemide/furosemide choice is formulary, insurance and renal/diuretic-resistance driven, not cardiac-structural. *Source: Mentz JAMA 2023.*
- **elite_ii**. Fidelity: ACEi-naive population, so the new-user design is mirrored. Class adaptation (losartan vs captopril). All-cause death. ECG: Prognosis is LV-driven (HFrEF, age >= 60), but ARB vs ACEi choice is driven by cough/angioedema intolerance, not cardiac structure. *Source: Pitt Lancet 2000.*
- **life**. Fidelity: Prior antihypertensives were withdrawn (placebo run-in) and replaced by the study drug; emulated initiators often add on (F3). 58-mo horizon (F4). Class adaptation of both arms (v2). ECG: ECG-LVH is itself the entry criterion. Beta-blocker vs ARB choice depends on heart rate/conduction/AF; prognosis is LVH-driven. *Source: Dahlof Lancet 2002.*
- **dionysos**. Fidelity: Same agents and no design flag. The endpoint (AF recurrence or drug discontinuation) needs rhythm monitoring and is not emulable (protocol v1 4b). Outcome poor. ECG: Dronedarone is contraindicated in HFrEF/permanent AF and guided by QT/conduction/structural disease, all ECG-reflected; AF population. *Source: Le Heuzey JCE 2010.*
- **allhat**. Fidelity: About 90% were previously treated, and prior antihypertensives were stopped and replaced by the step-1 drug (F3). 59-mo horizon (F4). Thiazide class for chlorthalidone. CHD death needs cause of death. ECG: Hypertension primary prevention. The CCB vs thiazide choice is driven by electrolytes, gout, oedema and cost; the population is not cardiac-substrate defined. *Source: ALLHAT JAMA 2002.*
- **plato**. Fidelity: Inpatient start is captured by EHR orders for both arms. A substantial share of RCT patients were pre-treated with open-label clopidogrel and switched at randomization; the other-arm washout excludes such switchers (F3). Vascular death needs cause of death. ECG: ACS population (ischemic burden/infarct size, ECG-reflected prognosis). Choice is mainly bleeding risk, age, PCI, OAC and cost; STEMI status contributes only partly. *Source: Wallentin NEJM 2009; PLATO angiographic substudy.*
- **triton**. Fidelity: Clopidogrel-naive at randomization before PCI; same agents; inpatient start visible. Note: no OUTCOMES/HORIZON entry is registered in trial_specs (not analysed at v1 feasibility). ECG: ACS-PCI population. Prasugrel choice is by age, weight, prior stroke and bleeding risk (non-ECG); prognosis is ischemic-burden driven. *Source: Wiviott NEJM 2007.*
- **aristotle**. Fidelity: Same agents; stroke/SE from inpatient codes. VKA experience is a population difference, not a switching-strategy flag. ECG: AF population (atrial cardiopathy, LV function, ECG-reflected stroke risk). DOAC vs warfarin choice is renal, cost/insurance, valve and bleeding driven. *Source: Granger NEJM 2011.*
- **rocket_af**. Fidelity: As ARISTOTLE. ECG: As ARISTOTLE. *Source: Patel NEJM 2011.*
- **rely**. Fidelity: Same agents. The 150 mg benchmark arm is the dominant US dose (110 mg is not US-approved for AF), so the unidentifiable dose is accepted as good. ECG: As ARISTOTLE. *Source: Connolly NEJM 2009.*
- **dapa_hf**. Fidelity: Placebo-controlled RCT emulated with a DPP-4i active-comparator proxy restricted to T2D. Comparator poor. ECG: HFrEF (+T2D). SGLT2i use in HF is cardiology/LV-dysfunction driven; prognosis is LV-driven. *Source: McMurray NEJM 2019; Packer NEJM 2020.*
- **partner**. Fidelity: Procedure vs procedure with time zero at the procedure. 'Disabling' stroke is not identifiable. Strong risk-based channelling is a confounding problem, not a design flag. ECG: Aortic stenosis (LVH, LV function, AF, conduction; ECG-reflected prognosis). TAVR vs SAVR choice is dominated by age, frailty and surgical risk. *Source: Leon NEJM 2016; Mack NEJM 2019.*
- **emperor_preserved**. Fidelity: Placebo-controlled RCT emulated with a DPP-4i proxy (T2D). Comparator poor. ECG: HFpEF (+T2D). SGLT2i choice in HF is cardiac-driven; prognosis is structure-driven (LVH, AF). *Source: Anker NEJM 2021.*
- **east_afnet4**. Fidelity: Add-on rhythm control vs continued rate control, mirrored by the sequential design; early AF (<= 1 y) mirrored. 61-mo horizon with late-diverging benefit (F4). Ablation-first rhythm control not captured. ECG: Rhythm vs rate choice depends on AF pattern, heart rate, QT/conduction and structural disease; AF prognosis. *Source: Kirchhof NEJM 2020.*
- **cabana**. Fidelity: 49-mo horizon (F4). The drug arm is approximated by antiarrhythmic initiators (most RCT drug-arm patients received rhythm-control drugs). Bleeding/cardiac-arrest components approximated. ECG: Ablation vs AAD choice depends on AF type/burden, atrial size and LV function; AF prognosis. *Source: Packer JAMA 2019.*
- **castle_af**. Fidelity: The RCT control was conventional therapy, about 70% rate control and 30% rhythm control (mostly amiodarone). Emulating it with AAD initiators changes the tested hypothesis. Comparator poor. ECG: HFrEF + AF. The choice depends on LV function, AF burden and conduction/device; prognosis is LV-driven. *Source: Marrouche NEJM 2018.*
- **paradise_mi**. Fidelity: Randomized in hospital 0.5-7 d post-MI (mean 4.3 d). Post-MI ARNI starts are off-label and plausibly delayed or outpatient within the 30-d window, while ACEi starts early (F1). Prior ACEi/ARB was stopped at randomization, which the ACEi washout does not mirror (F3). The endpoint includes outpatient incident HF. ECG: Post-MI LV dysfunction. ARNI vs ACEi choice follows EF/congestion; prognosis tracks infarct size/LV function. *Source: Pfeffer NEJM 2021; Jering EJHF 2021.*
- **dcp**. Fidelity: Pragmatic switch from HCTZ vs continuation, mirrored by the sequential design; same agents. Urgent revascularisation not captured; non-cancer death approximated by all-cause death. ECG: Hypertension. The choice is thiazide preference/potassium; the population is not cardiac-substrate defined. *Source: Ishani NEJM 2022.*
- **ontarget**. Fidelity: 3-week single-blind active run-in (ramipril, telmisartan, combination; 11.7% excluded) (F2). Prior ACEi/ARB was stopped for run-in, not mirrored (F3). 56-mo horizon (F4). Class adaptation. ECG: Established vascular disease population (ischemic burden, ECG-reflected prognosis). ARB vs ACEi choice is cough/intolerance driven. *Source: ONTARGET NEJM 2008.*
- **value**. Fidelity: Prior antihypertensives were replaced by the study drug at randomization (F3). 50-mo horizon (F4). ARB class for valsartan. Emergency-procedure component not captured. ECG: Emulated gate is hypertension only. ARB vs CCB choice follows DM/CKD/oedema, not cardiac structure. *Source: Julius Lancet 2004.*
- **ascot**. Fidelity: Previously treated patients were switched to the randomized regimen (F3). 66-mo horizon (F4). Beta-blocker class for atenolol, with add-on strategy. Silent MI is not captured. ECG: Hypertension without CAD, so prognosis is not substrate-driven. Beta-blocker vs CCB choice is plausibly heart-rate/AF/palpitation driven. *Source: Dahlof Lancet 2005.*
- **empa_reg**. Fidelity: Placebo-controlled RCT emulated with a DPP-4i proxy. Comparator poor. ECG: T2D + established CVD (ischemic burden). SGLT2i vs DPP-4i choice is glycaemic, renal and cost driven (and HF labels), not subclinical structure. *Source: Zinman NEJM 2015.*
- **carolina**. Fidelity: Same agents, add-on to background therapy. 76-mo horizon (F4). ECG: T2D. DPP-4i vs SU choice is hypoglycaemia/cost driven; the high-CV-risk criterion is not applied, so the population is not cardiac-substrate defined. *Source: Rosenstock JAMA 2019.*
- **invest**. Fidelity: Previously treated hypertensive CAD patients were moved to the assigned strategy (F3). The strategy is approximated by initiation of its first drug. Death/MI/stroke. ECG: CAD. Verapamil vs atenolol choice depends on LV dysfunction/prior MI (favour BB), conduction and heart rate; ischemic-burden prognosis. *Source: Pepine JAMA 2003.*
- **engage_af**. Fidelity: Same agents. The 60 mg arm with label dose-halving matches US labelling. ECG: As ARISTOTLE. *Source: Giugliano NEJM 2013.*
- **leader**. Fidelity: Placebo-controlled RCT emulated with a DPP-4i active-comparator proxy. Comparator poor. 46-mo horizon (< 48, F4 = 0). 3-point MACE needs CV death. ECG: Gate: T2D plus CVD/CKD/HF (mostly established CVD, i.e. ischemic burden). GLP-1RA vs DPP-4i choice is obesity, glycaemia and cost driven. *Source: Marso NEJM 2016;375:311.*
- **sustain6**. Fidelity: Placebo-controlled RCT, DPP-4i proxy. Comparator poor. ECG: As LEADER. *Source: Marso NEJM 2016;375:1834.*
- **rewind**. Fidelity: Placebo-controlled RCT, DPP-4i proxy. Comparator poor. 65-mo horizon (F4). ECG: Broad T2D age >= 50 with no cardiac-substrate gate. Choice is glycaemic/weight/cost driven. *Source: Gerstein Lancet 2019.*
- **declare**. Fidelity: Placebo-controlled RCT, DPP-4i proxy. Comparator poor. 50-mo horizon (F4). Co-primary CV death/HF hospitalisation. ECG: Broad T2D with no cardiac gate. SGLT2i vs DPP-4i choice is renal, glycaemic and cost driven (as rated for EMPA-REG). *Source: Wiviott NEJM 2019.*
- **canvas**. Fidelity: Placebo-controlled RCT, DPP-4i proxy. Comparator poor. 43-mo horizon. ECG: Emulated gate is T2D only (the RCT's CVD/risk-factor criterion is not applied). Non-cardiac choice. *Source: Neal NEJM 2017.*
- **tecos**. Fidelity: Placebo-controlled RCT emulated with a sulfonylurea proxy (RCT-DUPLICATE found this proxy less reliable). Comparator poor. ECG: Gate: T2D plus established CVD (ischemic burden). DPP-4i vs SU choice is hypoglycaemia/cost driven. *Source: Green NEJM 2015.*
- **carmelina**. Fidelity: Placebo-controlled RCT, sulfonylurea proxy. Comparator poor. ECG: Gate: T2D plus kidney disease, which is not a cardiac substrate. Choice is renal dosing/hypoglycaemia driven. *Source: Rosenstock JAMA 2019;321:69.*
- **valiant**. Fidelity: Randomized in hospital 0.5-10 d post-MI. RAS blockade (ACEi, or ARB as the guideline alternative) is standard in-admission care, so F1 = 0. About 40% were on an ACEi that was stopped at randomization, and the ACEi washout excludes these switchers (F3). Class adaptation (valsartan vs captopril). All-cause death. ECG: Post-MI LV dysfunction/HF (ECG-reflected prognosis: infarct size, QRS, EF). ARB vs ACEi choice is intolerance driven (as rated for ELITE II). *Source: Pfeffer NEJM 2003;349:1893.*
- **insight**. Fidelity: Previously treated hypertensives were switched to the randomized drug after a placebo run-in, not mirrored (F3; same criterion as ALLHAT/VALUE/ASCOT). Nifedipine (RCT: GITS) and thiazide class (RCT: co-amilozide) adaptations. Composite needs CV death and HF hospitalisation. ECG: Hypertension plus risk factor (CVD, DM, LVH/cardiomegaly or lipid code); the population is not cardiac-substrate defined. CCB vs thiazide choice is non-cardiac. *Source: Brown Lancet 2000.*
- **affirm**. Fidelity: Rhythm-control drug added vs continued rate control, mirrored by the sequential add-on design (as EAST-AFNET 4). 42-mo horizon. The strategy is approximated by drug initiation (cardioversion not modelled). All-cause death. ECG: Rhythm vs rate choice depends on AF pattern, heart rate, QT/conduction and structural disease; AF prognosis. *Source: Wyse NEJM 2002.*
- **af_chf**. Fidelity: Same sequential add-on design; HFrEF gate (EF > 35 excluded when known). The strategy is approximated. CV death needs listed cause. ECG: AF + HFrEF. The choice depends on LV function, AF burden, QT/conduction (amiodarone); prognosis is LV-driven. *Source: Roy NEJM 2008.*
- **precision**. Fidelity: Same agents (two of three RCT arms). RCT patients needing chronic NSAIDs commonly switched from a prior NSAID at randomization, and the prior-year NSAID exclusion removes such switchers (F3). OTC naproxen is unseen. Celecoxib dose titration allowed. APTC MACE needs CV death. ECG: Arthritis plus CV risk factor (HTN/lipids alone qualify); not cardiac-substrate defined. Celecoxib vs naproxen choice is GI-risk driven. *Source: Nissen NEJM 2016.*
- **amplify**. Fidelity: Both anticoagulants start at the index VTE encounter; the enoxaparin bridge is implicit in warfarin care. Recurrent VTE from a new inpatient stay with any VTE code is low-specificity (index-VTE codes recur), outpatient-managed recurrences are missed and VTE-related death is not captured. Outcome poor. ECG: Acute VTE with AF excluded; not a cardiac substrate. Choice is renal, cancer, cost and patient-preference driven. *Source: Agnelli NEJM 2013.*
- **lodestar**. Fidelity: Same agents (dose follows a factorial treat-to-target/high-intensity scheme; recorded). Any coronary revascularisation was the dominant component (about 5.3% of 8.7%, i.e. over half the events) and is not captured. Outcome poor. ECG: CAD population (ischemic burden). Rosuvastatin vs atorvastatin choice is formulary/intensity driven. *Source: Lee BMJ 2023.*
- **prove_it**. Fidelity: In-hospital ACS start is standard for both statins (F1 = 0). About 25% prior statin use, below the 'substantial share' bar for F3. Dose is not identifiable, but post-2013 post-ACS atorvastatin is predominantly high-intensity, so comparator moderate. Revascularisation >= 30 d, the largest primary component, is not captured. Outcome poor. ECG: ACS population (ischemic burden/infarct). Statin choice is intensity/formulary driven. *Source: Cannon NEJM 2004.*

## 5. Subsets

### All trials

- **S_fid** (19): paradigm_hf_seq, elite_ii, plato, triton, aristotle, rocket_af, rely, partner, east_afnet4, cabana, dcp, carolina, invest, engage_af, valiant, insight, affirm, af_chf, precision
- **S_fid_strict** (10): elite_ii, triton, aristotle, rocket_af, rely, partner, dcp, engage_af, affirm, af_chf
- **S_ecg** (35): comet, paradigm_hf, paradigm_hf_switch, paradigm_hf_seq, paragon_hf, paragon_hf_switch, transform_hf, elite_ii, life, dionysos, plato, triton, aristotle, rocket_af, rely, dapa_hf, partner, emperor_preserved, east_afnet4, cabana, castle_af, paradise_mi, ontarget, ascot, empa_reg, invest, engage_af, leader, sustain6, tecos, valiant, affirm, af_chf, lodestar, prove_it
- **S_both** (15): paradigm_hf_seq, elite_ii, plato, triton, aristotle, rocket_af, rely, partner, east_afnet4, cabana, invest, engage_af, valiant, affirm, af_chf
- **S_both_high** (6): paradigm_hf_seq, east_afnet4, cabana, invest, affirm, af_chf

### Existing v1.6 keys (31)

- **S_fid** (14): paradigm_hf_seq, elite_ii, plato, triton, aristotle, rocket_af, rely, partner, east_afnet4, cabana, dcp, carolina, invest, engage_af
- **S_fid_strict** (8): elite_ii, triton, aristotle, rocket_af, rely, partner, dcp, engage_af
- **S_ecg** (27): comet, paradigm_hf, paradigm_hf_switch, paradigm_hf_seq, paragon_hf, paragon_hf_switch, transform_hf, elite_ii, life, dionysos, plato, triton, aristotle, rocket_af, rely, dapa_hf, partner, emperor_preserved, east_afnet4, cabana, castle_af, paradise_mi, ontarget, ascot, empa_reg, invest, engage_af
- **S_both** (12): paradigm_hf_seq, elite_ii, plato, triton, aristotle, rocket_af, rely, partner, east_afnet4, cabana, invest, engage_af
- **S_both_high** (4): paradigm_hf_seq, east_afnet4, cabana, invest

### New v1.7 confirmation trials (15)

- **S_fid** (5): valiant, insight, affirm, af_chf, precision
- **S_fid_strict** (2): affirm, af_chf
- **S_ecg** (8): leader, sustain6, tecos, valiant, affirm, af_chf, lodestar, prove_it
- **S_both** (3): valiant, affirm, af_chf
- **S_both_high** (2): affirm, af_chf

Caveats for use:
- The subsets include design variants of the same RCT (e.g. paradigm_hf_seq). Apply the project's one-per-RCT convention downstream.
- TRITON has no registered outcome or horizon in trial_specs and did not pass v1 feasibility.
- Feasibility (>= 400 clinical-PS pairs) is applied separately by the pipeline.
- All 7 placebo-controlled new diabetes trials (DPP-4i or SU proxy) fail on comparator = poor, as DAPA-HF, EMPEROR-Preserved and EMPA-REG did.

## 6. Comparator clusters (design-only proposal)

Design-only cluster proposal for clustered/sign-flip tests. Trials share a cluster when they share a comparator drug class or arm patients drawn from the same prescribing pool, or when candidates.md flags record overlap of 50-80%: LEADER-EMPA-REG 0.58 (C_DPP4I_PROXY), VALIANT-ONTARGET 0.61 (C_ARB_VS_ACEI), INSIGHT-ALLHAT 0.63 (C_HTN_ANTIHYPERTENSIVE). AFFIRM contains most EAST-AFNET 4 records (C_AF_RHYTHM_AAD). CARMELINA-CAROLINA is 0.31, sharing linagliptin and SU arms (C_DPP4I_VS_SU). AMPLIFY shares the apixaban/warfarin tokens with the AF trials, but its population is disjoint (AF excluded; overlap 0.01), so it is a singleton. LODESTAR and PROVE IT share the atorvastatin arm within CAD/ACS. Hypertension trials are pooled into one cluster because their amlodipine, thiazide, ARB and beta-blocker arms interlock. Sensitivity: split C_HTN into CCB-vs-thiazide (allhat, insight), and C_AF_RHYTHM_AAD into sequential add-on (east_afnet4, affirm, af_chf) and ablation (cabana, castle_af).

| Cluster | Trials |
|---|---|
| C_DPP4I_PROXY | dapa_hf, emperor_preserved, empa_reg, leader, sustain6, rewind, declare, canvas |
| C_DPP4I_VS_SU | carolina, tecos, carmelina |
| C_AF_RHYTHM_AAD | east_afnet4, affirm, af_chf, cabana, castle_af, dionysos |
| C_ARB_VS_ACEI | elite_ii, ontarget, valiant |
| C_ARNI | paradigm_hf, paradigm_hf_switch, paradigm_hf_seq, paragon_hf, paragon_hf_switch, paradise_mi |
| C_HTN_ANTIHYPERTENSIVE | life, allhat, value, ascot, dcp, invest, insight |
| C_AF_OAC_VS_WARFARIN | aristotle, rocket_af, rely, engage_af |
| C_P2Y12_ACS | plato, triton |
| C_STATIN_CAD | lodestar, prove_it |
| C_SINGLE_comet | comet |
| C_SINGLE_transform_hf | transform_hf |
| C_SINGLE_partner | partner |
| C_SINGLE_precision | precision |
| C_SINGLE_amplify | amplify |

## 7. Candidate coverage

First pass (commit 68a13a5): docs/v17/candidates.json was absent, so only the 31 existing keys were rated. Second pass (same day): the 15 built v1.7 trials listed in candidates.md 'Selected for build' were rated under the unchanged rule. Screened-not-built candidates (savor, tosca_it, accomplish, euclid, isar_react5, cares, fast, oral_surv, pronounce, ideal) were not rated.

## 8. Blinding attestation

- scripts/trial_specs.py (full file, including the V17 block lines 651-949)
- docs/v16/V17_CONFIRMATION_PLAN.md (full file, 34 lines)
- docs/v13/rct_facts.json (notes; per-trial design fields and value_notes, truncated print)
- docs/PROTOCOL_V1.md lines 44-147 (sections 3, 4, 4b, 4c: trial designs, PICOT, sufficiency rule; these contain design-stage pair counts for DAPA-HF/PARTNER/PARAGON and emulation-rating labels, not used)
- docs/v14/closeness_rating.json: only the 'method' string was printed (plus the list of top-level keys, which printing the method exposed); no ratings viewed
- docs/v17/candidates.md (full file). It contains count-only feasibility numbers (arm sizes, pooled event counts, record-overlap shares), which were ignored for rating; only the overlap flags were used, for clusters.
- docs/v17/candidates.json: only the top-level keys and the field names of one entry were printed (design fields duplicate trial_specs V17); no feasibility block was printed
- CLAUDE.md (auto-loaded)
- Web searches: CASTLE-AF control-arm composition, PLATO clopidogrel pretreatment, ONTARGET run-in, PARADISE-MI design, TRANSFORM-HF design, PROVE IT endpoint components, LODESTAR endpoint components, VALIANT prior-ACEi discontinuation
- Directory listings: docs/v16 and docs/v17 (file names only; docs/v17/V17_BLINDED_SUBSET_EXISTING18.md was seen in a listing and NOT opened)

No file under /mnt/raid0, no audit/summary/panel/headline/result file (including docs/v17/V17_BLINDED_SUBSET_EXISTING18.md), no report.md, presentation or abstract, and no git log/show/diff of results was opened. No HR/SMD/balance numbers from any emulation were seen; per candidates.md, no PS, balance or HR exists for any v1.7 trial. The RATING_ITEMS tuples in trial_specs.py (an earlier design rating) were visible in the allowed file; the ratings here were derived independently from the rule above. The rule text was not changed between the two passes.
