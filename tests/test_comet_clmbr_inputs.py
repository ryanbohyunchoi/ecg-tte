import sys
from pathlib import Path
from datetime import date, datetime
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_comet_clmbr_inputs import coverage, InputError, files

class InputTests(unittest.TestCase):
    def test_identity_cutoff_and_aggregate_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); person=root/'person.parquet'; meds=root/'meds.parquet'
            pq.write_table(pa.table({'person_id':[1,2,2,3,4], 'person_source_value':['secretA','secretB','outside','secretC','secretC']}),person)
            pq.write_table(pa.table({'subject_id':[1,1,1,1,2], 'time':[datetime(2020,1,1),datetime(2020,1,2),None,datetime(2020,1,1),datetime(2020,1,1)],'code':['SNOMED/1','SNOMED/2','static',None,'SNOMED/3']}),meds)
            roster=[dict(patient_key=k,treatment_arm='arm',index_date=date(2020,1,2)) for k in ['secretA','secretB','secretC','secretD']]
            result,linked=coverage(roster,[person],[meds]); arm=result['arms']['arm']
            self.assertEqual(arm['unique_person_link'],1)
            self.assertEqual(arm['ambiguous_person_link'],2)
            self.assertEqual(arm['no_exact_person_link'],1)
            self.assertEqual(arm['patients_with_dated_preindex_codes'],1)
            self.assertEqual(arm['dated_preindex_coded_rows'],1)
            self.assertEqual(arm['same_day_or_future_rows'],1)
            self.assertEqual(arm['undated_rows_not_used_for_prior_coverage'],1)
            self.assertNotIn('secret',str(result))
            self.assertEqual(len(linked),1)
    def test_no_history_not_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'person.parquet'
            pq.write_table(pa.table({'person_id':[1],'person_source_value':['A']}),p)
            result,_=coverage([dict(patient_key='A',treatment_arm='arm',index_date=date(2020,1,1))],[p],[])
            self.assertEqual(result['arms']['arm']['linked_patients_without_dated_preindex_codes'],1)
    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'link').symlink_to(root,target_is_directory=True)
            with self.assertRaises(InputError):files(root/'link')
