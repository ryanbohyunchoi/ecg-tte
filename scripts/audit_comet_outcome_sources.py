#!/usr/bin/env python3
"""Outcome-source QC on H100; no endpoint assignment or treatment comparison."""
import argparse
from collections import Counter, defaultdict
from datetime import date
import os
from pathlib import Path
import time

import pyarrow as pa
import pyarrow.parquet as pq

from build_comet_candidates import records
from build_shared_tables import BuildError, atomic_json, digest, open_table
from medication_quality import missing_kind

PATIENTS = 'Data_2025_04_03_patients'
HOSPITAL = ('Data_2025_04_03_hosp_enc', 'Data_2026_04_15_hosp_enc')
OUTPATIENT = ('Data_2025_04_03_outpatient_enc', 'Data_2026_04_15_outpatient_enc')
SOURCES = (PATIENTS, *HOSPITAL, *OUTPATIENT)


def validate_paths(roster, snapshot, output):
    paths = tuple(map(Path, (roster, snapshot, output)))
    if any(not p.is_absolute() or p.is_symlink() for p in paths):
        raise BuildError('absolute_nonsymlink_paths_required')
    if not roster.is_file() or not snapshot.is_dir() or output.exists():
        raise BuildError('roster_snapshot_or_new_output_required')
    out = output.resolve()
    for source in (roster.resolve(), snapshot.resolve()):
        if out == source or out in source.parents or source in out.parents:
            raise BuildError('output_source_overlap')


def death_state(days, raw_states, rows, index):
    """Missing death date remains unknown, never an observed non-event."""
    if rows == 0:
        return 'no_patient_row'
    if 'unparseable' in raw_states:
        return 'unparseable_death_date'
    if len(days) > 1:
        return 'conflicting_death_dates'
    if len(days) == 1:
        death = next(iter(days))
        return 'death_before_index' if death < index else 'death_on_index' if death == index else 'single_postindex_death_date'
    return 'no_recorded_death_date'


def encounter_relation(day, index):
    return 'undated' if day is None else 'preindex' if day < index else 'index_day' if day == index else 'postindex'


def run(roster_path, snapshot, output):
    roster_path, snapshot, output = map(Path, (roster_path, snapshot, output))
    validate_paths(roster_path, snapshot, output)
    manifest_path = snapshot/'manifest.json'
    manifest_hash, roster_hash = digest(manifest_path), digest(roster_path)
    roster = pq.read_table(roster_path, columns=['patient_key', 'candidate_order_day']).to_pylist()
    if not 0 < len(roster) <= 1000000:
        raise BuildError('roster_size_invalid')
    anchors = {}
    for row in roster:
        key, index = row['patient_key'], row['candidate_order_day']
        if not key or key in anchors or not isinstance(index, date):
            raise BuildError('invalid_or_duplicate_roster_anchor')
        anchors[key] = index
    tables = {name: open_table(snapshot, name) for name in SOURCES}
    stamps = {path: (Path(path).stat().st_size, Path(path).stat().st_mtime_ns)
              for table in tables.values() for path in table.files}
    os.umask(0o077)
    output.mkdir(mode=0o700)
    started = time.monotonic()
    summary = dict(version='comet_outcome_source_audit_v1', status='running', counts_valid=False,
                   restricted_until_reviewed=True, roster_rows=len(roster),
                   interpretation='Source and chronology QC only. Missing death dates are unknown; encounter rows are not adjudicated admissions. No endpoint, censor date, treatment comparison or effect estimate.')
    atomic_json(output/'summary.json', summary)
    try:
        death_days = defaultdict(set)
        birth_days = defaultdict(set)
        death_raw_states = defaultdict(set)
        patient_rows = Counter()
        global_qc, roster_qc = Counter(), Counter()
        death_years, encounter_years = Counter(), Counter()
        for row in records(tables[PATIENTS], ['__patient_key', '__day_BIRTH_DATE', 'DEATH_DATE', '__day_DEATH_DATE']):
            raw = row['DEATH_DATE'] or ''
            day = row['__day_DEATH_DATE']
            state = 'missing' if missing_kind(raw) else 'unparseable' if day is None else 'dated'
            global_qc[PATIENTS, state] += 1
            if day is not None:
                death_years[day.year] += 1
            key = row['__patient_key']
            if key in anchors:
                patient_rows[key] += 1
                death_raw_states[key].add(state)
                if row['__day_BIRTH_DATE'] is not None:
                    birth_days[key].add(row['__day_BIRTH_DATE'])
                if day is not None:
                    death_days[key].add(day)
        encounter_rows = defaultdict(list)
        for source in (*HOSPITAL, *OUTPATIENT):
            hospital = source in HOSPITAL
            date_field = 'HOSP_ADMSN_DATE' if hospital else 'CONTACT_DATE'
            columns = ['__patient_key', 'PAT_ENC_CSN_ID', date_field, '__day_'+date_field]
            if hospital:
                columns += ['HOSP_DISCH_DATE', '__day_HOSP_DISCH_DATE', 'INP_YN', 'ED_YN']
            for row in records(tables[source], columns):
                day = row['__day_'+date_field]
                date_state = 'missing' if missing_kind(row[date_field] or '') else 'unparseable' if day is None else 'dated'
                global_qc[source, date_state] += 1
                if hospital:
                    discharge_state = ('missing' if missing_kind(row['HOSP_DISCH_DATE'] or '') else
                                       'unparseable' if row['__day_HOSP_DISCH_DATE'] is None else 'dated')
                    global_qc[source, 'discharge_'+discharge_state] += 1
                if day is not None:
                    encounter_years[source, day.year] += 1
                key = row['__patient_key']
                if key not in anchors:
                    continue
                relation = encounter_relation(day, anchors[key])
                roster_qc[source, relation] += 1
                csn = row['PAT_ENC_CSN_ID'] or ''
                csn = '' if missing_kind(csn) else csn.strip()
                if len(csn) > 256:
                    raise BuildError('oversized_encounter_key')
                item = (source, csn, day, row['__day_HOSP_DISCH_DATE'] if hospital else None,
                        (row['INP_YN'] or '').strip() if hospital else '',
                        (row['ED_YN'] or '').strip() if hospital else '')
                encounter_rows[key].append(item)
        patient_qc = []
        states, flags = Counter(), Counter()
        for key, index in anchors.items():
            days = death_days[key]
            state = death_state(days, death_raw_states[key], patient_rows[key], index)
            states[state] += 1
            unique_death = next(iter(days)) if len(days) == 1 else None
            death_before_birth = (unique_death is not None and len(birth_days[key]) == 1 and
                                  unique_death < next(iter(birth_days[key])))
            rows = encounter_rows[key]
            seen, by_csn = set(), defaultdict(set)
            duplicate_rows = 0
            postdeath = 0
            discharge_after_death = 0
            inpatient_candidates = set()
            inpatient_episodes = set()
            missing_inpatient_keys = 0
            discharge_before_admit = 0
            for source, csn, day, discharge, inp, ed in rows:
                if unique_death is not None and day is not None and day > unique_death:
                    postdeath += 1
                if source in HOSPITAL:
                    if unique_death is not None and discharge is not None and discharge > unique_death:
                        discharge_after_death += 1
                    if day is not None and discharge is not None and discharge < day:
                        discharge_before_admit += 1
                    if inp == '1' and day is not None and day > index:
                        if csn:
                            inpatient_candidates.add((csn, day))
                            inpatient_episodes.add((csn, day, discharge))
                        else:
                            missing_inpatient_keys += 1
                    if csn:
                        by_csn[csn].add(day)
                identity = (source.endswith('hosp_enc'), csn, day, discharge, inp, ed)
                if identity in seen:
                    duplicate_rows += 1
                seen.add(identity)
            conflicting_admission_keys = sum(len(ds) > 1 for ds in by_csn.values())
            episodes = sorted(inpatient_episodes, key=lambda item: (item[1], item[0]))
            adjacent_episode_pairs = sum(
                earlier[2] is not None and 0 <= (later[1]-earlier[2]).days <= 1
                for earlier, later in zip(episodes, episodes[1:]) if earlier[0] != later[0])
            qc = dict(patient_key=key, index_day=index, death_date=unique_death,
                      death_date_state=state, patient_source_rows=patient_rows[key],
                      death_before_birth=death_before_birth,
                      encounter_rows=len(rows), postdeath_encounter_rows=postdeath,
                      discharge_after_death_rows=discharge_after_death,
                      duplicate_encounter_rows=duplicate_rows,
                      postindex_inpatient_candidate_keys=len(inpatient_candidates),
                      inpatient_rows_missing_key=missing_inpatient_keys,
                      conflicting_admission_keys=conflicting_admission_keys,
                      discharge_before_admission_rows=discharge_before_admit,
                      adjacent_episode_pairs_for_review=adjacent_episode_pairs)
            patient_qc.append(qc)
            if death_before_birth:
                flags['death_before_birth_patients'] += 1
            for name in ('postdeath_encounter_rows', 'discharge_after_death_rows', 'duplicate_encounter_rows',
                         'inpatient_rows_missing_key', 'conflicting_admission_keys',
                         'discharge_before_admission_rows', 'adjacent_episode_pairs_for_review'):
                if qc[name]: flags[name+'_patients'] += 1
                flags[name+'_rows_or_keys'] += qc[name]
            if inpatient_candidates:
                flags['patients_with_postindex_inpatient_candidate'] += 1
        if (digest(manifest_path) != manifest_hash or digest(roster_path) != roster_hash or
                any((Path(path).stat().st_size, Path(path).stat().st_mtime_ns) != stamp
                    for path, stamp in stamps.items())):
            raise BuildError('input_changed')
        private = output/'restricted_patient_qc.parquet'
        pq.write_table(pa.Table.from_pylist(patient_qc), private, compression='zstd')
        summary.update(status='complete_source_qc', counts_valid=True,
                       death_date_states=dict(states), encounter_flags=dict(flags),
                       global_source_rows=[dict(source=s, state=state, rows=n) for (s, state), n in sorted(global_qc.items())],
                       roster_encounter_rows=[dict(source=s, relation=relation, rows=n) for (s, relation), n in sorted(roster_qc.items())],
                       death_year_rows=[dict(year=year, rows=n) for year, n in sorted(death_years.items())],
                       encounter_year_rows=[dict(source=s, year=year, rows=n) for (s, year), n in sorted(encounter_years.items())],
                       roster_sha256=roster_hash, clinical_manifest_sha256=manifest_hash,
                       script_sha256=digest(Path(__file__)),
                       next_gate='Review death-date provenance, coverage endpoint and inpatient episode semantics. Do not infer survival or assign a follow-up end from these counts.')
        atomic_json(output/'manifest.json', dict(version=summary['version'], roster_sha256=roster_hash,
                                                  clinical_manifest_sha256=manifest_hash,
                                                  restricted_patient_qc_sha256=digest(private),
                                                  script_sha256=digest(Path(__file__))))
    except Exception:
        summary.update(status='failed_counts_invalid', counts_valid=False)
        raise
    finally:
        summary['elapsed_seconds'] = round(time.monotonic()-started, 3)
        atomic_json(output/'summary.json', summary)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('roster-parquet', 'clinical-snapshot', 'output-dir'):
        p.add_argument('--'+name, required=True, type=Path)
    a = p.parse_args()
    try:
        result = run(a.roster_parquet, a.clinical_snapshot, a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc, BuildError) else type(exc).__name__))
        return 1
    print('Outcome-source QC complete. Review restricted summary on H100; no endpoint assigned.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
