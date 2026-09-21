from datetime import date,timedelta
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import count_comet_hf_variants as C
import build_shared_tables as B

class VariantTests(unittest.TestCase):
    def test_code_groups_and_combined_not_isolated(self):
        f=C.dx_flags('I50.42','Combined systolic and diastolic heart failure')
        self.assertTrue({'general','systolic','combined','diastolic_mention'}<=f)
        self.assertNotIn('isolated_diastolic',f)
        self.assertIn('isolated_diastolic',C.dx_flags('I50.32','Diastolic HF'))
        self.assertIn('hfpef_mention',C.dx_flags('I50.9','HFpEF'))
        self.assertIn('hfpef_mention',C.dx_flags('I50.9','HF with preserved ejection fraction'))

    def test_low_ef_rescue_versus_entire_patient_exclusion(self):
        r=C.scenarios({'general','isolated_diastolic'},True)
        self.assertTrue(r['general_exclude_isolated_diastolic_or_hfpef_code_branch'])
        self.assertFalse(r['general_exclude_isolated_diastolic_or_hfpef_entire_patient'])
        self.assertTrue(r['systolic_or_ef_lt40'])

    def test_combined_sensitivity_changes_count(self):
        r=C.scenarios({'general','systolic','combined','diastolic_mention'},False)
        self.assertTrue(r['general_exclude_isolated_diastolic_or_hfpef_code_branch'])
        self.assertFalse(r['general_exclude_any_diastolic_or_hfpef_code_branch'])

    def test_ef40_boundary_missing_and_conflicts(self):
        index=date(2024,1,1);day=index-timedelta(days=1)
        for value,label in ((39.9,'gt1_lt40'),(40,'eq40'),(40.1,'gt40_le100'),('missing','missing')):
            self.assertEqual(C.echo_state(dict(day=day,values={value}),index),label)
        self.assertEqual(C.echo_state(dict(day=day,values={30,35}),index),'latest_day_disagreement')
        self.assertEqual(C.echo_state(dict(day=index-timedelta(days=366),values={30}),index),'stale_over365')

    def test_malformed_codes_no_partial_acceptance_or_name_export(self):
        f=C.dx_flags('I50.22;garbage','SECRET_SYNTHETIC')
        self.assertNotIn('systolic',f);self.assertIn('unresolved_code',f)
        self.assertNotIn('SECRET',str(f))

    def test_end_to_end_projected_parquet_and_fixed_denominators(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();core=root/'core'
            dx=pa.table({'PAT_MRN_ID':['A','B','C','A'],
                         'DX_DATE':['2024-01-01']*3+['2025-01-01'],
                         'CALC_DX_DATE':['2024-01-01']*4,
                         'CURRENT_ICD10_LIST':['I50.9','I50.42','I50.32','I50.32'],
                         'DX_NAME':['HF','Combined systolic diastolic HF','Diastolic HF','Diastolic HF']})
            echo=pa.table({'MRN':['A','B','C','C'], 'EchoDate':['2024-01-01']*3+['2024-02-02'],
                           'EF':[39.,45.,30.,55.]})
            specs=[]
            for name,t,key,dates in [('hospital_diagnoses',dx,'PAT_MRN_ID',['DX_DATE','CALC_DX_DATE']),
                                     ('outpatient_diagnoses',dx.slice(0,1),'PAT_MRN_ID',['DX_DATE','CALC_DX_DATE']),
                                     ('echo_studies',echo,'MRN',['EchoDate'])]:
                path=raw/(name+'.parquet');pq.write_table(t,path)
                specs.append(dict(id=name,path=str(path),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],
                    expected_rows=t.num_rows,key=key,dates=dates,terminal_empty=False))
            with contextlib.redirect_stdout(io.StringIO()):B.build(specs,core)
            report=root/'comet-candidates-test'/'report';report.mkdir(parents=True)
            candidate=report/'restricted_candidates.parquet'
            pq.write_table(pa.table({'patient_key':['A','B','C'],'candidate_arm':['carvedilol_candidate']*3,
                                     'candidate_order_day':[date(2024,2,1)]*3}),candidate)
            h=B.digest(core/'manifest.json')
            (report/'summary.json').write_text(json.dumps(dict(version='comet_candidates_v1',status='complete_provisional_candidates',
                counts_valid=True,candidate_patient_keys=3,core_manifest_sha256=h)))
            (report/'restricted_manifest.json').write_text(json.dumps(dict(version='comet_candidates_v1',rows=3,core_manifest_sha256=h,
                core_snapshot=str(core),candidate_sha256=B.digest(candidate))))
            with contextlib.redirect_stdout(io.StringIO()):r=C.run(report,root/'out')
            self.assertTrue(r['counts_valid']);self.assertEqual(r['denominators'],{'carvedilol_candidate':3})
            counts={(x['date_view'],x['scenario']):x['patient_keys'] for x in r['scenario_counts']}
            self.assertEqual(counts['DX_DATE','systolic_or_ef_lt40'],3)
            self.assertEqual(counts['DX_DATE','general_exclude_isolated_diastolic_or_hfpef_entire_patient'],2)
            self.assertEqual(counts['CALC_DX_DATE','general_exclude_isolated_diastolic_or_hfpef_entire_patient'],1)
            self.assertEqual(counts['DX_DATE','general_exclude_any_diastolic_or_hfpef_entire_patient'],1)
            for v in C.VIEWS:self.assertEqual(sum(x['patient_keys'] for x in r['evidence_strata'] if x['date_view']==v),3)
            self.assertEqual(C.discover(root),report)

if __name__=='__main__':unittest.main()
