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
    def test_recency_boundaries_and_tokenization(self):
        for lag,label in [(None,'no_prior_candidate_ef'),(1,'days_1_90'),(90,'days_1_90'),
            (91,'days_91_180'),(180,'days_91_180'),(181,'days_181_365'),
            (365,'days_181_365'),(366,'days_366_730'),(730,'days_366_730'),(731,'days_over_730')]:
            self.assertEqual(A.recency_band(lag),label)
        with self.assertRaises(ValueError): A.recency_band(0)
        self.assertEqual(A.token_structure('I50.2, I10'),'all_split_tokens_code_shaped')
        self.assertEqual(A.token_structure('I50.2|I10'),'all_split_tokens_code_shaped')
        self.assertEqual(A.token_structure('I50.2,'),'empty_token_review')
        self.assertEqual(A.token_structure('description I50.2'),'unresolved_tokens_review')

    def test_latest_echo_missingness_and_ties_not_hidden_by_older_ef(self):
        db=sqlite3.connect(':memory:'); self.addCleanup(db.close); A.init_db(db)
        bucket=A.ARMS[0]
        db.executemany('INSERT INTO meds VALUES (?,?,?)',[(bucket,'A','2024-06-01'),(bucket,'B','2024-06-01')])
        db.execute('INSERT INTO med_years VALUES (?,?,?)',(bucket,'A','2024'))
        def r(day,ef): return dict(MRN='A',EchoDate=day,EF=ef,AccessionNumber=day+str(ef))
        A.echo_records([r('2024-03-01',35),r('2024-05-01',None),r('2024-05-01',60),
            r('2024-02-01',20),r('2024-06-01',40),r('2024-07-01',30)],db,{})
        report=A.calendar_report(db)[bucket]['first_candidate_anchor_years'][0]
        self.assertEqual(report['candidate_patient_keys'],2)
        self.assertEqual(report['nearest_prior_candidate_ef_recency'],{'days_1_90':1,'no_prior_candidate_ef':1})
        self.assertEqual(report['latest_prior_echo_ef_bands'],{'same_latest_day_band_disagreement':1,'no_prior_echo':1})
        self.assertNotIn('2024-06-01',json.dumps(report))

    def test_terminal_empty_line_is_explicit_and_counted(self):
        for ending in ('\n','\r\n'):
            with self.subTest(ending=repr(ending)), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'dx.txt'; p.write_bytes(('PAT_MRN_ID\tDX_DATE\nA\t2024-01-01\n'+ending).encode())
                schema=A.inspect(p.parent,p.name)['schema_sha256']; before=p.read_bytes()
                with self.assertRaises(A.CountError): list(A.literal_rows(p,schema,{}))
                r={}; self.assertEqual(len(list(A.literal_rows(p,schema,r,allow_terminal_empty_line=True))),1)
                self.assertEqual(r['rows_read'],1); self.assertEqual(r['physical_lines_read'],2)
                self.assertEqual(r['terminal_empty_lines_accepted'],1); self.assertTrue(r['reached_eof'])
                self.assertEqual(p.read_bytes(),before)
                r={}; list(A.literal_rows(p,schema,r,limit=1,allow_terminal_empty_line=True))
                self.assertFalse(r['reached_eof']); self.assertEqual(r['terminal_empty_lines_accepted'],0)

    def test_terminal_policy_rejects_nonempty_interior_and_multiple_blanks(self):
        for tail in (' \n','\t\nEXTRA\n','\nB\t2024-01-02\n','\n\n','\ufeff\n','\r\r\n','BAD\n'):
            with self.subTest(tail=repr(tail)), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'dx.txt'; p.write_bytes(('PAT_MRN_ID\tDX_DATE\nA\t2024-01-01\n'+tail).encode())
                schema=A.inspect(p.parent,p.name)['schema_sha256']
                with self.assertRaises(A.CountError): list(A.literal_rows(p,schema,{},allow_terminal_empty_line=True))

    def test_terminal_policy_is_source_specific_and_opt_in(self):
        h='CarDS_2435227_Hosp_Enc_DX.txt'; o='CarDS_2435227_Outpatient_Enc_DX.txt'
        self.assertFalse(A.terminal_policy(h)); self.assertFalse(A.terminal_policy(o))
        self.assertTrue(A.terminal_policy(h,hospital=True))
        self.assertFalse(A.terminal_policy(o,hospital=True))
        self.assertFalse(A.terminal_policy(h,outpatient=True))
        self.assertTrue(A.terminal_policy(o,outpatient=True))
        self.assertFalse(A.terminal_policy('CarDS_2435227_Meds.txt',True,True))
        self.assertFalse(A.terminal_policy('unreviewed.txt',True,True))

    def test_cached_dates_preserve_parser_and_bound_retention(self):
        A._cached_date.cache_clear()
        values=['2024-01-01','2024-01-01 12:34','NULL','02/03/2024','2024-01-01T12:34Z','bad','x'*129]
        for _ in range(2):
            for value in values: self.assertEqual(A.cached_date(value),A.parse(value))
        self.assertEqual(A._cached_date.cache_info().currsize,6)
        self.assertEqual(A._cached_date.cache_info().maxsize,32768)
        self.assertGreater(A._cached_date.cache_info().hits,0)
        A._cached_date.cache_clear()

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
