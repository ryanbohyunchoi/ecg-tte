import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_hf_sources as A

class SourceAuditTests(unittest.TestCase):
    def test_ef_quality_not_threshold_selection(self):
        for value, label in [(None,'null'),(float('nan'),'nonfinite'),(float('inf'),'nonfinite'),
            (-1,'outside_0_100'),(101,'outside_0_100'),(0,'zero'),(.4,'positive_le_1_scale_ambiguous'),
            (35,'gt_1_le_35'),(40,'gt_35_le_40'),(50,'gt_40_le_50'),(60,'gt_50_le_100')]:
            self.assertEqual(A.ef_band(value),label)

    def test_identity_and_code_structure(self):
        self.assertEqual(A.key('  A001 '),'A001')
        self.assertNotEqual(A.key('001'),A.key('1'))
        self.assertIsNone(A.key('NULL'))
        self.assertEqual(A.code_structure('I50.22'),'single_icd10_shaped_token')
        self.assertEqual(A.code_structure('I50.22;I10'),'contains_semicolon')
        self.assertEqual(A.code_structure('patient SECRET'),'other_structure')

    def test_echo_temporal_overlap_duplicates_and_privacy(self):
        db=sqlite3.connect(':memory:'); self.addCleanup(db.close); A.init_db(db)
        db.executemany('INSERT INTO meds VALUES (?,?,?)',[
            ('a','SECRET001','2024-06-01'),('b','SECRET001','2024-01-01'),('a','001','2024-06-01')])
        def row(day,ef=35,patient='SECRET001',accession='ACC_SECRET'):
            return dict(MRN=patient,EchoDate=day,EF=ef,AccessionNumber=accession)
        report={}
        A.echo_records([row('2024-05-01'),row('2024-05-01'),row('2024-06-01',40),
            row('2024-07-01',.4),row('2024-05-01',patient='1',accession='OTHER'),
            row('06/07/2024',None,accession=None)],db,report)
        flags=dict(db.execute("SELECT flag,COUNT(*) FROM coverage WHERE bucket='a' GROUP BY flag"))
        self.assertEqual(flags['ef_gt1_le100_before'],1)
        self.assertEqual(flags['ef_gt1_le100_same_day'],1)
        self.assertNotIn('ef_gt1_le100_after',flags)
        self.assertEqual(flags['any_echo'],1)
        self.assertEqual(report['counts']['repeated_accession_rows'],3)
        self.assertEqual(report['counts']['accession_rows_disagreeing_with_first'],2)
        self.assertEqual(report['date_formats']['slash_day_month_ambiguous_not_compared'],1)
        self.assertNotIn('SECRET',json.dumps(report))
        self.assertNotIn('2024',json.dumps(report))

    def test_literal_width_schema_and_scope(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'dx.txt'; p.write_text('PAT_MRN_ID\tDX_DATE\nA\t2024-01-01\nB\t2024-02-01\n')
            schema=A.inspect(p.parent,p.name)['schema_sha256']
            r={}; self.assertEqual(len(list(A.literal_rows(p,schema,r,1))),1)
            self.assertEqual(r['status'],'bounded_prefix'); self.assertFalse(r['reached_eof'])
            r={}; self.assertEqual(len(list(A.literal_rows(p,schema,r))),2)
            self.assertTrue(r['reached_eof'])
            with self.assertRaises(A.CountError): list(A.literal_rows(p,'bad',{}))
            p.write_text(p.read_text()+'SECRET\n')
            with self.assertRaises(A.CountError): list(A.literal_rows(p,schema,{}))

    def test_source_change_invalidates(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'dx.txt'; p.write_text('PAT_MRN_ID\tDX_DATE\nA\t2024-01-01\n')
            schema=A.inspect(p.parent,p.name)['schema_sha256']
            it=A.literal_rows(p,schema,{}); next(it)
            with p.open('a') as f: f.write('B\t2024-01-02\n')
            with self.assertRaises(A.CountError): list(it)

    def test_output_overlap_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            with self.assertRaises(ValueError): A.run(root,root/'echo.parquet',root/'report')
            self.assertFalse((root/'report').exists())

    def test_missing_dependency_invalidates_without_private_error_output(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t); (base/'source').mkdir(); (base/'echo').mkdir()
            with patch.dict(sys.modules, {'pyarrow': None, 'pyarrow.parquet': None}):
                report=A.run(base/'source',base/'echo'/'SECRET.parquet',base/'out')
            self.assertEqual(report['status'],'failed_counts_invalid')
            self.assertFalse(report['counts_valid'])
            self.assertEqual(report['failure_stage'],'dependencies')
            self.assertNotIn('arm_echo_coverage',report)
            self.assertNotIn('Traceback',(base/'out'/'summary.json').read_text())
            with self.assertRaises(FileExistsError):
                A.run(base/'source',base/'echo'/'SECRET.parquet',base/'out')

if __name__=='__main__': unittest.main()
