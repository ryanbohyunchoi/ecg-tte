# Medication setting lineage and candidate cohort rules

Reviewed 2026-09-16. Local source-code inspection and previously reviewed H100
aggregates only. No cluster access, patient-row inspection, ETL execution or
clinical validation. Selection rules below are proposals, not a frozen protocol.

## What the setting fields establish

The supplemental `/home/rbc58/mnt/ecg-tte/drugs` reports confirm a `setting`
column with `home_meds`, `outpatient_admin`, and `inpatient` values. These are
source-family labels, not yet independently verified encounter settings.

Historical reference code in
`archive/2026-09-09-legacy-v1/scripts/build_drug_master.py` explains a compatible
construction. It was read only; nothing in the archive was imported or executed.
Its exact relationship to the current cluster files still requires run provenance.

| Source pattern | Assigned label | Code behavior and limits |
|---|---|---|
| `*_Meds.txt` | `home_meds` | `COHORT_SPECS` assigns the label; includes historical medication and prescription classes. Does not establish an outpatient visit or pharmacy fill. |
| `*_Outpatient_Enc_Med_Admin.txt` | `outpatient_admin` | Label assigned by file family; administration-action evidence is not preserved. Does not identify outpatient pharmacy dispensing. |
| `*_Hosp_Enc_Med_Admin_*.txt` | `inpatient` | Label assigned by file family; actual hospital encounter class is not checked. Hospital-source records cannot automatically be equated with inpatient admissions. |

Trace anchors: `COHORT_SPECS` at lines 78–100; date selection at 181–194;
optional field projection at 196–212; setting/cohort/source-file assignment at
214–216; shard naming at 268–286. The builder:

- Copies `ORDER_STATUS` rather than reconstructing status as of treatment index.
- Chooses a date column by availability: administration files prefer `TAKEN_TIME`,
  then `CONTACT_DATE`, then order/start candidates. All are renamed `order_date`.
  This is column-level selection, not row-level fallback for missing timestamps.
- Maps `end_date` from the first available end/discontinuation candidate; that
  output cannot establish medication supply duration.
- Omits refill/quantity/supply fields, encounter/order identifiers and `MAR_ACTION`.
- Does not validate administration actions or new treatment initiation. Historical
  comments asserting valid prescriptions or universal exclusion of inpatient starts
  are legacy claims, not accepted clinical rules for the restart.

The separate local `CardioMap/scripts/build_drug_master.py` at repository HEAD
`2cad31719a584a017bd6714a607377086d47df14` uses `outpmeds` metadata and a source-directory
label, without a validated encounter-setting field. Its projection also omits
refill/supply evidence. This is a different builder; a shared output name does not
prove the producing version of any current cluster table.

## RBC OMOP medication and visit lineage

Inspected local `reference/cards-misc` main `33532e6` and feature revision `9e9fbc9`.
The precise producing revision of current RBC gold remains unresolved.

- Both reviewed medication implementations combine Meds, hospital administration
  and outpatient administration source patterns; derive event time from `ORDER_INST`;
  retain only medication-name/class fields in addition to shared event fields; and
  emit the same constant `drug_type_concept_id` for every drug record. Main's constant
  is 32817. Neither output distinguishes these three source families through that
  type field. Start and end timestamps are set equal; no drug-to-visit key is emitted.
- Feature revision `step7_visits.py` maps `ACCT_BASECLS_HA` values Inpatient,
  Outpatient and Emergency to 9201, 9202 and 9203, preserving the raw class as
  `visit_source_value`. Thus hospital encounter files themselves can contain
  more than inpatient encounters.
- Feature revision `step8_op_visits.py` assigns 9202 to all outpatient-source rows
  and preserves `ENC_TYPE` as `visit_source_value`. The implementation explicitly
  leaves refinement of telephone/refill and other non-visit types unresolved.
- The reviewed visit builders generate surrogate visit IDs without preserving
  raw encounter IDs in gold. They therefore do not provide a demonstrated exact
  medication-to-encounter join. Same-patient date overlap is only a temporal clue.

OMOP's intended distinction between exposure provenance and linked encounter
setting does not establish that this particular mapping implemented it:
[OMOP conventions](https://ohdsi.github.io/CommonDataModel/dataModelConventions.html),
[CDM 5.4](https://ohdsi.github.io/CommonDataModel/cdm54.html).

## Proposed selection and follow-up contract

For a chronic outpatient initiation trial, classify the candidate medication event
at index, rather than classifying a person permanently as inpatient or outpatient.

1. Confirm age, indication, exclusions and sufficient captured baseline history
   using evidence available at index. Define a drug-specific washout for both arms;
   the first recorded order alone does not establish new use.
2. Use a verified outpatient pharmacy fill timestamp if the source supports a
   dispensing strategy. If only prescriptions are verifiable, explicitly define a
   prescribing strategy and use its validated order/start rule. Never rename an
   order date to a dispensing date. Historical reconciliation alone is insufficient.
3. Keep care setting and evidence type separate. An outpatient administration may
   suit an infusion trial but not a pharmacy-refill definition. Inpatient initiation
   and discharge initiation require separately specified strategies; do not pool
   them by relabeling a later outpatient record as the original start.
4. Retain the enrolled patient's subsequent inpatient, emergency and outpatient
   records for endpoint-specific follow-up. A later hospitalization does not remove
   an outpatient initiator. Outpatient follow-up is retained as well, but an outpatient
   diagnosis does not automatically satisfy a hospitalization endpoint.
5. Do not require a future encounter, refill, survival interval or continued use to
   qualify at the original index. Lack of a later visit is not evidence of no event
   or continued observability. Prespecify follow-up ascertainment, administrative
   end and loss-to-follow-up handling using the actual capture mechanism.
6. Retain later discontinuers in the agreed primary analysis. Only the separately
   specified secondary sustained-treatment strategy censors at a verified deviation,
   with appropriate weighting. Setting changes alone are not automatic deviations.

These proposals follow the alignment of eligibility, treatment assignment and
follow-up described by [Hernán et al.](https://pubmed.ncbi.nlm.nih.gov/27237061/).
No drug pair, washout, gap rule, horizon or endpoint is frozen here.

For easy comparison, a future event contract should retain `source_setting_label`,
`validated_care_setting`, `medication_evidence_type`, `event_time_basis`,
`setting_evidence_source`, and an explicit validation/unknown reason. Raw order and
encounter keys remain on the cluster. These fields are proposed, not implemented.
Feasibility summaries should cross-tabulate setting × evidence type × treatment
arm, with record counts, unique patients, eligible candidate starts, duplicates,
unknowns, baseline-history availability and exact linkage success. Patients may
appear in multiple settings; those counts must not be summed as disjoint groups.

## Next evidence request

Use the existing header inspector on the H100 for the RBC implementation delivery,
not another larger scan of the same derived medication rows. This explicit root
comes from the reviewed lineage; missing files should be reported, not guessed or
silently replaced. Ryan runs it from his checkout after obtaining these changes:

```bash
cd "$HOME/github/ecg-tte"
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
MED_TRACE_OUT=$(mktemp -d "/mnt/raid0/rbc58/ecg-tte/audits/medication-source-headers-XXXXXXXX")
python scripts/inspect_jdat_headers.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Meds.txt \
  --file CarDS_2435227_Hosp_Enc_Med_Admin_1.txt \
  --file CarDS_2435227_Hosp_Enc_Med_Admin_2.txt \
  --file CarDS_2435227_Outpatient_Enc_Med_Admin.txt \
  --file CarDS_2435227_Hosp_Enc.txt \
  --file CarDS_2435227_Outpatient_Enc.txt \
  --output-dir "$MED_TRACE_OUT/report"
```

Review `report/headers.md` and `report/summary.json` before sharing metadata only.
This reads bounded first lines, not patient histories. The run must establish
current schemas; it cannot validate field semantics by itself.

Then obtain the source dictionary/extract specification for order class/source,
status and status timing, fill versus authorized refill, supply, encounter class,
administration action and timestamp fields. The earlier T2DM headers include
refill/quantity candidates and administration encounter/action fields, but that is
not proof of the same columns in the RBC delivery. Confirm exact builder/run lineage
for the 13 supplemental files, including CMP/merged overlap. Only after those checks
should a new read-only, trial-specific linkage and candidate-index audit be built.
