# Structured trial search: execution log

Executed 2026-10-13, following [SEARCH_PROTOCOL.md](SEARCH_PROTOCOL.md) (written first, the same day). Results are in [CANDIDATES.md](CANDIDATES.md) and [candidates.json](candidates.json).

How the search was run:
- **Who:** an LLM agent was the single screener.
- **What was read:** literature only. No patient data was read and no data screen or count was run.
- **Web access:**
  - PubMed E-utilities and the ClinicalTrials.gov API v2, with no API key, no e-mail and no identifying parameter. Only the default Python/curl user agent was sent.
  - One PMC full-text page (the RCT-DUPLICATE trial list).
- **Working files:** intermediate files (record lists, scripts) were kept in the session scratchpad and are not committed.

## 1. Sources and queries (as executed)

### 1.1 PubMed (E-utilities `esearch`, then `efetch` XML for titles and abstracts), 2026-10-13

Every query is `RCT AND JRN AND DT AND HARD AND <AREA> NOTSEC`. The common blocks are exactly as in protocol §4:
- `RCT`
- `JRN` (NEJM, Lancet, JAMA, JACC, Circulation, EHJ)
- `DT` (1995/01/01–2025/12/31, by publication date; records with a 2025 e-publication and a 2026 issue date are included)
- `HARD`
- `NOTSEC`

The area blocks are the strings in protocol §4.

| ID | Area | Hits |
|---|---|---|
| Q1 | AF / anticoagulation | 508 |
| Q2 | HF and devices | 822 |
| Q3 | Hypertension | 220 |
| Q4 | Diabetes / cardiometabolic | 414 |
| Q5 | ACS / CAD / antiplatelet / revascularisation | 2,444 |
| Q6 | Lipids | 350 |
| Q7 | VTE | 126 |
| Q8 | Valve / structural | 192 |
| Q9 | Stroke / carotid / peripheral / aortic | 452 |
| Q10 | Other CV safety / vaccines | 118 |
| **Total** | | **5,646 hits, 4,611 unique PMIDs** |

### 1.2 ClinicalTrials.gov API v2, 2026-10-13

The parameters were exactly those of protocol §5:
- `query.cond` = CV condition list;
- `filter.advanced` = interventional AND randomized AND (Phase 3 OR Phase 4) AND enrollment ≥1,000 AND start 1995-01-01 to 2022-12-31;
- `filter.overallStatus` = COMPLETED|TERMINATED.

The query returned **908 registry records**.

### 1.3 RCT-DUPLICATE trial list

The source was Wang SV, et al. JAMA 2023 (PMID 37097356), PMC full text (PMC10130954), read 2026-10-13. It lists **32 trials**: 25 cardiovascular or cardiometabolic, and 7 non-CV (osteoporosis and COPD/asthma).

### 1.4 Guideline-cited landmark trials (hand search) and targeted PubMed checks

The landmark trials of the guidelines listed in protocol §3 were enumerated from the agent's knowledge of those guidelines, then verified one by one on PubMed.

A further 19 targeted PubMed queries recovered primary papers that the journal-restricted stream missed or that were published elsewhere. The query strings and hit counts follow.

| Target | Query | Hits | Primary paper found |
|---|---|---|---|
| TOTAL | `"routine manual thrombectomy"[ti] AND "N Engl J Med"[ta]` | 1 | PMID 25853743 |
| ADAPTABLE | `ADAPTABLE[tiab] AND aspirin[ti] AND dosing[ti]` | 16 | secondary papers only; primary PMID 33999548 then verified by efetch |
| ENTRACTE | `tocilizumab[ti] AND etanercept[ti] AND cardiovascular[ti]` | 2 | PMID 31469238 (Arthritis Rheumatol) |
| COBRRA | `(apixaban[ti] AND rivaroxaban[ti]) AND (bleeding[ti]) AND venous[ti]` | 17 | PMID 42269161 (NEJM 2026; outside the window) |
| JMIC-B | `JMIC-B[tiab]` | 7 | primary paper not retrieved |
| CONVINCE | `"Controlled Onset Verapamil Investigation"[tiab]` | 13 | PMID 12709465 |
| ALL-HEART | `ALL-HEART[tiab] AND allopurinol[ti]` | 7 | PMID 36216006 |
| WRAP-IT | `"Antibacterial Envelope"[ti]` | 48 | PMID 30883056 |
| RE-COVER II | `dabigatran[ti] AND "venous thromboembolism"[ti] AND Circulation[ta] AND 2014[dp]` | 1 | PMID 24344086 |
| CHAMPION PHOENIX | `cangrelor[ti] AND "N Engl J Med"[ta] AND 2013[dp]` | 3 | PMID 23473369 |
| CASE-J | `CASE-J[tiab] AND candesartan[ti] AND Hypertension[ta]` | 0 | not retrieved |
| UKPDS 34 | `"UK Prospective Diabetes Study"[tiab] AND metformin[ti] AND 1998[dp]` | 1 | PMID 9742977 |
| SPORTIF III | `SPORTIF III[tiab]` | 44 | secondary only (SPORTIF V found in Q1) |
| TiCAB | `TiCAB[tiab]` | 8 | secondary only (registry record used) |
| OAT | `"persistent occlusion after myocardial infarction"[ti]` | 0 | primary found in Q5 (PMID 17105759) |
| PARTNER 2A | `"Intermediate-Risk Patients"[ti] AND transcatheter[ti] AND 2016[dp] AND "N Engl J Med"[ta]` | 1 | PMID 27040324 |
| ELITE | `ELITE[tiab] AND losartan[ti] AND captopril[ti] AND Lancet[ta] AND 1997[dp]` | 1 | PMID 9074572 |
| HEAAL | `HEAAL[tiab]` | 24 | primary found in Q2 (PMID 19922995) |
| NAVIGATE ESUS | `NAVIGATE ESUS[tiab]` | 41 | primary found in Q1 (PMID 29766772) |

Three further registry checks were run: PEPPER (`PEPPER[tiab] AND aspirin AND arthroplasty AND RCT[pt]`), EPCAT III and TC4.
- **PEPPER:** 0 hits, so treated as unpublished.
- **EPCAT III:** NEJM 2026, outside the window.
- **TC4:** CMAJ 2025, a cluster trial.

### 1.5 Effect verification, 2026-10-13

All benchmarks quoted in CANDIDATES.md were transcribed from the primary-paper abstract, retrieved by `efetch` for 96 PMIDs. Every PMID cited in candidates.json was checked against the set of PMIDs retrieved in this session. One unverifiable PMID (POISE) was removed automatically.

## 2. Screening procedure and deviations

1. **Scripted title pre-screen.** This step was added during execution and is a deviation; the protocol foresaw manual screening of all records. A documented rule flagged two kinds of record:
   - (a) secondary-publication titles, e.g. "in the X trial", "insights from", "analysis", "according to" (1,003 records);
   - (b) abstracts whose largest parsed participant count was below 1,000 (1,347 records after a parser fix).

   The size parser was corrected once during screening: it had swallowed numbers inside phrases, and all records passing either version were read. Two flagged subsets were then re-screened manually:
   - **secondary-title flags:** the 379 records with N ≥1,000 or unparsed N and no secondary keyword;
   - **size flags:** the 765 records with parsed N ≥400 (because arm counts are often reported instead of totals) or published in NEJM, Lancet or JAMA.
2. **Manual title (and, where needed, abstract) screening:**
   - **3,410** unique PubMed records were read;
   - **1,201** were excluded by the scripted rule alone without being read (624 secondary-title flags and 577 size flags);
   - all **908** ClinicalTrials.gov records were screened by acronym, title and intervention.
3. **Record-to-trial linkage.** Retained records were collapsed to trials by name and acronym. Secondary papers, extended follow-ups and companion analyses were merged into the parent trial (reason Q).
4. **Trial-level eligibility (abstract level).** For every trial considered, E1–E7 were judged from the primary abstract. A single exclusion reason was recorded (codes in protocol §2, plus *near-dup*, *rare* and *date*).
5. **Coverage matching.** Trials were matched by name against:
   - `scripts/trial_specs.py`;
   - `docs/v17/candidates.md` and `docs/v18/af_candidates.md`, including the "screened, not built" and "not screened" tables;
   - the paper's Table 1;
   - legacy configs in `archive/2026-09-09-legacy-v1/configs/`.

   Pool trials were also matched automatically against the retrieved PubMed and CT.gov text (regex on acronym or title) to test whether this search would have found them.

## 3. PRISMA-style flow (aggregate counts)

```
IDENTIFICATION
  PubMed (10 area queries, journal-restricted)      5,646 hits -> 4,611 unique records
  ClinicalTrials.gov API v2                           908 registry records
  RCT-DUPLICATE list (Wang 2023)                       32 trials (25 CV/cardiometabolic)
  Guideline hand search + 19 targeted PubMed queries  (trial-level additions; see §1.4)

SCREENING (records)
  PubMed records read at title/abstract level        3,410
  PubMed records excluded by scripted rule only      1,201 (secondary-title or N<1,000; not read)
  CT.gov records screened                              908
  -> records collapsed to trials (secondary, follow-up and companion papers merged into the parent trial)

ELIGIBILITY (trials, abstract level)
  Trials assessed                                      316  = 68 pool trials retrieved + 38 new A-C + 210 new in Group D
  Excluded (fail E1-E7)                                155  (P 37, X 57, O 27, N 10, S 9, D 7, date 4, R 2, E2 1, near-dup 1)
  Eligible (meet E1-E7)                                161

INCLUDED / CLASSIFIED (eligible trials)
  Already in the current 99-candidate pool              68  (42%)
  Only in the legacy v1 archive                          4  (EINSTEIN-DVT, EINSTEIN-PE, RE-COVER II, DAPA-CKD)
  New (not in pool or archive)                          89
     of which Group A 11 | Group B 13 (3 legacy) | Group C 14 (1 legacy)  [38 A-C, 4 of them legacy]
     and Group D-eligible 55 (near-duplicate cohort 37; too rare 18)
  Group D also lists the 155 ineligible trials for transparency (126 table rows covering 210 trials)
```

Notes on the counts:
- **Pool trials (the 68).** These are pool trials that meet E1–E7 *and* were retrieved by this search's sources. Two further eligible pool trials (ORAL Surveillance, NEJM 2022; OPTIMAS, Lancet 2024) were not retrieved, because their titles lack the area terms.
- **Pool trials that fail E1–E7.** Examples: TOPCAT and HOPE-3 (placebo); DIONYSOS, RAAFT-2 and the other AF-recurrence trials (outcome); PRAGUE-17, RAFT-AF and RENAL-AF (size under 1,000 and not a landmark); AVERROES and BAFTA (aspirin). These trials are excluded from the coverage denominator.
- **Counting rule.** Each trial is counted once. Grouped rows in Group D count each trial separately. Design variants of one trial (STICH/STICHES; ALLHAT arms) count once.

## 4. Screening decisions by stage (aggregate)

Trial-level exclusion reasons (ineligible, 155 trials):

| Reason | Trials | Typical examples |
|---|---|---|
| X: strategy not identifiable or not used in 2011–2024 | 57 | aspirin comparators; dose and BP-target strategies; drugs never marketed or withdrawn; device brand; access site |
| P: placebo without an accepted proxy | 37 | DIG, RALES, EMPHASIS-HF, FOURIER, ODYSSEY, SELECT, colchicine trials |
| O: endpoint not ascertainable | 27 | venography prophylaxis trials; index-stay periprocedural endpoints; glycaemic primary |
| N: population not identifiable | 10 | ESUS; multivessel/left-main anatomy (COMPLETE, FIRE, FULL REVASC, EXCEL, NOBLE) |
| S: size <1,000 and not a landmark | 9 | COAPT, PFO trials, OVER |
| D: design | 7 | cluster-crossover; no-device comparators without a decision point |
| date: outside 1995–2025 | 4 | COBRRA (2026), OCEAN (2026), EPCAT III (2026), PEPPER (unpublished) |
| R: retracted | 2 | Jikei Heart, KYOTO HEART |
| E2: non-CV primary endpoint | 1 | DANFLU-2 |
| near-dup (and renal endpoint) | 1 | FLOW |

Eligible but expected to be infeasible (Group D-eligible, 55 trials):

| Reason | Trials | Examples |
|---|---|---|
| near-dup | 37 | MADIT-CRT (RAFT); PIONEER 6 (SOUL); REDUCE-AMI and REBOOT (BETAMI-DANBLOCK); TOTAL (TASTE); TAVI-vs-SAVR trials (PARTNER, already analysed); carotid trials (CREST); bivalirudin trials (VALIDATE); FRISC II and others (TACTICS) |
| rare | 18 | verapamil (CONVINCE); pioglitazone (PROactive); edoxaban (Hokusai); ertugliflozin, lixisenatide, alogliptin; biologic arm (ENTRACTE); rivaroxaban after TAVR (GALILEO) |

The rarity judgements rest on the project's previous count-only screens, not on new counts:
- INVEST verapamil: 316 initiators;
- TOSCA.IT pioglitazone: 96 with an ECG;
- edoxaban: about 150 users;
- ORAL Surveillance tofacitinib: 87 with an ECG.

## 5. Coverage check

**Coverage = eligible trials already in the project's candidates ÷ all eligible trials identified.**

| Definition | Numerator | Denominator | Coverage |
|---|---|---|---|
| Current pool, all eligible trials (including near-duplicates and rare-drug trials) | 68 | 161 | **42%** |
| Current pool + legacy v1 archive | 72 | 161 | 45% |
| Current pool vs eligible *and plausibly feasible* new trials (A–C only; D-eligible excluded) | 68 | 106 | 64% |
| Recall check: eligible pool trials retrieved by this search | 68 | 70 | 97% |

Interpretation:
- **Recall.** The pool's eligible trials were almost all recovered by this search, at 97% recall. This supports the search's sensitivity for the kinds of trials the project already uses.
- **Distribution of the uncovered trials.** Most eligible trials outside the pool fall into four kinds:
  - (i) procedure and device trials (CRT, carotid, AAA, PAD, PCI vs CABG, thrombectomy), which the pool mostly lacks beyond LAAO/TAVR/ablation;
  - (ii) decision-point strategy trials (early invasive, β-blocker after MI, revascularisation vs medical therapy);
  - (iii) near-duplicate same-question trials that offer alternative benchmarks on an existing or proposed cohort;
  - (iv) rare-drug trials.
- **Coverage by area.** AF/anticoagulation is the best-covered area: no AF trial entered Groups A–C, and nearly all eligible AF trials were already in the v1.8 lists.

Eligible pool trials (70), with the sources in this search that retrieved each (PubMed / CT.gov / RCT-DUPLICATE):
- **AF / anticoagulation:**
  - the four pivotal DOAC-vs-warfarin trials (ARISTOTLE, ROCKET-AF, RE-LY, ENGAGE AF);
  - rhythm-control trials (AFFIRM, AF-CHF, EAST-AFNET 4, CABANA, CASTLE-AF);
  - LAAO and switch trials (PROTECT AF, FRAIL-AF, LAAOS III, ACTIVE W, OPTION);
  - AF-PCI trials (AUGUSTUS, PIONEER AF-PCI, RE-DUAL PCI, ENTRUST-AF PCI, ENVISAGE-TAVI AF);
  - timing and other (ELAN, OPTIMAS*, INVICTUS, RIVER).
- **HF:** COMET, PARADIGM-HF, PARAGON-HF, TRANSFORM-HF, ELITE II, DAPA-HF, EMPEROR-Reduced, EMPEROR-Preserved, DELIVER, PARADISE-MI, VALIANT.
- **Hypertension:** LIFE, ALLHAT, VALUE, ASCOT-BPLA, INSIGHT, ACCOMPLISH, INVEST, ONTARGET, DCP.
- **Diabetes:**
  - placebo-controlled CVOTs (EMPA-REG, LEADER, SUSTAIN-6, REWIND, DECLARE, CANVAS, TECOS, SAVOR, CARMELINA, CREDENCE);
  - active-comparator trials (CAROLINA, TOSCA.IT, DEVOTE).
- **ACS / CAD:** PLATO, TRITON, ISAR-REACT 5, EUCLID.
- **Lipids:** IDEAL, LODESTAR, PROVE IT.
- **VTE:** AMPLIFY.
- **Valve:** PARTNER (2A/3).
- **Other:** PRECISION, CARES, FAST, ORAL Surveillance*, PRONOUNCE.

(* = not retrieved by this search.) The per-trial retrieval flags are in `candidates.json` → `pool_eligible_coverage`.

## 6. Limitations

1. **Single LLM screener and partial scripted exclusion.** There was no second reviewer. 1,201 PubMed records (26%) were excluded by a scripted title and size rule without being read. The rule is conservative toward primary papers, but it can miss primaries whose title contains words like "analysis", or whose abstract reports only small arm counts. One such miss (JELIS, flagged as secondary) was recovered during a validation check of the rule; others may remain.
2. **Journal restriction.** The PubMed stream covered six journals. Trials elsewhere were reached only through CT.gov (registered trials from about 2000 onwards), RCT-DUPLICATE and hand search. Recall of eligible pool trials was 97% (68/70). The two misses (ORAL Surveillance, OPTIMAS) were lost to the title-term restriction, not the journal filter, which shows that the area-term blocks also lose trials.
3. **Not used:** Embase and CENTRAL, by design (no key- or e-mail-free access). Asian national trials in regional journals are under-represented (e.g. CASE-J and JMIC-B were not retrievable).
4. **Effects from abstracts.** Benchmarks come from abstracts, not full texts:
   - FREEDOM and SYNTAX report rates and P values without an HR in the abstract;
   - SURPASS-CVOT and NORDIL follow-up durations are not stated in the abstract.

   The full-text HR, CI and the registered estimand must be checked before any registration.
5. **Feasibility is a design-level judgement.** No counts were run. Group A means "no proxy or new design needed", not "will pass the size gate". Several A trials carry an explicit size risk: CIBIS III, SURPASS-CVOT (short window), TASTE (declining thrombectomy use), SCOT and CTOPP.
6. **Near-duplicate classification is anticipatory.** It follows the project's 80% record rule as applied in v1.7/v1.8, judged from cohort definitions, not computed. In several cases (DapaTAVI vs PARTNER; BEST-CLI, SWEDEPAD 1 and VOYAGER PAD) the rule's interpretation for same-records/different-contrast cohorts needs a decision by the user.
7. **New designs.** Group B/C trials marked "decision-point", "grace period" or "add-on" would need a clone-censor-weight or non-initiator design that the pipeline does not yet have. Non-initiator comparators are not an accepted RCT-DUPLICATE proxy and would score CO = 2.
8. **Date window.** COBRRA (apixaban vs rivaroxaban in VTE; NEJM 2026) is outside the protocol window but is the closest new Group A/C analogue. It is kept on a watch list.
