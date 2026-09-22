#!/usr/bin/env python3
"""Pooled follow-up horizon feasibility; never assigns censoring or compares arms."""
import argparse
from collections import Counter, defaultdict
from datetime import date
import os
from pathlib import Path
import time

import pyarrow.parquet as pq

from audit_comet_outcome_sources import PATIENTS, HOSPITAL, OUTPATIENT, SOURCES, validate_paths
from build_comet_candidates import records
from build_shared_tables import BuildError, atomic_json, digest, open_table
from medication_quality import missing_kind

HORIZONS = (30, 90, 180, 365, 730)


def lag_bin(days):
    if days < 0: return 'before_index'
    if days == 0: return 'index_day'
    if days <= 30: return 'days1_30'
    if days <= 90: return 'days31_90'
    if days <= 180: return 'days91_180'
    if days <= 365: return 'days181_365'
    if days <= 730: return 'days366_730'
    return 'over730'


def month(day):
    return f'{day.year:04d}-{day.month:02d}'


def run(roster_path, snapshot, output):
    roster_path, snapshot, output = map(Path, (roster_path, snapshot, output))
    validate_paths(roster_path, snapshot, output)
    manifest_path = snapshot/'manifest.json'
    manifest_hash, roster_hash = digest(manifest_path), digest(roster_path)
    roster = pq.read_table(roster_path, columns=['patient_key','candidate_order_day']).to_pylist()
    if not 0 < len(roster) <= 1000000: raise BuildError('roster_size_invalid')
    anchors = {}
    for row in roster:
        key, index = row['patient_key'], row['candidate_order_day']
        if not key or key in anchors or not isinstance(index,date): raise BuildError('invalid_or_duplicate_roster_anchor')
        anchors[key] = index
    tables = {name:open_table(snapshot,name) for name in SOURCES}
    stamps = {p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for t in tables.values() for p in t.files}
    os.umask(0o077);output.mkdir(mode=0o700);started=time.monotonic()
    summary=dict(version='comet_followup_feasibility_v1',status='running',counts_valid=False,
        restricted_until_reviewed=True,roster_rows=len(roster),
        interpretation='Pooled horizon/source feasibility only. Future encounters are audit signals, not eligibility or censoring. No arm, endpoint assignment or effect estimate.')
    atomic_json(output/'summary.json',summary)
    try:
        death_dates=defaultdict(set);patient_rows=Counter();death_months=Counter()
        for row in records(tables[PATIENTS],['__patient_key','DEATH_DATE','__day_DEATH_DATE']):
            day=row['__day_DEATH_DATE'];raw=row['DEATH_DATE'] or ''
            if day is not None: death_months[month(day)]+=1
            key=row['__patient_key']
            if key in anchors:
                patient_rows[key]+=1
                if day is not None:death_dates[key].add(day)
                elif not missing_kind(raw):death_dates[key].add('unparseable')
        last_any={};last_inpatient={};first_inpatient={};encounter_months=Counter();inpatient_keys=defaultdict(set)
        for source in (*HOSPITAL,*OUTPATIENT):
            hospital=source in HOSPITAL;field='HOSP_ADMSN_DATE' if hospital else 'CONTACT_DATE'
            cols=['__patient_key','PAT_ENC_CSN_ID','__day_'+field]+(['INP_YN'] if hospital else [])
            for row in records(tables[source],cols):
                day=row['__day_'+field]
                if day is not None: encounter_months[source,month(day)]+=1
                key=row['__patient_key']
                if key not in anchors or day is None:continue
                index=anchors[key]
                if day>index and (key not in last_any or day>last_any[key]):last_any[key]=day
                if not hospital or (row['INP_YN'] or '').strip()!='1' or day<=index:continue
                csn=row['PAT_ENC_CSN_ID'] or ''
                if missing_kind(csn):continue
                token=(csn.strip(),day)
                inpatient_keys[key].add(token)
                if key not in first_inpatient or day<first_inpatient[key]:first_inpatient[key]=day
                if key not in last_inpatient or day>last_inpatient[key]:last_inpatient[key]=day
        index_years=Counter(d.year for d in anchors.values());death_lags=Counter();index_deaths=Counter()
        last_any_lags=Counter();last_inpatient_lags=Counter();first_inpatient_lags=Counter();horizon_signals=Counter()
        death_qc=Counter()
        for key,index in anchors.items():
            values=death_dates[key]
            if 'unparseable' in values:death_qc['unparseable_death_date']+=1;continue
            days={d for d in values if isinstance(d,date)}
            if not days:death_qc['no_recorded_death_date']+=1
            elif len(days)>1:death_qc['conflicting_death_dates']+=1
            else:
                death=next(iter(days));lag=(death-index).days;death_lags[lag_bin(lag)]+=1
                if lag>0:index_deaths[index.year]+=1
                else:death_qc['death_on_or_before_index']+=1
            if key in last_any:
                lag=(last_any[key]-index).days;last_any_lags[lag_bin(lag)]+=1
                for h in HORIZONS:
                    if lag>=h:horizon_signals['any_encounter_at_or_after_'+str(h)+'d']+=1
            else:last_any_lags['none_postindex']+=1
            if key in last_inpatient:last_inpatient_lags[lag_bin((last_inpatient[key]-index).days)]+=1
            else:last_inpatient_lags['none_postindex']+=1
            if key in first_inpatient:first_inpatient_lags[lag_bin((first_inpatient[key]-index).days)]+=1
            else:first_inpatient_lags['none_postindex']+=1
        if digest(manifest_path)!=manifest_hash or digest(roster_path)!=roster_hash or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=v for p,v in stamps.items()):raise BuildError('input_changed')
        years=sorted(index_years)
        summary.update(status='complete_followup_feasibility',counts_valid=True,
            index_years=[dict(year=y,patients=index_years[y],recorded_postindex_deaths=index_deaths[y]) for y in years],
            death_qc=dict(death_qc),death_lag_bins=dict(death_lags),
            last_any_encounter_lag_bins=dict(last_any_lags),last_inpatient_lag_bins=dict(last_inpatient_lags),
            first_inpatient_lag_bins=dict(first_inpatient_lags),horizon_encounter_signals=dict(horizon_signals),
            candidate_inpatient_keys=sum(len(v) for v in inpatient_keys.values()),
            recent_death_month_rows=[dict(month=m,rows=n) for m,n in sorted(death_months.items()) if m>='2023-01'],
            recent_encounter_month_rows=[dict(source=s,month=m,rows=n) for (s,m),n in sorted(encounter_months.items()) if m>='2023-01'],
            roster_sha256=roster_hash,clinical_manifest_sha256=manifest_hash,script_sha256=digest(Path(__file__)),
            next_gate='Establish death-source provenance and an external coverage end. Encounter landmark signals cannot define censoring or prove survival.')
        atomic_json(output/'manifest.json',dict(version=summary['version'],roster_sha256=roster_hash,
            clinical_manifest_sha256=manifest_hash,script_sha256=digest(Path(__file__))))
    except Exception:
        summary.update(status='failed_counts_invalid',counts_valid=False);raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-started,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('roster-parquet','clinical-snapshot','output-dir'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    try:run(a.roster_parquet,a.clinical_snapshot,a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Pooled follow-up feasibility complete; review aggregate summary on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
