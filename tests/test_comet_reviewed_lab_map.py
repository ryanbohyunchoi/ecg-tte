import contextlib
from datetime import date
import io
from pathlib import Path
import sys
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import comet_reviewed_lab_map as L
from build_shared_tables import atomic_json, digest, BuildError


class LabMapTests(unittest.TestCase):
    def observation(self,**changes):
        r=dict(day=date(2023,12,1),RESULT_TIME='2023-12-01 12:00',COMPONENT_ID='795',COMPONENT_NAME='BKR CREATININE',BASE_NAME='CREATININE',SPECIMEN_TYPE='Blood',SPECIMEN_SOURCE='Arm, Left',ORD_VALUE='1.2',explicit_units={})
        r.update(changes);return r

    def test_target_and_numeric_contract(self):
        for raw in ('<0.1','>20','1.2 mg/dL','NULL','NaN','1e3'):self.assertIsNone(L.number(raw))
        self.assertEqual(L.number(' 1.20 '),1.2)
        for component in ('12357','28029','13943','21319','13966','20728'):self.assertNotIn(component,L.MAP)

    def test_no_fallback_conflicts_and_specimen_gate(self):
        a=self.observation()
        v,s,_=L.select_latest([a,a]);self.assertEqual(v,1.2);self.assertEqual(s,'mapped_numeric_units_unverified')
        self.assertEqual(L.select_latest([a,self.observation(ORD_VALUE='1.3')])[1],'latest_timestamp_disagreement')
        self.assertEqual(L.select_latest([a,self.observation(RESULT_TIME='2023-12-01 13:00',ORD_VALUE='NULL')])[1],'latest_value_non_numeric_or_missing')
        self.assertEqual(L.select_latest([self.observation(SPECIMEN_TYPE='Urine')])[1],'specimen_not_confirmed_blood')
        self.assertEqual(L.select_latest([self.observation(COMPONENT_NAME='URINE CREATININE')])[1],'component_signature_changed')
        self.assertEqual(L.select_latest([self.observation(RESULT_TIME='2024-01-01 12:00')])[1],'latest_day_time_date_conflict')
        self.assertEqual(L.select_latest([self.observation(explicit_units={'UNIT':'mg/dL'})])[1],'unit_signature_changed_requires_review')

    def test_extract_uses_raw_value_and_preserves_unit_status(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            p=Path(tmp);labs=p/'labs';labs.mkdir();out=p/'out';out.mkdir();tables=[]
            t=pa.table({'__patient_key':['A'],'__source_row':[1],'__day_RESULT_DATE':[date(2023,12,1)],'RESULT_TIME':['2023-12-01 12:00'],'COMPONENT_ID':['795'],'COMPONENT_NAME':['BKR CREATININE'],'BASE_NAME':['CREATININE'],'ORD_VALUE':['1.2'],'ORD_NUM_VALUE':['9999999'],'SPECIMEN_TYPE':['Blood']})
            for n in L.SOURCES:
                path=labs/(n+'.parquet');pq.write_table(t,path);tables.append(dict(table=n,file=path.name,sha256=digest(path)))
            atomic_json(labs/'manifest.json',dict(tables=tables))
            anchors={'A':dict(candidate_arm='arm',candidate_order_day=date(2024,1,1))}
            v,s,report=L.extract(p,anchors,out)
            self.assertEqual(v['A','creatinine'],1.2);self.assertEqual(s['A','creatinine'],'mapped_numeric_units_unverified')
            self.assertIsNone(v['A','hemoglobin'])
            self.assertEqual(sum(x['rows'] for x in report['record_qc'] if x['flag']=='numeric_companion_disagrees_not_used'),3)
            with self.assertRaisesRegex(BuildError,'outside_baseline_window'):L.extract(p,{'A':dict(candidate_arm='arm',candidate_order_day=date(2023,12,1))},out)
