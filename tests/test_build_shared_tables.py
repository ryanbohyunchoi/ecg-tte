import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_shared_tables as B

class SharedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.src=self.base/'source';self.src.mkdir()
        self.out=self.base/'shared'

    def text_spec(self,name='medication_orders',body=None,terminal=False,expected=2):
        path=self.src/(name+'.txt')
        path.write_bytes(b'PAT_MRN_ID\tORDER_INST\tTEXT\n'+(body if body is not None else b' A001 \t2024-01-01 12:34\t"quoted"suffix\n001\tNULL\tSECRET_SYNTHETIC\n'))
        return dict(id=name,path=str(path),format='literal_tabs',schema_hash=B.inspect(self.src,path.name)['schema_sha256'],
                    expected_rows=expected,key='PAT_MRN_ID',terminal_empty=terminal,dates=['ORDER_INST'])

    def build(self,specs,resume=False):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):r=B.build(specs,self.out,resume,batch_rows=1)
        self.assertNotIn('SECRET',out.getvalue())
        return r

    def test_lossless_values_typed_days_and_manifest_reader(self):
        s=self.text_spec();before=Path(s['path']).read_bytes();r=self.build([s])
        self.assertEqual(r['status'],'complete')
        table=B.open_table(self.out,s['id'],verify_hashes=True).to_table().to_pydict()
        self.assertEqual(table['PAT_MRN_ID'],[' A001 ','001'])
        self.assertEqual(table['__patient_key'],['A001','001'])
        self.assertEqual(table['TEXT'],['"quoted"suffix','SECRET_SYNTHETIC'])
        self.assertEqual(table['__source_row'],[1,2]);self.assertIsNone(table['__day_ORDER_INST'][1])
        self.assertEqual(table['ORDER_INST'][1],'NULL')
        self.assertEqual(Path(s['path']).read_bytes(),before)
        self.assertNotIn('SECRET',(self.out/'manifest.json').read_text())
        with self.assertRaises(FileExistsError):self.build([s])

    def test_terminal_blank_counted_but_not_data(self):
        s=self.text_spec(body=b'A\t2024-01-01\tx\r\n\r\n',terminal=True,expected=1)
        r=self.build([s]);stage=r['stages'][s['id']]
        self.assertEqual(stage['rows'],1);self.assertEqual(stage['physical_lines'],2)
        self.assertEqual(stage['terminal_empty_lines'],1)
        self.assertEqual(stage['source_sha256'],B.digest(Path(s['path'])))

    def test_interior_blank_fails_and_reader_refuses_partial(self):
        s=self.text_spec(body=b'A\t2024-01-01\tx\n\nB\t2024-01-02\ty\n',terminal=True)
        with self.assertRaises(B.BuildError):self.build([s])
        self.assertEqual(json.loads((self.out/'manifest.json').read_text())['status'],'failed')
        with self.assertRaises(B.BuildError):B.open_table(self.out,s['id'])
        self.assertFalse((self.out/s['id']).exists())

    def test_parquet_preserves_all_columns_and_numeric_ef(self):
        path=self.src/'echo.parquet'
        raw=pa.table({'MRN':['001','A001'],'EchoDate':['2024-01-01','02/03/2024'],
                      'EF':pa.array([35.,None],type=pa.float64()),'extra':['keep','SECRET_SYNTHETIC']})
        pq.write_table(raw,path)
        s=dict(id='echo_studies',path=str(path),format='parquet',schema_fields=[(f.name,str(f.type)) for f in raw.schema],
               expected_rows=2,key='MRN',terminal_empty=False,dates=['EchoDate'])
        self.build([s]);got=B.open_table(self.out,s['id']).to_table().to_pydict()
        for c in raw.column_names:self.assertEqual(got[c],raw.to_pydict()[c])
        self.assertIsNone(got['__day_EchoDate'][1]);self.assertEqual(got['__date_status_EchoDate'][1],'slash_day_month_ambiguous_not_compared')

    def test_resume_preserves_complete_stage_and_restarts_only_incomplete(self):
        first=self.text_spec('first');second=self.text_spec('second',body=b'bad\n')
        with self.assertRaises(B.BuildError):self.build([first,second])
        part=self.out/'first'/'part-00000.parquet';stamp=part.stat().st_mtime_ns
        Path(second['path']).write_bytes(Path(first['path']).read_bytes())
        with patch.object(B,'build_stage',wraps=B.build_stage) as call:
            self.build([first,second],resume=True)
            self.assertEqual(call.call_count,1);self.assertEqual(call.call_args.args[0]['id'],'second')
        self.assertEqual(part.stat().st_mtime_ns,stamp)
        self.assertEqual(len(list(self.out.glob('.incomplete-second-*'))),1)
        self.build([first,second],resume=True)

    def test_corrupt_part_and_changed_source_rejected_on_resume(self):
        s=self.text_spec();self.build([s]);part=self.out/s['id']/'part-00000.parquet'
        original=part.read_bytes();part.write_bytes(original[:-1]+b'X')
        with self.assertRaises(B.BuildError):self.build([s],resume=True)
        part.write_bytes(original)
        Path(s['path']).write_bytes(Path(s['path']).read_bytes().replace(b'A001',b'A002'))
        with self.assertRaises(B.BuildError):self.build([s],resume=True)

    def test_schema_and_expected_count_stop(self):
        s=self.text_spec(expected=3)
        with self.assertRaisesRegex(B.BuildError,'expected_rows_mismatch'):self.build([s])
        self.assertFalse((self.out/s['id']).exists())

    def test_source_changed_mid_build_not_published(self):
        s=self.text_spec();original=B.enriched
        def mutate(*args):
            result=original(*args)
            with Path(s['path']).open('ab') as f:f.write(b'X')
            return result
        with patch.object(B,'enriched',side_effect=mutate):
            with self.assertRaises(B.BuildError):self.build([s])
        self.assertFalse((self.out/s['id']).exists())

    def test_incompatible_resume_preserves_manifest(self):
        s=self.text_spec();self.build([s]);before=(self.out/'manifest.json').read_bytes()
        with self.assertRaisesRegex(B.BuildError,'incompatible_resume_contract'):
            B.build([s],self.out,resume=True,batch_rows=2)
        self.assertEqual(before,(self.out/'manifest.json').read_bytes())

    def test_same_stat_source_change_detected_by_resume_hash(self):
        s=self.text_spec();self.build([s]);p=Path(s['path']);stat=p.stat()
        p.write_bytes(p.read_bytes().replace(b'A001',b'A002'))
        os.utime(p,ns=(stat.st_atime_ns,stat.st_mtime_ns))
        with self.assertRaisesRegex(B.BuildError,'source_changed_resume'):self.build([s],resume=True)

    def test_symlink_source_rejected_and_summary_has_no_values(self):
        s=self.text_spec();self.build([s])
        summary=json.loads((self.out/'summary.json').read_text())
        self.assertEqual(summary['status'],'complete')
        self.assertFalse(summary['clinical_semantics_validated'])
        self.assertNotIn('SECRET',json.dumps(summary))
        link=self.src/'link.txt';link.symlink_to(s['path']);s['path']=str(link)
        with self.assertRaises(B.BuildError): B.build([s],self.base/'other')

    def test_source_overlap_rejected(self):
        s=self.text_spec()
        with self.assertRaises(B.BuildError):B.build([s],self.src/'output')
        self.assertFalse((self.src/'output').exists())

if __name__=='__main__':unittest.main()
