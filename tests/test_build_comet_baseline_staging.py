import contextlib
from datetime import date
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_comet_baseline_staging as S
import build_shared_tables as B

class StagingTests(unittest.TestCase):
    def test_name_and_code_leads_not_substring_accidents(self):
        self.assertEqual(S.tokens('I48.91;N18.3'),{'I4891','N183'})
        self.assertIsNone(S.tokens('I48.91;bad'))
        f=S.drug_flags(('sacubitril valsartan',));self.assertIn('arni_order',f);self.assertNotIn('arb_order',f)
        self.assertNotIn('digoxin_order',S.drug_flags(('notdigoxin',)))
    def test_recorded_policy_positive_overrides_uncertainty(self):
        self.assertEqual(S.recorded_binary(False,False),(0,'no_qualifying_record'))
        self.assertEqual(S.recorded_binary(False,True),(None,'recorded_evidence_unassessable'))
        self.assertEqual(S.recorded_binary(True,True),(1,'recorded_positive'))

    def test_linkage_diagnostic_does_not_relax_date_or_key(self):
        index=date(2024,1,1)
        self.assertEqual(S.timing(date(2023,1,1),index),'prior365')
        self.assertEqual(S.timing(date(2022,12,31),index),'older')
        self.assertEqual(S.timing(index,index),'same_day')
        self.assertEqual(S.timing(None,index),'missing_date')
        enc={('A','E'):{(date(2023,12,1),'hospital_source','1','1')},
             ('B','E'):{(date(2023,12,1),'hospital_source','0','1')}}
        anchors={k:{'candidate_arm':'arm'} for k in ('A','B')}
        self.assertEqual(S.linkage_report(enc,{'E':{'A','B'}},{},anchors),[])
        del enc['B','E']
        links={(('A','E'),'hospital_diagnoses'):{'any_diagnosis_same_key','hf_code_same_key_any_date','hf_dx_date_future'}}
        rows=S.linkage_report(enc,{'E':{'A'}},links,anchors)
        stages={r['stage'] for r in rows}
        self.assertIn('hf_dx_date_future',stages)
        self.assertNotIn('hf_dx_date_prior365',stages)

    def build(self,root,name,tables):
        raw=root/(name+'_raw');raw.mkdir();specs=[]
        for n,(t,dates) in tables.items():
            p=raw/(n+'.parquet');pq.write_table(t,p)
            specs.append(dict(id=n,path=str(p),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],expected_rows=t.num_rows,key='PAT_MRN_ID',dates=dates,terminal_empty=False))
        out=root/name
        with contextlib.redirect_stdout(io.StringIO()):B.build(specs,out)
        return out
    def test_full_assembly_recorded_zero_and_linkage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            dx=pa.table({'PAT_MRN_ID':['A','A'],'DX_DATE':['2023-12-01','2024-01-02'],'CALC_DX_DATE':['2023-12-01','2023-12-02'],'CURRENT_ICD9_LIST':['',''],'CURRENT_ICD10_LIST':['I50.2;I48.91','E11.9;I50.9'],'PAT_ENC_CSN_ID':['E1','E2']})
            core=self.build(root,'core',{
                'echo_studies':(pa.table({'PAT_MRN_ID':['A'],'EchoDate':['2023-12-01'],'EF':[30.]}),['EchoDate']),
                'hospital_diagnoses':(dx,['DX_DATE','CALC_DX_DATE']),'outpatient_diagnoses':(dx,['DX_DATE','CALC_DX_DATE']),
                'medication_orders':(pa.table({'PAT_MRN_ID':['A','A'],'ORDER_INST':['2023-12-01','2024-01-01'],
                  'MEDICATION_NAME':['lisinopril','digoxin'],'GENERIC_NAME':['',''],'SIMPLE_GENERIC':['','']}),['ORDER_INST'])})
            clinical=self.build(root,'clinical',{
                'test_patients':(pa.table({'PAT_MRN_ID':['A','B'],'BIRTH_DATE':['1980-01-01','1990-01-01'],'SEX_C':['1','2'],'SEX':['Female','Male']}),['BIRTH_DATE']),
                'test_hosp_enc':(pa.table({'PAT_MRN_ID':['A','A'],'HOSP_ADMSN_DATE':['2023-12-01']*2,'PAT_ENC_CSN_ID':['E1']*2,'ED_YN':['1']*2,'INP_YN':['1']*2}),['HOSP_ADMSN_DATE']),
                'test_outpatient_enc':(pa.table({'PAT_MRN_ID':['A'],'CONTACT_DATE':['2023-12-02'],'PAT_ENC_CSN_ID':['E2']}),['CONTACT_DATE'])})
            report=root/'cohort';report.mkdir();cp=report/'restricted_broad_candidates.parquet'
            arms=['carvedilol_candidate','metoprolol_tartrate_candidate'];days=[date(2024,1,1)]*2
            pq.write_table(pa.table({'patient_key':['A','B'],'candidate_arm':arms,'candidate_order_day':days}),cp)
            (report/'summary.json').write_text(json.dumps(dict(version='comet_broad_exploratory_v2',status='complete_exploratory_cohort_audit',counts_valid=True,selected_candidate_keys=2,core_snapshot=str(core))))
            (report/'restricted_manifest.json').write_text(json.dumps(dict(version='comet_broad_exploratory_v2',rows=2,output_sha256=B.digest(cp),core_manifest_sha256=B.digest(core/'manifest.json'))))
            vr=root/'vitals';vr.mkdir();vp=vr/'restricted_vital_candidates.parquet'
            vals=dict(patient_key=['A','B'],arm=arms,index_date=days,bp_first_candidate=[120.,None],bp_second_candidate=[80.,None],pulse_candidate=[70.,None],bmi_candidate=[25.,None])
            for f in ('bp','pulse','bmi'):vals[f+'_status']=['candidate_numeric_units_unverified','no_record_in_window']
            pq.write_table(pa.table(vals),vp)
            (vr/'summary.json').write_text(json.dumps(dict(status='complete_candidate_extraction',counts_valid=True)))
            (vr/'manifest.json').write_text(json.dumps(dict(version='comet_vital_candidates_v2',cohort_sha256=B.digest(cp),clinical_manifest_sha256=B.digest(clinical/'manifest.json'),output_sha256=B.digest(vp))))
            ids={'test_patients','test_hosp_enc','test_outpatient_enc'}
            with patch.object(S,'IDS',ids),contextlib.redirect_stdout(io.StringIO()):s=S.run(report,clinical,vr,root/'out')
            self.assertTrue(s['counts_valid']);self.assertFalse(s['ready_for_mice'])
            t=pq.read_table(root/'out'/'restricted_baseline_staging.parquet');self.assertEqual(t.num_columns,36);self.assertEqual(t.num_rows,2)
            a,b=t.to_pylist();self.assertEqual(a['age_at_index'],44);self.assertEqual(a['recorded_sex'],'Female')
            self.assertEqual(a['atrial_fibrillation'],1);self.assertEqual(a['diabetes'],0)
            self.assertEqual(a['ace_inhibitor_order'],1);self.assertEqual(a['digoxin_order'],0)
            self.assertEqual(a['hospital_admissions'],1);self.assertEqual(a['hf_hospital_admissions'],1)
            self.assertEqual(b['diabetes'],0);self.assertEqual(b['digoxin_order'],0)
            self.assertIsNone(b['hospital_admissions']);self.assertIsNone(a['creatinine'])
            self.assertEqual(sum(x['patient_keys'] for x in s['feature_status_counts']),66)
            diag=json.loads((root/'out'/'hf_linkage_diagnostic.json').read_text())
            hospital={x['stage']:x['encounter_keys'] for x in diag['linkage_counts'] if x['diagnosis_source']=='hospital_diagnoses'}
            self.assertEqual(hospital['inpatient_encounter_denominator'],1)
            self.assertEqual(hospital['hf_dx_date_prior365'],1)
            self.assertNotIn('hf_dx_date_future',hospital) # E2 is outpatient, not inpatient.
            with patch.object(S,'IDS',ids),self.assertRaises(FileExistsError):S.run(report,clinical,vr,root/'out')
            with vp.open('ab') as f:f.write(b'changed')
            with patch.object(S,'IDS',ids),self.assertRaisesRegex(B.BuildError,'incompatible_vital'):S.run(report,clinical,vr,root/'bad')

if __name__=='__main__':unittest.main()
