# v1.9 sensitivity analysis: outpatient initiators (results)

Plan: `docs/v19/SENS_OUTPATIENT_PLAN.md` (committed ac0a347, with the a priori RCT-setting classification, before any
restricted result; deviation 1 committed 48d594e before results). Code: `scripts/v19/sens_outpatient.py`. Outputs:
`/mnt/raid0/rbc58/ecg-tte/audits/claude-v19-sens-outpatient/` (setting, power, per_trial, summary, domains,
restriction .csv; tables.md). Exploratory; aggregates only; values derived from counts 1–10 suppressed (–).

## Reproduction

With the population mask set to all rows, all 38 trials × 3 halves × (P1, P5, unmatched) × arms (1,026 cells)
reproduce `claude-v17-confirm/results_all.csv`, `results_p5.csv` and `claude-v18-af-confirm/results_af5.csv`.
n, n_t, n_c and n_pairs are identical. log HR, SE, C-statistic and SMDs differ by at most 1.4e-14, which is
floating-point rounding (max 2.2e-16 on log HR). This passes the ≤ 1e-12 gate of deviation 1. The all-initiator
columns below come from this verified run.

## Summary

1. **Index setting.** Under the S4 rule, 19–61% of analysed initiators in outpatient-RCT drug trials started during
   an inpatient stay (median 34%). The range is 44–64% in the procedure-arm trials and 73–99% in the
   hospital-initiated trials. The flags are identical to S4's; S4 reported percentages over the whole cohort, while
   the percentages here are over the ECG-analysed initiators, who are more often inpatients. ED-day initiation
   (not inpatient) is 0–11%. Inpatient initiation is often very different between arms (median absolute arm
   difference 14 points; > 10 points in 23/38 trials, e.g. SUSTAIN-6 4% vs 32%). The restriction therefore changes
   the case mix differently in each arm.
2. **Balance (OUT-29, outpatient only).** ECG still improves held-out balance, but by less. With P1, % |SMD| < 0.1
   goes from 51.7 to 54.0 (+2.3 pp, 17/29, p = 0.035; vs permuted ECG p = 0.023; clustered p = 0.008). With all
   initiators on the same trials the gain is +5.7 pp (22/29, p = 0.0008). The outpatient gain is not stable across
   halves (A 0.34, B 0.28), and the leave-one-out max p is 0.068. With P5 the gain is +3.2 pp (p = 0.027; vs
   permuted p = 0.047; clustered 0.13), against +3.0 pp (p = 0.023) with all initiators. On the covars2b panel, P1
   gains +1.7 pp (p = 0.028), against +4.5 pp (p < 1e-6) with all initiators; P5 shows no gain (p = 0.36).
   The domain pattern also changes. With all initiators, ECG gains fall in LV function, diastolic/LA and the coded
   record. With outpatients only, the only nominal gain is in vitals and core labs (P1, p = 0.007).
3. **Emulation (OUT-29).** With outpatients only, ECG no longer moves HRs toward the RCT. P1 |Δlog HR| goes from
   0.213 to 0.196 (14/29 trials closer, p = 0.24; vs permuted p = 0.29; benchmark shuffle p = 0.85). P5 goes from
   0.195 to 0.194 (p = 0.49; shuffle 0.41). With all initiators on the same trials, the change was 0.241 → 0.192
   (19/29, p = 0.008) for P1 and 0.220 → 0.179 (p = 0.007) for P5, and it already failed the within-set benchmark
   shuffle (p = 0.22 and 0.14). The outpatient result therefore removes the generic shrinkage without revealing a
   trial-specific gain. Consistency is unchanged by ECG (P1 79% → 79%; P5 83% → 86%).
4. **Effect of the restriction itself.** Without ECG, restricting to outpatients moves the thin-PS HRs slightly
   closer to the RCTs (P1 base |Δ| 0.241 → 0.213, 15/29, p = 0.20; P5 0.220 → 0.195, p = 0.34). Neither change is
   significant. Consistency rises from 52% to 79% (P1, p = 0.008), mostly because the SEs are wider.
   Balance on the 58-variable panel gets slightly worse (P1 base −2.1 pp, ns; P5 base −4.3 pp, p = 0.024; P1 +ECG
   −5.4 pp, p = 0.017). The covars2b panel gets better (P1 base +5.2 pp, p = 0.041). Part of the ECG balance
   advantage with all initiators therefore comes from the care-setting mix: ECG captures inpatient-vs-outpatient
   physiology.
5. **Secondary sets.** OUT-32 (with CABANA and RAFT-AF; PROTECT AF is not analysable) gives the same answer:
   balance P1 +2.3 pp, p = 0.037; |Δ| p = 0.26. In the setting-matched Mixed-38 (OUT-32 outpatient-only plus
   HOSP-6 all initiators; 37 analysable), balance with P1 goes from 50.9 to 53.8 (p = 0.018; vs permuted
   p = 0.003), and |Δ| goes from 0.216 to 0.197 (p = 0.17; shuffle p = 0.60). With all initiators on the same
   37 trials, balance p is 0.0004 and |Δ| p is 0.002 (shuffle p = 0.08).
   **HOSP-6 (all initiators, = primary):** balance P1 +5.7 pp, 4/6, p = 0.19; |Δ| 0.204 → 0.161, 4/6, p = 0.19
   (shuffle p = 0.033, 6 trials). Inpatient-only: |Δ| p = 0.42 (P1) and 0.078 (P5). Six trials cannot support
   inference.
6. **Cohort and power (PI question).** In OUT-29 the restriction keeps a median of 66.5% of initiators (IQR
   48.7–71.5), 60.0% of the smaller arm, 63.8% of P1 matched pairs and 52.3% of cohort events. The SE of log HR
   rises by a median factor of 1.37 (IQR 1.24–1.68) for P1 base, 1.43 for P1 +ECG and 1.36 for P5 base. This is
   equivalent to losing about 47% of the effective sample (1/1.37² = 0.53). The largest inflations are in the
   AF / rhythm-control and HF trials, where outpatient initiation of the treatment arm is rare: AF-CHF 2.99,
   AFFIRM 2.52, EAST-AFNET 4 2.32, ARISTOTLE 2.06, COMET 1.78. **Feasibility after restriction** (≥ 300 with
   ECG in the smaller arm and ≥ 50 events): 27/29 OUT-29 trials still pass. INSIGHT and AF-CHF fail, although
   all 29 were feasible with all initiators. In OUT-32, 29/32 pass (PROTECT AF also fails, 5% of its smaller arm
   retained). If the hospital trials were restricted to outpatients (supplementary; not setting-appropriate), only
   2/6 would pass and a median of 20% of initiators would remain.

**Verdict (plan's rule).** For OUT-29 the conclusion changes on emulation: ECG vs base on |Δlog HR| goes from
p = 0.008 (P1) and 0.007 (P5) with all initiators to 0.24 and 0.49. The earlier emulation gain was already
non-specific (benchmark shuffle p = 0.14–0.22) and is not present in outpatient initiators. The balance conclusion
holds in direction and nominal significance (p = 0.035 P1, 0.027 P5, both beating permuted ECG), but the P1 gain is
about 40% of its all-initiator size and is unstable across halves. Outpatient restriction costs about 37% in SE
(median) and makes 2 of 29 outpatient-RCT trials infeasible.


## T1. Index setting (% of analysed initiators; inpatient = index date within a 9201 stay; ED = within a 9203 visit, not inpatient)

| Trial | RCT setting | % inpatient | arm 1 | arm 0 | % ED | ED arm 1 | ED arm 0 |
|---|---|---|---|---|---|---|---|
| comet | outpatient | 61.0 | 68.7 | 55.7 | 0.4 | 0.6 | – |
| paradigm-hf-seq | outpatient | 38.0 | 42.2 | 36.7 | 0.7 | – | 0.8 |
| transform-hf | hospital | 75.5 | 46.6 | 76.9 | 1.8 | – | 1.8 |
| elite-ii | outpatient | 57.4 | 53.4 | 60.7 | 1.8 | 1.8 | 1.8 |
| life | outpatient | 32.1 | 17.9 | 41.3 | 6.6 | 5.7 | 7.1 |
| plato | hospital | 86.4 | 90.3 | 80.8 | 0.4 | 0.3 | 0.5 |
| aristotle | outpatient | 51.3 | 48.8 | 62.5 | 4.0 | 4.4 | 2.4 |
| rocket-af | outpatient | 48.5 | 36.2 | 61.6 | 3.7 | 5.0 | 2.3 |
| rely | outpatient | 57.9 | 40.0 | 61.6 | 2.6 | 4.1 | 2.3 |
| allhat | outpatient | 32.4 | 35.3 | 26.3 | 5.3 | 4.9 | 6.2 |
| emperor-preserved-v2 | outpatient | 42.5 | 40.6 | 45.6 | 0.5 | – | – |
| east-afnet4 | outpatient | 55.7 | 78.2 | 49.6 | 1.3 | 0.8 | 1.4 |
| cabana-v2 | outpatient (procedure arm) | 64.0 | 24.3 | 69.4 | 1.1 | 0.0 | 1.3 |
| ontarget | outpatient | 33.5 | 26.4 | 40.1 | 4.0 | 3.8 | 4.2 |
| value | outpatient | 26.3 | 15.8 | 32.8 | 6.0 | 6.3 | 5.9 |
| ascot | outpatient | 31.9 | 27.9 | 36.1 | 7.7 | 7.9 | 7.4 |
| empa-reg | outpatient | 27.0 | 26.0 | 28.3 | 1.6 | 1.3 | 1.9 |
| carolina | outpatient | 23.1 | 28.2 | 17.2 | 5.9 | 5.1 | 6.9 |
| leader | outpatient | 28.5 | 11.5 | 30.8 | 1.9 | – | 1.9 |
| sustain6 | outpatient | 19.2 | 3.6 | 32.3 | 0.6 | – | 0.9 |
| rewind | outpatient | 22.6 | 6.5 | 27.1 | 3.3 | 1.0 | 3.9 |
| declare | outpatient | 30.0 | 43.6 | 24.0 | 3.9 | 1.6 | 4.9 |
| canvas | outpatient | 24.5 | 7.6 | 25.9 | 4.8 | 4.1 | 4.8 |
| tecos | outpatient | 29.8 | 27.0 | 32.8 | 2.6 | 2.5 | 2.8 |
| carmelina | outpatient | 46.8 | 50.3 | 42.9 | 1.7 | – | 2.6 |
| valiant | hospital | 76.3 | 74.0 | 77.4 | 1.3 | – | 1.3 |
| insight | outpatient | 22.8 | 34.8 | 22.3 | 4.2 | 5.5 | 4.2 |
| affirm | outpatient | 47.9 | 74.9 | 39.7 | 1.1 | 0.8 | 1.2 |
| af-chf | outpatient | 57.6 | 82.9 | 50.1 | 0.9 | – | 1.0 |
| precision | outpatient | 29.5 | 43.3 | 17.8 | 10.9 | 1.9 | 18.5 |
| amplify | hospital | 72.7 | 70.7 | 80.7 | 4.5 | 4.9 | 3.0 |
| lodestar | outpatient | 53.5 | 53.5 | 53.4 | 1.2 | 0.9 | 1.5 |
| prove-it | hospital | 83.7 | 84.2 | 80.0 | 0.7 | 0.6 | – |
| frail-af | outpatient | 41.5 | 36.5 | 42.9 | 0.9 | – | 0.9 |
| laaos3 | hospital | 98.9 | – | 98.8 | 0.0 | 0.0 | 0.0 |
| protect-af | outpatient (procedure arm) | 60.5 | 94.6 | 51.0 | – | 0.0 | – |
| raft-af | outpatient (procedure arm) | 43.7 | 32.4 | 46.5 | 1.0 | 0.0 | 1.3 |
| active-w | outpatient | 57.9 | 54.0 | 60.0 | 2.2 | 1.8 | 2.5 |

## T2. Cohort and power after outpatient restriction (outpatient / all initiators)

| Trial | RCT setting | % retained | % smaller arm | % pairs P1 base | % pairs P1 ECG | % pairs P5 base | % events (cohort) | % events (P1 matched) | SE ratio P1 base | SE ratio P1 ECG | SE ratio P5 base | feasible all | feasible outpt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| comet | outpatient | 39.0 | 31.3 | 31.3 | 32.6 | 32.8 | 36.8 | 30.4 | 1.779 | 1.752 | 1.700 | yes | yes |
| paradigm-hf-seq | outpatient | 62.0 | 57.8 | 57.8 | 57.8 | 57.8 | 52.3 | 49.5 | 1.447 | 1.432 | 1.366 | yes | yes |
| transform-hf | hospital | 24.5 | 53.4 | 53.4 | 53.2 | 53.4 | 14.2 | 38.3 | 1.712 | 1.622 | 1.512 | yes | yes |
| elite-ii | outpatient | 42.6 | 46.6 | 52.1 | 48.0 | 50.3 | 25.5 | 34.1 | 1.681 | 1.842 | 1.836 | yes | yes |
| life | outpatient | 67.9 | 82.1 | 82.0 | 76.8 | 79.7 | 50.9 | 59.7 | 1.258 | 1.307 | 1.265 | yes | yes |
| plato | hospital | 13.6 | 14.2 | 15.1 | 14.3 | 15.2 | 6.1 | 6.2 | 3.994 | 3.909 | 4.128 | yes | yes |
| aristotle | outpatient | 48.7 | 37.5 | 30.8 | 32.6 | 31.7 | 32.7 | 24.5 | 2.059 | 2.044 | 1.845 | yes | yes |
| rocket-af | outpatient | 51.5 | 38.4 | 38.0 | 39.0 | 41.4 | 36.0 | 31.1 | 1.779 | 1.660 | 1.804 | yes | yes |
| rely | outpatient | 42.1 | 60.0 | 60.0 | 60.0 | 60.0 | 34.0 | 51.3 | 1.329 | 1.257 | 1.414 | yes | yes |
| allhat | outpatient | 67.6 | 73.7 | 73.7 | 73.7 | 73.7 | 57.5 | 63.7 | 1.241 | 1.236 | 1.250 | yes | yes |
| emperor-preserved-v2 | outpatient | 57.5 | 54.4 | 62.1 | 61.4 | 63.1 | 47.5 | 54.6 | 1.429 | 1.467 | 1.434 | yes | yes |
| east-afnet4 | outpatient | 44.3 | 21.8 | 21.8 | 21.8 | 21.8 | 36.8 | 17.4 | 2.320 | 2.331 | 2.368 | yes | yes |
| cabana-v2 | outpatient (procedure arm) | 36.0 | 75.7 | 75.7 | 75.3 | 75.7 | 18.9 | 41.8 | 1.336 | 1.353 | 1.349 | yes | yes |
| ontarget | outpatient | 66.5 | 65.3 | 68.3 | 65.2 | 66.2 | 53.7 | 58.0 | 1.306 | 1.355 | 1.341 | yes | yes |
| value | outpatient | 73.7 | 84.2 | 84.2 | 84.3 | 84.0 | 58.4 | 68.6 | 1.231 | 1.185 | 1.187 | yes | yes |
| ascot | outpatient | 68.1 | 63.9 | 63.8 | 68.1 | 66.7 | 53.0 | 51.2 | 1.401 | 1.373 | 1.405 | yes | yes |
| empa-reg | outpatient | 73.0 | 71.7 | 78.7 | 77.3 | 78.7 | 62.5 | 68.2 | 1.220 | 1.173 | 1.177 | yes | yes |
| carolina | outpatient | 76.9 | 82.8 | 81.9 | 79.3 | 81.7 | 67.6 | 69.9 | 1.242 | 1.177 | 1.159 | yes | yes |
| leader | outpatient | 71.5 | 88.5 | 88.5 | 88.7 | 88.5 | 63.5 | 77.6 | 1.086 | 1.073 | 1.136 | yes | yes |
| sustain6 | outpatient | 80.8 | 80.7 | 78.0 | 80.0 | 79.4 | 67.1 | 71.2 | 1.178 | 1.085 | 1.206 | yes | yes |
| rewind | outpatient | 77.4 | 93.5 | 93.2 | 90.7 | 93.4 | 68.5 | 88.9 | 1.039 | 1.071 | 1.061 | yes | yes |
| declare | outpatient | 70.0 | 56.4 | 71.2 | 71.2 | 71.7 | 55.7 | 57.4 | 1.273 | 1.322 | 1.277 | yes | yes |
| canvas | outpatient | 75.5 | 92.4 | 92.4 | 92.4 | 92.4 | 65.2 | 85.5 | 1.077 | 1.089 | 1.019 | yes | yes |
| tecos | outpatient | 70.2 | 67.2 | 67.6 | 66.1 | 67.2 | 61.0 | 58.4 | 1.311 | 1.320 | 1.263 | yes | yes |
| carmelina | outpatient | 53.2 | 53.7 | 57.7 | 56.7 | 58.6 | 47.0 | 51.3 | 1.396 | 1.449 | 1.364 | yes | yes |
| valiant | hospital | 23.7 | 26.0 | 26.6 | 23.8 | 26.5 | 14.2 | 15.8 | 2.589 | 3.008 | 2.696 | yes | no |
| insight | outpatient | 77.2 | 65.2 | 65.2 | 65.0 | 65.2 | 62.4 | 49.0 | 1.430 | 1.550 | 1.309 | yes | no |
| affirm | outpatient | 52.1 | 25.1 | 25.1 | 25.1 | 25.1 | 37.0 | 15.6 | 2.524 | 2.519 | 2.401 | yes | yes |
| af-chf | outpatient | 42.4 | 17.1 | 17.2 | 17.1 | 17.2 | 29.3 | 11.6 | 2.989 | 2.854 | 2.849 | yes | no |
| precision | outpatient | 70.5 | 56.7 | 56.7 | 56.0 | 57.7 | 61.3 | 47.6 | 1.447 | 1.429 | 1.410 | yes | yes |
| amplify | hospital | 27.3 | 19.3 | 21.1 | 20.2 | 20.9 | 20.8 | 19.9 | 2.170 | 2.442 | 2.544 | yes | no |
| lodestar | outpatient | 46.5 | 46.5 | 78.4 | 74.5 | 76.7 | 28.8 | 52.0 | 1.372 | 1.448 | 1.443 | yes | yes |
| prove-it | hospital | 16.3 | 20.0 | 20.0 | 19.7 | 19.8 | 7.9 | 7.6 | 3.413 | 3.067 | 4.012 | yes | no |
| frail-af | outpatient | 58.5 | 63.5 | 63.5 | 63.6 | 63.4 | 44.2 | 48.7 | 1.351 | 1.443 | 1.348 | yes | yes |
| laaos3 | hospital | 1.1 | – | – | – | – | – | – | – | – | – | yes | no |
| protect-af | outpatient (procedure arm) | 39.5 | 5.4 | – | – | – | 33.0 | – | – | – | – | yes | no |
| raft-af | outpatient (procedure arm) | 56.3 | 67.6 | 67.6 | 67.6 | 66.9 | 48.2 | 58.0 | 1.322 | 1.186 | 1.295 | yes | yes |
| active-w | outpatient | 42.1 | 46.0 | 43.7 | 43.3 | 40.6 | 32.1 | 31.9 | 1.874 | 1.762 | 1.722 | yes | yes |

**OUT-29** median (IQR): retained 66.5% (48.7–71.5); smaller arm 60.0%; P1 pairs 63.8%; cohort events 52.3%; SE ratio P1 base 1.372 (1.242–1.681), P1 ECG 1.429, P5 base 1.364. Feasible: all initiators 29/29, outpatient 27/29; analysable (≥ 100 per arm) 29/29.

**OUT-32** median (IQR): retained 60.2% (46.0–70.7); smaller arm 61.7%; P1 pairs 65.2%; cohort events 49.6%; SE ratio P1 base 1.351 (1.250–1.564), P1 ECG 1.373, P5 base 1.349. Feasible: all initiators 32/32, outpatient 29/32; analysable (≥ 100 per arm) 31/32.

**HOSP-6** median (IQR): retained 20.0% (14.3–24.3); smaller arm 20.0%; P1 pairs 21.1%; cohort events 14.2%; SE ratio P1 base 2.589 (2.170–3.413), P1 ECG 3.008, P5 base 2.696. Feasible: all initiators 6/6, outpatient 2/6; analysable (≥ 100 per arm) 5/6.

## T3. ECG vs base across trials (one-sided exact sign-flip; bshuf = within-set benchmark shuffle)

| Set | PS | metric | n | base | +ECG | +perm ECG | k better | p | p vs perm | cluster p | p A | p B | LOO max p | bshuf p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OUT-29 outpt | P1 | lt01 | 29 | 51.658 | 53.991 | 51.404 | 17/29 | 0.035 | 0.023 | 0.008 | 0.341 | 0.276 | 0.068 | – |
| OUT-29 outpt | P1 | x_lt01 | 29 | 71.850 | 73.587 | 71.550 | 16/29 | 0.028 | 6.4e-04 | 0.033 | 0.006 | 0.163 | 0.055 | – |
| OUT-29 outpt | P1 | absd | 29 | 0.213 | 0.196 | 0.210 | 14/29 | 0.241 | 0.291 | 0.232 | 0.623 | 0.018 | 0.420 | 0.846 |
| OUT-29 outpt | P1 | cons | 29 | 79.310 | 79.310 | 75.862 | 2/29 | 0.688 | 0.500 | 0.500 | 1.000 | 0.875 | 0.875 | – |
| OUT-29 outpt | P5 | lt01 | 29 | 53.926 | 57.093 | 54.106 | 17/29 | 0.027 | 0.047 | 0.127 | 0.508 | 0.042 | 0.050 | – |
| OUT-29 outpt | P5 | x_lt01 | 29 | 75.993 | 76.323 | 74.835 | 12/29 | 0.363 | 0.052 | 0.231 | 0.194 | 0.391 | 0.527 | – |
| OUT-29 outpt | P5 | absd | 29 | 0.195 | 0.194 | 0.202 | 16/29 | 0.490 | 0.366 | 0.360 | 0.177 | 0.711 | 0.701 | 0.405 |
| OUT-29 outpt | P5 | cons | 29 | 82.759 | 86.207 | 75.862 | 3/29 | 0.500 | 0.125 | 0.500 | 0.250 | 0.500 | 0.688 | – |
| OUT-29 all (same trials) | P1 | lt01 | 29 | 53.722 | 59.437 | 54.234 | 22/29 | 7.5e-04 | 9.1e-04 | 0.004 | 0.001 | 2.5e-04 | 0.002 | – |
| OUT-29 all (same trials) | P1 | x_lt01 | 29 | 66.643 | 71.100 | 66.521 | 24/29 | 8.9e-07 | 2.8e-06 | 9.8e-04 | 5.8e-05 | 0.002 | 1.8e-06 | – |
| OUT-29 all (same trials) | P1 | absd | 29 | 0.241 | 0.192 | 0.266 | 19/29 | 0.008 | 0.002 | 0.088 | 0.347 | 0.102 | 0.017 | 0.223 |
| OUT-29 all (same trials) | P1 | cons | 29 | 51.724 | 72.414 | 51.724 | 7/29 | 0.035 | 0.035 | 0.062 | 0.500 | 0.031 | 0.062 | – |
| OUT-29 all (same trials) | P5 | lt01 | 29 | 58.246 | 61.283 | 58.247 | 17/29 | 0.023 | 0.011 | 0.062 | 0.420 | 0.035 | 0.042 | – |
| OUT-29 all (same trials) | P5 | x_lt01 | 29 | 72.752 | 75.729 | 73.637 | 25/29 | 2.7e-05 | 0.009 | 0.002 | 0.003 | 0.010 | 5.3e-05 | – |
| OUT-29 all (same trials) | P5 | absd | 29 | 0.220 | 0.179 | 0.214 | 19/29 | 0.007 | 0.028 | 0.005 | 0.522 | 0.887 | 0.015 | 0.142 |
| OUT-29 all (same trials) | P5 | cons | 29 | 65.517 | 68.966 | 68.966 | 2/29 | 0.500 | 0.688 | 0.250 | 0.875 | 0.891 | 0.750 | – |
| OUT-29 all (full set) | P1 | lt01 | 29 | 53.722 | 59.437 | 54.234 | 22/29 | 7.5e-04 | 9.1e-04 | 0.004 | 0.001 | 2.5e-04 | 0.002 | – |
| OUT-29 all (full set) | P1 | x_lt01 | 29 | 66.643 | 71.100 | 66.521 | 24/29 | 8.9e-07 | 2.8e-06 | 9.8e-04 | 5.8e-05 | 0.002 | 1.8e-06 | – |
| OUT-29 all (full set) | P1 | absd | 29 | 0.241 | 0.192 | 0.266 | 19/29 | 0.008 | 0.002 | 0.088 | 0.347 | 0.102 | 0.017 | 0.223 |
| OUT-29 all (full set) | P1 | cons | 29 | 51.724 | 72.414 | 51.724 | 7/29 | 0.035 | 0.035 | 0.062 | 0.500 | 0.031 | 0.062 | – |
| OUT-29 all (full set) | P5 | lt01 | 29 | 58.246 | 61.283 | 58.247 | 17/29 | 0.023 | 0.011 | 0.062 | 0.420 | 0.035 | 0.042 | – |
| OUT-29 all (full set) | P5 | x_lt01 | 29 | 72.752 | 75.729 | 73.637 | 25/29 | 2.7e-05 | 0.009 | 0.002 | 0.003 | 0.010 | 5.3e-05 | – |
| OUT-29 all (full set) | P5 | absd | 29 | 0.220 | 0.179 | 0.214 | 19/29 | 0.007 | 0.028 | 0.005 | 0.522 | 0.887 | 0.015 | 0.142 |
| OUT-29 all (full set) | P5 | cons | 29 | 65.517 | 68.966 | 68.966 | 2/29 | 0.500 | 0.688 | 0.250 | 0.875 | 0.891 | 0.750 | – |
| OUT-32 outpt | P1 | lt01 | 31 | 51.051 | 53.399 | 50.646 | 18/31 | 0.037 | 0.016 | 0.008 | 0.184 | 0.179 | 0.070 | – |
| OUT-32 outpt | P1 | x_lt01 | 31 | 70.719 | 72.439 | 70.245 | 18/31 | 0.021 | 1.8e-04 | 0.016 | 0.003 | 0.091 | 0.042 | – |
| OUT-32 outpt | P1 | absd | 31 | 0.219 | 0.204 | 0.219 | 15/31 | 0.258 | 0.268 | 0.262 | 0.522 | 0.010 | 0.445 | 0.860 |
| OUT-32 outpt | P1 | cons | 31 | 77.419 | 77.419 | 74.194 | 2/31 | 0.688 | 0.500 | 0.500 | 1.000 | 0.688 | 0.875 | – |
| OUT-32 outpt | P5 | lt01 | 31 | 53.339 | 56.579 | 53.397 | 19/31 | 0.018 | 0.029 | 0.124 | 0.585 | 0.019 | 0.034 | – |
| OUT-32 outpt | P5 | x_lt01 | 31 | 74.825 | 74.913 | 73.626 | 12/31 | 0.461 | 0.072 | 0.243 | 0.284 | 0.429 | 0.631 | – |
| OUT-32 outpt | P5 | absd | 31 | 0.197 | 0.200 | 0.207 | 16/31 | 0.571 | 0.384 | 0.414 | 0.197 | 0.753 | 0.775 | 0.409 |
| OUT-32 outpt | P5 | cons | 31 | 80.645 | 83.871 | 74.194 | 3/31 | 0.500 | 0.125 | 0.500 | 0.250 | 0.500 | 0.688 | – |
| OUT-32 all (same trials) | P1 | lt01 | 31 | 52.480 | 57.939 | 53.015 | 23/31 | 6.7e-04 | 9.8e-04 | 0.004 | 6.2e-04 | 6.5e-04 | 0.001 | – |
| OUT-32 all (same trials) | P1 | x_lt01 | 31 | 63.985 | 68.396 | 63.804 | 26/31 | 4.1e-07 | 1.1e-06 | 9.8e-04 | 1.9e-05 | 8.6e-04 | 8.2e-07 | – |
| OUT-32 all (same trials) | P1 | absd | 31 | 0.272 | 0.217 | 0.299 | 21/31 | 0.003 | 7.2e-04 | 0.086 | 0.234 | 0.071 | 0.007 | 0.223 |
| OUT-32 all (same trials) | P1 | cons | 31 | 51.613 | 70.968 | 51.613 | 7/31 | 0.035 | 0.035 | 0.062 | 0.500 | 0.031 | 0.062 | – |
| OUT-32 all (same trials) | P5 | lt01 | 31 | 57.269 | 60.555 | 57.381 | 19/31 | 0.011 | 0.006 | 0.062 | 0.515 | 0.035 | 0.022 | – |
| OUT-32 all (same trials) | P5 | x_lt01 | 31 | 70.212 | 73.056 | 71.002 | 26/31 | 2.7e-05 | 0.007 | 0.002 | 0.001 | 0.005 | 5.4e-05 | – |
| OUT-32 all (same trials) | P5 | absd | 31 | 0.244 | 0.199 | 0.239 | 20/31 | 0.005 | 0.020 | 0.005 | 0.338 | 0.719 | 0.011 | 0.152 |
| OUT-32 all (same trials) | P5 | cons | 31 | 64.516 | 67.742 | 67.742 | 2/31 | 0.500 | 0.688 | 0.250 | 0.875 | 0.891 | 0.750 | – |
| OUT-32 all (full set) | P1 | lt01 | 32 | 51.541 | 57.367 | 52.705 | 24/32 | 3.4e-04 | 0.001 | 0.004 | 4.9e-04 | 3.4e-04 | 6.9e-04 | – |
| OUT-32 all (full set) | P1 | x_lt01 | 32 | 63.671 | 67.840 | 63.420 | 26/32 | 1.6e-06 | 1.5e-06 | 9.8e-04 | 1.1e-05 | 7.2e-04 | 3.2e-06 | – |
| OUT-32 all (full set) | P1 | absd | 32 | 0.268 | 0.215 | 0.293 | 21/32 | 0.004 | 9.9e-04 | 0.095 | 0.148 | 0.060 | 0.008 | 0.485 |
| OUT-32 all (full set) | P1 | cons | 32 | 53.125 | 71.875 | 53.125 | 7/32 | 0.035 | 0.035 | 0.062 | 0.500 | 0.031 | 0.062 | – |
| OUT-32 all (full set) | P5 | lt01 | 32 | 56.611 | 60.171 | 56.828 | 20/32 | 0.007 | 0.004 | 0.053 | 0.642 | 0.049 | 0.013 | – |
| OUT-32 all (full set) | P5 | x_lt01 | 32 | 69.712 | 72.401 | 70.553 | 26/32 | 5.3e-05 | 0.013 | 0.003 | 8.9e-04 | 0.005 | 1.1e-04 | – |
| OUT-32 all (full set) | P5 | absd | 32 | 0.237 | 0.196 | 0.235 | 20/32 | 0.009 | 0.019 | 0.005 | 0.353 | 0.750 | 0.018 | 0.295 |
| OUT-32 all (full set) | P5 | cons | 32 | 65.625 | 68.750 | 68.750 | 2/32 | 0.500 | 0.688 | 0.250 | 0.875 | 0.891 | 0.750 | – |
| HOSP-6 all | P1 | lt01 | 6 | 50.413 | 56.161 | 49.254 | 4/6 | 0.188 | 0.062 | 0.188 | 0.109 | 0.016 | 0.375 | – |
| HOSP-6 all | P1 | x_lt01 | 6 | 63.291 | 67.634 | 64.729 | 4/6 | 0.062 | 0.125 | 0.062 | 0.094 | 0.172 | 0.125 | – |
| HOSP-6 all | P1 | absd | 6 | 0.204 | 0.161 | 0.243 | 4/6 | 0.188 | 0.094 | 0.188 | 0.609 | 0.078 | 0.375 | 0.033 |
| HOSP-6 all | P1 | cons | 6 | 83.333 | 100.000 | 83.333 | 1/6 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | – |
| HOSP-6 all | P5 | lt01 | 6 | 50.287 | 55.747 | 53.448 | 5/6 | 0.031 | 0.375 | 0.031 | 0.453 | 0.188 | 0.062 | – |
| HOSP-6 all | P5 | x_lt01 | 6 | 69.251 | 71.552 | 70.831 | 4/6 | 0.156 | 0.375 | 0.156 | 0.656 | 0.234 | 0.312 | – |
| HOSP-6 all | P5 | absd | 6 | 0.153 | 0.187 | 0.163 | 3/6 | 0.859 | 0.703 | 0.859 | 0.094 | 0.188 | 0.906 | 1.000 |
| HOSP-6 all | P5 | cons | 6 | 83.333 | 83.333 | 83.333 | 0/6 | 1.000 | 1.000 | 1.000 | 0.250 | 0.500 | 1.000 | – |
| HOSP inpt | P1 | lt01 | 6 | 47.414 | 50.403 | 47.525 | 4/6 | 0.234 | 0.219 | 0.234 | 0.125 | 0.109 | 0.438 | – |
| HOSP inpt | P1 | x_lt01 | 6 | 61.176 | 64.368 | 60.375 | 5/6 | 0.094 | 0.141 | 0.094 | 0.047 | 0.125 | 0.188 | – |
| HOSP inpt | P1 | absd | 6 | 0.186 | 0.173 | 0.123 | 4/6 | 0.422 | 0.766 | 0.422 | 0.625 | 0.500 | 0.625 | 0.066 |
| HOSP inpt | P1 | cons | 6 | 100.000 | 83.333 | 100.000 | 0/6 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | – |
| HOSP inpt | P5 | lt01 | 6 | 48.730 | 51.437 | 53.428 | 4/6 | 0.156 | 0.766 | 0.156 | 0.375 | 0.328 | 0.312 | – |
| HOSP inpt | P5 | x_lt01 | 6 | 69.427 | 68.379 | 67.751 | 2/6 | 0.734 | 0.312 | 0.734 | 0.062 | 0.078 | 0.969 | – |
| HOSP inpt | P5 | absd | 6 | 0.145 | 0.100 | 0.185 | 4/6 | 0.078 | 0.062 | 0.078 | 0.250 | 0.453 | 0.156 | 0.066 |
| HOSP inpt | P5 | cons | 6 | 83.333 | 100.000 | 100.000 | 1/6 | 0.500 | 1.000 | 0.500 | 0.500 | 1.000 | 1.000 | – |
| HOSP inpt: all (same trials) | P1 | lt01 | 6 | 50.413 | 56.161 | 49.254 | 4/6 | 0.188 | 0.062 | 0.188 | 0.109 | 0.016 | 0.375 | – |
| HOSP inpt: all (same trials) | P1 | x_lt01 | 6 | 63.291 | 67.634 | 64.729 | 4/6 | 0.062 | 0.125 | 0.062 | 0.094 | 0.172 | 0.125 | – |
| HOSP inpt: all (same trials) | P1 | absd | 6 | 0.204 | 0.161 | 0.243 | 4/6 | 0.188 | 0.094 | 0.188 | 0.609 | 0.078 | 0.375 | 0.033 |
| HOSP inpt: all (same trials) | P1 | cons | 6 | 83.333 | 100.000 | 83.333 | 1/6 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | – |
| HOSP inpt: all (same trials) | P5 | lt01 | 6 | 50.287 | 55.747 | 53.448 | 5/6 | 0.031 | 0.375 | 0.031 | 0.453 | 0.188 | 0.062 | – |
| HOSP inpt: all (same trials) | P5 | x_lt01 | 6 | 69.251 | 71.552 | 70.831 | 4/6 | 0.156 | 0.375 | 0.156 | 0.656 | 0.234 | 0.312 | – |
| HOSP inpt: all (same trials) | P5 | absd | 6 | 0.153 | 0.187 | 0.163 | 3/6 | 0.859 | 0.703 | 0.859 | 0.094 | 0.188 | 0.906 | 1.000 |
| HOSP inpt: all (same trials) | P5 | cons | 6 | 83.333 | 83.333 | 83.333 | 0/6 | 1.000 | 1.000 | 1.000 | 0.250 | 0.500 | 1.000 | – |
| HOSP outpt (suppl.) | P1 | lt01 | 5 | 34.487 | 32.067 | 33.840 | 2/5 | 0.812 | 0.750 | 0.812 | 0.375 | 0.188 | 0.938 | – |
| HOSP outpt (suppl.) | P1 | x_lt01 | 5 | 52.998 | 51.910 | 53.434 | 2/5 | 0.594 | 0.688 | 0.594 | 0.312 | 0.469 | 0.875 | – |
| HOSP outpt (suppl.) | P1 | absd | 5 | 0.401 | 0.329 | 0.439 | 3/5 | 0.344 | 0.156 | 0.344 | 0.094 | 0.281 | 0.688 | 0.302 |
| HOSP outpt (suppl.) | P1 | cons | 5 | 100.000 | 80.000 | 60.000 | 0/5 | 1.000 | 0.500 | 1.000 | 0.500 | 1.000 | 1.000 | – |
| HOSP outpt (suppl.) | P5 | lt01 | 5 | 35.207 | 32.847 | 38.444 | 2/5 | 0.750 | 0.875 | 0.750 | 0.812 | 0.062 | 0.875 | – |
| HOSP outpt (suppl.) | P5 | x_lt01 | 5 | 56.130 | 56.840 | 58.615 | 3/5 | 0.312 | 0.781 | 0.312 | 0.375 | 0.875 | 0.625 | – |
| HOSP outpt (suppl.) | P5 | absd | 5 | 0.450 | 0.319 | 0.251 | 4/5 | 0.094 | 0.844 | 0.094 | 0.688 | 0.375 | 0.188 | 0.404 |
| HOSP outpt (suppl.) | P5 | cons | 5 | 60.000 | 100.000 | 100.000 | 2/5 | 0.250 | 1.000 | 0.250 | 1.000 | 1.000 | 0.500 | – |
| HOSP outpt: all (same trials) | P1 | lt01 | 5 | 48.427 | 58.427 | 48.760 | 4/5 | 0.062 | 0.031 | 0.062 | 0.219 | 0.031 | 0.125 | – |
| HOSP outpt: all (same trials) | P1 | x_lt01 | 5 | 62.534 | 68.783 | 64.626 | 4/5 | 0.062 | 0.125 | 0.062 | 0.125 | 0.344 | 0.125 | – |
| HOSP outpt: all (same trials) | P1 | absd | 5 | 0.178 | 0.165 | 0.198 | 3/5 | 0.375 | 0.188 | 0.375 | 0.656 | 0.156 | 0.625 | 0.199 |
| HOSP outpt: all (same trials) | P1 | cons | 5 | 80.000 | 100.000 | 80.000 | 1/5 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | – |
| HOSP outpt: all (same trials) | P5 | lt01 | 5 | 52.414 | 58.276 | 54.483 | 4/5 | 0.062 | 0.250 | 0.062 | 0.344 | 0.250 | 0.125 | – |
| HOSP outpt: all (same trials) | P5 | x_lt01 | 5 | 73.040 | 74.399 | 74.692 | 3/5 | 0.312 | 0.625 | 0.312 | 0.906 | 0.031 | 0.625 | – |
| HOSP outpt: all (same trials) | P5 | absd | 5 | 0.174 | 0.188 | 0.154 | 3/5 | 0.719 | 0.750 | 0.719 | 0.188 | 0.375 | 0.812 | 1.000 |
| HOSP outpt: all (same trials) | P5 | cons | 5 | 80.000 | 80.000 | 80.000 | 0/5 | 1.000 | 1.000 | 1.000 | 0.250 | 0.500 | 1.000 | – |
| Mixed-38 setting-matched | P1 | lt01 | 37 | 50.947 | 53.847 | 50.420 | 22/37 | 0.018 | 0.003 | 0.043 | 0.071 | 0.043 | 0.033 | – |
| Mixed-38 setting-matched | P1 | x_lt01 | 37 | 69.514 | 71.660 | 69.351 | 22/37 | 0.005 | 1.2e-04 | 0.017 | 7.9e-04 | 0.045 | 0.009 | – |
| Mixed-38 setting-matched | P1 | absd | 37 | 0.216 | 0.197 | 0.223 | 19/37 | 0.168 | 0.126 | 0.103 | 0.540 | 0.003 | 0.297 | 0.597 |
| Mixed-38 setting-matched | P1 | cons | 37 | 78.378 | 81.081 | 75.676 | 3/37 | 0.500 | 0.363 | 0.250 | 1.000 | 0.688 | 0.688 | – |
| Mixed-38 setting-matched | P5 | lt01 | 37 | 52.844 | 56.444 | 53.405 | 24/37 | 0.004 | 0.021 | 0.031 | 0.569 | 0.008 | 0.007 | – |
| Mixed-38 setting-matched | P5 | x_lt01 | 37 | 73.921 | 74.368 | 73.172 | 16/37 | 0.290 | 0.062 | 0.070 | 0.371 | 0.318 | 0.425 | – |
| Mixed-38 setting-matched | P5 | absd | 37 | 0.190 | 0.198 | 0.200 | 19/37 | 0.691 | 0.468 | 0.740 | 0.077 | 0.546 | 0.861 | 0.742 |
| Mixed-38 setting-matched | P5 | cons | 37 | 81.081 | 83.784 | 75.676 | 3/37 | 0.500 | 0.125 | 0.500 | 0.062 | 0.344 | 0.688 | – |
| Mixed-38: all (same trials) | P1 | lt01 | 37 | 52.145 | 57.650 | 52.405 | 27/37 | 4.3e-04 | 1.6e-04 | 0.017 | 1.9e-04 | 4.9e-05 | 8.5e-04 | – |
| Mixed-38: all (same trials) | P1 | x_lt01 | 37 | 63.873 | 68.273 | 63.954 | 30/37 | 2.4e-07 | 7.5e-07 | 0.001 | 6.6e-06 | 4.2e-04 | 4.9e-07 | – |
| Mixed-38: all (same trials) | P1 | absd | 37 | 0.261 | 0.208 | 0.290 | 25/37 | 0.002 | 2.0e-04 | 0.019 | 0.265 | 0.032 | 0.003 | 0.081 |
| Mixed-38: all (same trials) | P1 | cons | 37 | 56.757 | 75.676 | 56.757 | 8/37 | 0.020 | 0.020 | 0.031 | 0.500 | 0.031 | 0.035 | – |
| Mixed-38: all (same trials) | P5 | lt01 | 37 | 56.137 | 59.775 | 56.744 | 24/37 | 0.002 | 0.004 | 0.011 | 0.494 | 0.017 | 0.004 | – |
| Mixed-38: all (same trials) | P5 | x_lt01 | 37 | 70.056 | 72.812 | 70.974 | 30/37 | 1.3e-05 | 0.007 | 6.1e-04 | 0.015 | 0.003 | 2.6e-05 | – |
| Mixed-38: all (same trials) | P5 | absd | 37 | 0.229 | 0.197 | 0.226 | 23/37 | 0.023 | 0.047 | 0.222 | 0.127 | 0.485 | 0.043 | 0.530 |
| Mixed-38: all (same trials) | P5 | cons | 37 | 67.568 | 70.270 | 70.270 | 2/37 | 0.500 | 0.688 | 0.250 | 0.500 | 0.773 | 0.750 | – |

## T4. Direct restriction effect (outpatient-only minus all initiators, same trials; two-sided exact sign-flip)

| Set | PS | arm | metric | n | all | outpt | Δ | k outpt better | p |
|---|---|---|---|---|---|---|---|---|---|
| OUT-29 | P1 | base | lt01 | 29 | 53.722 | 51.658 | -2.063 | 10/29 | 0.385 |
| OUT-29 | P1 | base | x_lt01 | 29 | 66.643 | 71.850 | +5.208 | 21/29 | 0.041 |
| OUT-29 | P1 | base | mean_smd | 29 | 0.131 | 0.140 | +0.009 | 11/29 | 0.246 |
| OUT-29 | P1 | base | absd | 29 | 0.241 | 0.213 | -0.028 | 15/29 | 0.201 |
| OUT-29 | P1 | base | cons | 29 | 51.724 | 79.310 | +27.586 | 8/29 | 0.008 |
| OUT-29 | P1 | ECG | lt01 | 29 | 59.437 | 53.991 | -5.447 | 7/29 | 0.017 |
| OUT-29 | P1 | ECG | x_lt01 | 29 | 71.100 | 73.587 | +2.487 | 19/29 | 0.300 |
| OUT-29 | P1 | ECG | mean_smd | 29 | 0.115 | 0.129 | +0.014 | 12/29 | 0.024 |
| OUT-29 | P1 | ECG | absd | 29 | 0.192 | 0.196 | +0.003 | 13/29 | 0.883 |
| OUT-29 | P1 | ECG | cons | 29 | 72.414 | 79.310 | +6.897 | 3/29 | 0.625 |
| OUT-29 | P5 | base | lt01 | 29 | 58.246 | 53.926 | -4.320 | 9/29 | 0.024 |
| OUT-29 | P5 | base | x_lt01 | 29 | 72.752 | 75.993 | +3.241 | 19/29 | 0.119 |
| OUT-29 | P5 | base | mean_smd | 29 | 0.118 | 0.130 | +0.013 | 10/29 | 0.024 |
| OUT-29 | P5 | base | absd | 29 | 0.220 | 0.195 | -0.025 | 17/29 | 0.342 |
| OUT-29 | P5 | base | cons | 29 | 65.517 | 82.759 | +17.241 | 8/29 | 0.227 |
| OUT-29 | P5 | ECG | lt01 | 29 | 61.283 | 57.093 | -4.190 | 9/29 | 0.059 |
| OUT-29 | P5 | ECG | x_lt01 | 29 | 75.729 | 76.323 | +0.593 | 14/29 | 0.769 |
| OUT-29 | P5 | ECG | mean_smd | 29 | 0.108 | 0.121 | +0.013 | 10/29 | 0.016 |
| OUT-29 | P5 | ECG | absd | 29 | 0.179 | 0.194 | +0.016 | 13/29 | 0.493 |
| OUT-29 | P5 | ECG | cons | 29 | 68.966 | 86.207 | +17.241 | 5/29 | 0.062 |
| OUT-32 | P1 | base | lt01 | 31 | 52.480 | 51.051 | -1.429 | 12/31 | 0.526 |
| OUT-32 | P1 | base | x_lt01 | 31 | 63.985 | 70.719 | +6.733 | 23/31 | 0.016 |
| OUT-32 | P1 | base | mean_smd | 31 | 0.135 | 0.141 | +0.005 | 13/31 | 0.512 |
| OUT-32 | P1 | base | absd | 31 | 0.272 | 0.219 | -0.054 | 17/31 | 0.069 |
| OUT-32 | P1 | base | cons | 31 | 51.613 | 77.419 | +25.806 | 8/31 | 0.008 |
| OUT-32 | P1 | ECG | lt01 | 31 | 57.939 | 53.399 | -4.539 | 9/31 | 0.041 |
| OUT-32 | P1 | ECG | x_lt01 | 31 | 68.396 | 72.439 | +4.043 | 21/31 | 0.130 |
| OUT-32 | P1 | ECG | mean_smd | 31 | 0.119 | 0.129 | +0.010 | 14/31 | 0.086 |
| OUT-32 | P1 | ECG | absd | 31 | 0.217 | 0.204 | -0.013 | 15/31 | 0.633 |
| OUT-32 | P1 | ECG | cons | 31 | 70.968 | 77.419 | +6.452 | 3/31 | 0.625 |
| OUT-32 | P5 | base | lt01 | 31 | 57.269 | 53.339 | -3.930 | 10/31 | 0.030 |
| OUT-32 | P5 | base | x_lt01 | 31 | 70.212 | 74.825 | +4.613 | 21/31 | 0.045 |
| OUT-32 | P5 | base | mean_smd | 31 | 0.120 | 0.131 | +0.011 | 12/31 | 0.050 |
| OUT-32 | P5 | base | absd | 31 | 0.244 | 0.197 | -0.046 | 19/31 | 0.132 |
| OUT-32 | P5 | base | cons | 31 | 64.516 | 80.645 | +16.129 | 8/31 | 0.227 |
| OUT-32 | P5 | ECG | lt01 | 31 | 60.555 | 56.579 | -3.975 | 10/31 | 0.055 |
| OUT-32 | P5 | ECG | x_lt01 | 31 | 73.056 | 74.913 | +1.857 | 16/31 | 0.397 |
| OUT-32 | P5 | ECG | mean_smd | 31 | 0.110 | 0.122 | +0.011 | 12/31 | 0.028 |
| OUT-32 | P5 | ECG | absd | 31 | 0.199 | 0.200 | +0.001 | 15/31 | 0.967 |
| OUT-32 | P5 | ECG | cons | 31 | 67.742 | 83.871 | +16.129 | 5/31 | 0.062 |

## T5. Domain balance (% of the domain's held-out variables with |SMD| < 0.1, mean over trials; p = ECG vs base)

| Set | PS | arm | Coded record | Vitals & core labs | Other labs | Echo: LV structure | Echo: LV function | Echo: diastolic / LA | Echo: RV / pulmonary | Echo: valves / aorta |
|---|---|---|---|---|---|---|---|---|---|---|
| OUT-29 outpt | P1 | base | 65.5 | 44.8 | 64.5 | 50.2 | 39.7 | 51.7 | 42.9 | 51.3 |
| OUT-29 outpt | P1 | ECG | 67.2 (p 0.383) | 52.5 (p 0.007) | 62.8 (p 0.792) | 53.7 (p 0.260) | 36.8 (p 0.783) | 53.4 (p 0.335) | 46.3 (p 0.195) | 54.0 (p 0.179) |
| OUT-29 outpt | P5 | base | 70.7 | 51.7 | 61.7 | 53.2 | 42.5 | 53.0 | 44.3 | 54.0 |
| OUT-29 outpt | P5 | ECG | 75.9 (p 0.122) | 54.4 (p 0.157) | 64.1 (p 0.269) | 58.6 (p 0.121) | 41.1 (p 0.608) | 58.6 (p 0.059) | 45.3 (p 0.449) | 57.5 (p 0.212) |
| OUT-29 all (same trials) | P1 | base | 50.9 | 53.3 | 72.8 | 54.7 | 37.1 | 48.3 | 47.8 | 50.2 |
| OUT-29 all (same trials) | P1 | ECG | 60.3 (p 0.008) | 57.9 (p 0.039) | 69.0 (p 0.954) | 62.1 (p 0.058) | 50.0 (p 0.004) | 62.5 (p 0.002) | 55.7 (p 0.064) | 52.5 (p 0.277) |
| OUT-29 all (same trials) | P5 | base | 63.8 | 54.4 | 73.8 | 52.7 | 40.2 | 62.1 | 56.7 | 52.5 |
| OUT-29 all (same trials) | P5 | ECG | 70.7 (p 0.018) | 60.2 (p 0.006) | 72.4 (p 0.765) | 60.1 (p 0.051) | 40.8 (p 0.500) | 66.4 (p 0.137) | 57.6 (p 0.451) | 54.0 (p 0.368) |
| HOSP-6 all | P1 | base | 66.7 | 61.1 | 66.7 | 33.3 | 43.1 | 45.8 | 47.6 | 37.0 |
| HOSP-6 all | P1 | ECG | 66.7 (p 0.625) | 66.7 (p 0.250) | 73.3 (p 0.188) | 61.9 (p 0.031) | 47.2 (p 0.500) | 45.8 (p 0.688) | 45.2 (p 0.750) | 38.9 (p 0.500) |
| HOSP-6 all | P5 | base | 62.5 | 57.4 | 68.3 | 45.2 | 45.8 | 37.5 | 42.9 | 40.7 |
| HOSP-6 all | P5 | ECG | 70.8 (p 0.375) | 59.3 (p 0.500) | 65.0 (p 0.938) | 59.5 (p 0.125) | 54.2 (p 0.375) | 47.9 (p 0.125) | 45.2 (p 0.500) | 48.1 (p 0.250) |

## T6. Per-trial HR (outpatient-RCT drug trials; P1)

| Trial | RCT HR | all base | all +ECG | outpt base | outpt +ECG | outpt +perm | |Δ| all base→ECG | |Δ| outpt base→ECG |
|---|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.20 | 1.25 | 1.22 | 1.13 | 1.16 | 0.007→0.038 | 0.013→0.067 |
| paradigm-hf-seq | 0.80 | 1.16 | 0.99 | 1.28 | 1.02 | 1.32 | 0.373→0.217 | 0.470→0.241 |
| elite-ii | 1.13 | 0.86 | 1.01 | 0.78 | 0.86 | 0.84 | 0.269→0.108 | 0.372→0.278 |
| life | 0.87 | 0.68 | 0.81 | 0.90 | 0.88 | 0.82 | 0.240→0.074 | 0.030→0.013 |
| aristotle | 0.79 | 0.55 | 0.65 | 0.49 | 0.61 | 0.47 | 0.367→0.198 | 0.482→0.251 |
| rocket-af | 0.88 | 0.51 | 0.51 | 0.57 | 0.67 | 0.58 | 0.555→0.550 | 0.431→0.269 |
| rely | 0.66 | 0.77 | 0.73 | 0.98 | 0.91 | 0.82 | 0.155→0.099 | 0.396→0.324 |
| allhat | 0.98 | 1.31 | 1.22 | 1.09 | 1.07 | 1.06 | 0.289→0.216 | 0.106→0.085 |
| emperor-preserved-v2 | 0.79 | 0.76 | 0.81 | 0.70 | 0.71 | 0.74 | 0.032→0.019 | 0.125→0.100 |
| east-afnet4 | 0.79 | 1.07 | 0.94 | 0.89 | 0.86 | 0.88 | 0.305→0.170 | 0.117→0.083 |
| cabana-v2 | 0.86 | 0.25 | 0.32 | 0.51 | 0.52 | 0.45 | 1.230→0.989 | 0.526→0.502 |
| ontarget | 1.01 | 0.81 | 0.84 | 0.89 | 0.89 | 0.91 | 0.221→0.187 | 0.122→0.126 |
| value | 1.04 | 0.74 | 0.76 | 0.87 | 0.85 | 0.87 | 0.334→0.312 | 0.184→0.201 |
| ascot | 0.90 | 0.80 | 0.89 | 0.87 | 0.85 | 0.88 | 0.119→0.006 | 0.033→0.052 |
| empa-reg | 0.86 | 0.77 | 0.66 | 0.74 | 0.69 | 0.73 | 0.110→0.266 | 0.153→0.216 |
| carolina | 0.98 | 0.99 | 0.91 | 0.95 | 0.85 | 0.93 | 0.009→0.076 | 0.033→0.144 |
| leader | 0.87 | 0.57 | 0.54 | 0.74 | 0.60 | 0.90 | 0.423→0.478 | 0.161→0.373 |
| sustain6 | 0.74 | 0.49 | 0.54 | 0.54 | 0.61 | 0.66 | 0.407→0.307 | 0.315→0.201 |
| rewind | 0.88 | 0.86 | 0.82 | 0.83 | 0.73 | 0.91 | 0.019→0.073 | 0.054→0.183 |
| declare | 0.83 | 1.81 | 1.36 | 1.63 | 1.11 | 1.57 | 0.779→0.492 | 0.677→0.291 |
| canvas | 0.86 | 0.82 | 0.95 | 0.79 | 1.04 | 0.99 | 0.050→0.095 | 0.088→0.188 |
| tecos | 0.98 | 0.88 | 0.88 | 0.81 | 0.82 | 0.87 | 0.105→0.106 | 0.193→0.173 |
| carmelina | 1.02 | 1.01 | 0.98 | 1.05 | 1.11 | 1.12 | 0.011→0.039 | 0.025→0.084 |
| insight | 1.10 | 1.74 | 1.49 | 1.71 | 1.95 | 1.74 | 0.459→0.305 | 0.440→0.570 |
| affirm | 1.15 | 1.35 | 1.11 | 1.09 | 0.96 | 0.88 | 0.159→0.039 | 0.050→0.181 |
| af-chf | 1.06 | 1.42 | 1.26 | 1.30 | 1.07 | 1.26 | 0.289→0.173 | 0.206→0.007 |
| precision | 0.93 | 0.70 | 0.73 | 0.67 | 0.69 | 0.70 | 0.283→0.243 | 0.323→0.305 |
| lodestar | 1.06 | 1.09 | 0.91 | 1.00 | 0.96 | 0.84 | 0.030→0.157 | 0.059→0.102 |
| frail-af | 1.69 | 0.96 | 1.08 | 1.00 | 0.99 | 0.92 | 0.569→0.445 | 0.522→0.536 |
| protect-af | 0.62 | 0.55 | 0.72 | – | – | – | 0.115→0.153 | – |
| raft-af | 0.71 | 0.57 | 0.60 | 0.66 | 0.62 | 0.67 | 0.227→0.169 | 0.078→0.139 |
| active-w | 1.44 | 1.47 | 1.57 | 1.44 | 1.40 | 1.49 | 0.019→0.085 | 0.001→0.028 |
