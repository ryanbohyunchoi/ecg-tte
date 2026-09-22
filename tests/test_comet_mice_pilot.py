from datetime import date
import json
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_comet_mice_pilot import model_spec,validate_completed,BASE
from build_shared_tables import BuildError


def synthetic_rows():
    rng=random.Random(17)
    features=json.loads((BASE/'docs/COMET_PSM_TABLE_V2.json').read_text())['covariates']
    rows=[]
    for i in range(160):
        row=dict(patient_key=f'synthetic_{i}',treatment_arm='carvedilol_candidate' if i%2 else 'metoprolol_tartrate_candidate',index_date=date(2020+i%3,1,1))
        for f in features:
            name=f['name']
            row[name]=(rng.randrange(2) if f['type']=='binary_recorded_evidence' else rng.randrange(10) if f['type']=='count' else 30+rng.random()*10)
        row.update(recorded_sex='F' if i%3 else 'M',index_year=2020+i%3,age_at_index=40+i%50)
        for f in features:
            if f['type'] in ('continuous','binary_recorded_evidence') and rng.random()<.2:row[f['name']]=None
        rows.append(row)
    return rows


class PilotTests(unittest.TestCase):
    def test_spec_has_no_identifiers_or_outcomes_and_rejects_bad_domains(self):
        rows=synthetic_rows();spec=model_spec(rows)
        self.assertEqual(len(spec['columns']),33)
        self.assertNotIn('patient_key',spec['columns'])
        self.assertNotIn('index_date',spec['columns'])
        rows[0]['ckd']=2
        with self.assertRaisesRegex(BuildError,'nonbinary'):model_spec(rows)

    def test_observed_preservation_donor_support_and_binary_validation(self):
        rows=synthetic_rows();spec=model_spec(rows)
        completed=[]
        for r in rows:
            completed.append({f:str(r[f] if r[f] is not None else next(x[f] for x in rows if x[f] is not None)) for f in spec['columns']})
        self.assertEqual(len(validate_completed(rows,completed,spec)),160)
        completed[0]['age_at_index']='999'
        with self.assertRaisesRegex(BuildError,'observed_value_changed'):validate_completed(rows,completed,spec)

    def test_all_missing_target_stops(self):
        rows=synthetic_rows()
        for r in rows:r['lvef']=None
        with self.assertRaisesRegex(BuildError,'insufficient_target_support'):model_spec(rows)

    def test_engine_integration_when_requested(self):
        import os
        if os.environ.get('COMET_TEST_R_MICE')!='1':self.skipTest('Set COMET_TEST_R_MICE=1 with R mice installed')
        import tempfile
        import pyarrow as pa
        import pyarrow.parquet as pq
        from collections import Counter
        from build_shared_tables import atomic_json,digest
        from run_comet_mice_pilot import run
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source';source.mkdir();rows=synthetic_rows()
            pq.write_table(pa.Table.from_pylist(rows),source/'restricted_cleaned_baseline.parquet')
            atomic_json(source/'summary.json',dict(version='comet_mice_preparation_v1',status='complete_mice_preparation',counts_valid=True,rows=len(rows),denominators=dict(Counter(r['treatment_arm'] for r in rows))))
            atomic_json(source/'manifest.json',dict(version='comet_mice_preparation_v1',outputs={'restricted_cleaned_baseline.parquet':digest(source/'restricted_cleaned_baseline.parquet')}))
            result=run(source,Path(tmp)/'output')
            self.assertTrue(result['counts_valid'])
            self.assertFalse(result['ready_for_psm'])
            self.assertTrue(result['engine']['convergence_available'])
            for i in range(1,6):
                completed=pq.read_table(Path(tmp)/'output'/f'restricted_completed_{i:02d}.parquet').to_pylist()
                for original,filled in zip(rows,completed):
                    for key,value in original.items():
                        if value is not None:self.assertEqual(value,filled[key])
            with self.assertRaises(FileExistsError):run(source,Path(tmp)/'output')
            atomic_json(source/'summary.json',dict(version='wrong'))
            with self.assertRaises(BuildError):run(source,Path(tmp)/'invalid')
