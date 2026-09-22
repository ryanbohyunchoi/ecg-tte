from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_comet_numeric_candidates as Q
from build_shared_tables import digest, atomic_json, BuildError


class NumericTests(unittest.TestCase):
    def test_profiles_keep_extremes_and_separate_nonfinite(self):
        p=Q.profile([None,float('nan'),float('inf'),9999999.,-1.,0.,1.2])
        self.assertEqual(p['finite'],4);self.assertEqual(p['nulls'],1)
        self.assertEqual(p['nonfinite_or_non_numeric'],2);self.assertEqual(p['possible_sentinel_values'],1)
        self.assertIsNone(p['quantiles']);self.assertEqual(p['magnitude_counts']['ge10000'],1)
        self.assertEqual(Q.quantile([0,10],.25),2.5)
        self.assertEqual(Q.quantile([-1e308,1e308],.5),0)
        self.assertIsNotNone(Q.profile(list(range(20)))['quantiles'])

    def test_saved_artifact_and_lineage_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);src=p/'mapped';src.mkdir()
            r=dict(patient_key='A',treatment_arm='arm',index_date=date(2024,1,1),index_year=2024,**{f:None for f in Q.FIELDS})
            r.update(age_at_index=50.,creatinine=1.2,sbp=120.,dbp=80.)
            pq.write_table(pa.Table.from_pylist([r]),src/'restricted_baseline_resolution.parquet')
            pq.write_table(pa.table({'patient_key':['A'],'feature':['creatinine'],'status':['mapped_numeric_units_unverified']}),src/'restricted_feature_status.parquet')
            lineage=dict(patient_key='A',target='creatinine',source='source',component_id='795',result_day=date(2023,12,1),status='mapped_numeric_units_unverified',raw_value='1.2')
            pq.write_table(pa.Table.from_pylist([lineage,lineage]),src/'restricted_lab_selected_lineage.parquet')
            atomic_json(src/'lab_mapping_report.json',{})
            atomic_json(src/'summary.json',dict(version='comet_baseline_resolution_v2_mapped_labs',status='complete_resolution_candidate',counts_valid=True,rows=1,denominators={'arm':1}))
            manifest=dict(version='comet_baseline_resolution_v2_mapped_labs',outputs={f.name:digest(f) for f in src.iterdir() if f.name!='summary.json'})
            atomic_json(src/'manifest.json',manifest)
            out=Q.run(src,p/'qc')
            self.assertTrue(out['counts_valid']);self.assertFalse(out['ready_for_mice'])
            self.assertEqual(out['lab_component_distributions'][0]['finite'],1)
            self.assertEqual(out['paired_bp_qc'],[dict(arm='arm',flag='paired_bp_candidates',patient_keys=1)])
            lineage['raw_value']='1.3';pq.write_table(pa.Table.from_pylist([lineage]),src/'restricted_lab_selected_lineage.parquet')
            with self.assertRaisesRegex(BuildError,'mapped_artifact_changed'):Q.run(src,p/'bad')
            manifest['outputs']['restricted_lab_selected_lineage.parquet']=digest(src/'restricted_lab_selected_lineage.parquet');atomic_json(src/'manifest.json',manifest)
            with self.assertRaisesRegex(BuildError,'lineage_value_mismatch'):Q.run(src,p/'inconsistent')
            self.assertFalse(json.loads((p/'inconsistent'/'summary.json').read_text())['counts_valid'])
