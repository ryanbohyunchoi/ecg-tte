import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_hf_medications as A

HEAD = ['PAT_MRN_ID','MEDICATION_ID','MEDICATION_NAME','GENERIC_NAME','SIMPLE_GENERIC',
        'ORDER_INST','START_DATE','ORDERING_MODE','ORDER_CLASS','MEDICATION_ROUTE']


class HFScreenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'; self.root.mkdir()
        self.path = self.root / 'meds.txt'

    def row(self, patient, drug, day='2024-01-01', cls='Normal', mode='Outpatient'):
        return [patient,'M1',drug,drug,drug,day+' 12:30',day,mode,cls,'Oral']

    def run_rows(self, rows, limit=None, catalog_limit=2000):
        with self.path.open('w') as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerow(HEAD); writer.writerows(rows)
        before = self.path.read_bytes()
        schema = A.inspect(self.root, 'meds.txt')['schema_sha256']
        r = A.run(self.root,'meds.txt',self.base/'report',schema,limit,catalog_limit)
        self.assertEqual(before,self.path.read_bytes())
        self.assertNotIn('SECRET',json.dumps(r))
        self.assertTrue(all(p.is_file() for p in (self.base/'report').iterdir()))
        return r

    def test_formulations_and_conflicts(self):
        cases = {
            'metoprolol tartrate 25 mg tablet':'metoprolol_tartrate_candidate',
            'metoprolol succinate ER':'metoprolol_succinate_review',
            'metoprolol 25 mg':'metoprolol_unspecified_review',
            'metoprolol tartrate TOPROL XL':'conflicting_names_review',
            'carvedilol phosphate CR':'carvedilol_extended_review',
            'carvedilol tablet':'carvedilol_not_marked_extended_candidate',
            'sacubitril-valsartan':'sacubitril_valsartan_candidate',
            'sacubitril':'sacubitril_without_valsartan_review',
            'enalapril maleate':'enalapril_candidate',
            'enalapril hydrochlorothiazide':'combination_review',
            'enalaprilat injection':None, 'valsartan tablet':None,
            'TOPROL XL':'brand_only_review', 'ENTRESTO':'brand_only_review',
            'notmetoprolol':None}
        for name, expected in cases.items():
            self.assertEqual(A.classify((name,'','')),expected,name)
        self.assertEqual(A.classify(('carvedilol','metoprolol tartrate','')), 'conflicting_names_review')
        self.assertEqual(A.classify(('metoprolol tartrate','metoprolol succinate','')), 'conflicting_names_review')

    def test_patients_overlap_same_day_history_and_no_double_count(self):
        rows = [self.row('SECRET_A','carvedilol','2023-01-01','Historical Med'),
                self.row('SECRET_A','carvedilol'),self.row('SECRET_A','carvedilol'),
                self.row('SECRET_A','metoprolol tartrate'),
                self.row('SECRET_B','carvedilol'),
                self.row('SECRET_B','metoprolol tartrate','2024-02-01'),
                self.row('SECRET_C','enalapril','2024-01-01','Historical Med')]
        r = self.run_rows(rows)
        self.assertEqual(r['status'],'complete_file')
        c=r['candidates']['carvedilol_not_marked_extended_candidate']
        self.assertEqual(c['records'],4)
        self.assertEqual(c['distinct_nonmarker_patient_keys'],2)
        self.assertEqual(c['outpatient_normal_print_with_parseable_order_patient_keys'],2)
        self.assertEqual(c['patients_with_earlier_recorded_same_bucket_order_than_first_candidate'],1)
        pair=r['pair_overlap']['COMET']
        self.assertEqual(pair['patients_in_both_dated_candidate_buckets'],2)
        self.assertEqual(pair['patients_with_same_calendar_day_candidate_orders_in_both'],1)
        self.assertIsNone(r['eligible_HF_patients'])
        self.assertIsNone(r['verified_fill_patients'])
        raw=(self.base/'report'/'restricted_mapping_review.json').read_text()
        self.assertNotIn('SECRET',raw)
        self.assertNotIn('2024-01-01',raw)

    def test_missing_dates_null_ids_and_setting(self):
        row=self.row('A','enalapril'); row[5]='NULL'
        r=self.run_rows([row,self.row('NULL','enalapril'),self.row('B','enalapril',mode='Inpatient')])
        b=r['candidates']['enalapril_candidate']
        self.assertEqual(b['distinct_nonmarker_patient_keys'],2)
        self.assertEqual(b['outpatient_normal_print_patient_keys'],1)
        self.assertEqual(b['outpatient_normal_print_with_parseable_order_patient_keys'],0)
        self.assertEqual(b['records_without_nonmarker_patient_key'],1)

    def test_catalog_limits_do_not_limit_patient_counts(self):
        r=self.run_rows([self.row('A','carvedilol'),self.row('B','enalapril')], catalog_limit=1)
        self.assertEqual(r['catalog_omitted_records']['name_catalog_records'],1)
        self.assertEqual(r['candidates']['enalapril_candidate']['distinct_nonmarker_patient_keys'],1)

    def test_prefix_not_population_and_output_refusal(self):
        r=self.run_rows([self.row('A','enalapril'),self.row('B','enalapril')],limit=1)
        self.assertEqual(r['status'],'bounded_prefix')
        with self.assertRaises(FileExistsError):
            A.run(self.root,'meds.txt',self.base/'report','schema')
        with self.assertRaises(ValueError):
            A.run(self.root,'meds.txt',self.root/'report','schema')

    def test_malformed_record_invalidates_counts(self):
        r=self.run_rows([self.row('A','enalapril'),['SECRET_BAD']])
        self.assertEqual(r['reason'],'row_width_mismatch')
        self.assertNotIn('candidates',r)
        self.assertEqual([p.name for p in (self.base/'report').iterdir()],['summary.json'])

    def test_schema_mismatch_and_symlink_fail(self):
        self.path.write_text('\t'.join(HEAD)+'\n')
        r=A.run(self.root,'meds.txt',self.base/'report','wrong')
        self.assertEqual(r['reason'],'schema_hash_mismatch')
        (self.root/'link.txt').symlink_to(self.path)
        r=A.run(self.root,'link.txt',self.base/'report2','wrong')
        self.assertEqual(r['status'],'failed_counts_invalid')


if __name__ == '__main__':
    unittest.main()
