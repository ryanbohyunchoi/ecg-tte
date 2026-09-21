import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_clinical_shared_tables as C
import build_shared_tables as B

class ClinicalBuildTests(unittest.TestCase):
    def test_exact_real_inventory_no_labs_or_missing_patients_probe(self):
        selected=[r for r in C.sources() if r[1] in C.DOMAINS]
        self.assertEqual({r[0] for r in selected},C.EXPECTED)
        self.assertEqual(len(selected),8)
        calls=[]
        def header(root,relative):
            calls.append(relative)
            return dict(status='header_candidate',delimiter='tab',schema_sha256=next(r[2] for r in selected if r[0]==relative),columns=['PAT_MRN_ID'])
        with patch.object(C,'inspect',side_effect=header):specs=C.clinical_sources(Path('/synthetic'))
        self.assertEqual(set(calls),C.EXPECTED)
        self.assertFalse(any('Labs' in r for r in calls))
        self.assertEqual(len({s['id'] for s in specs}),8)
        self.assertTrue(all(s['selection_driver_sha256'] for s in specs))
    def test_inventory_and_schema_fail_before_build(self):
        with patch.object(C,'sources',return_value=[]),patch.object(C,'inspect') as inspect:
            with self.assertRaisesRegex(B.BuildError,'inventory_changed'):C.clinical_sources(Path('/synthetic'))
            inspect.assert_not_called()
        with patch.object(C,'inspect',return_value=dict(status='header_candidate',delimiter='tab',schema_sha256='wrong')):
            with self.assertRaisesRegex(B.BuildError,'schema_mismatch'):C.clinical_sources(Path('/synthetic'))
    def test_independent_complete_snapshot_with_absent_labs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();relative='Data-2025-04-03/CarDS_2435227_Patients.txt'
            path=raw/relative;path.parent.mkdir();path.write_text('PAT_MRN_ID\tBIRTH_DATE\nA\t1980-01-01\n\n')
            schema=B.inspect(raw,relative)['schema_sha256']
            selected=[(relative,'patients',schema),('missing_Labs.txt','labs_2025','not-read')]
            with patch.object(C,'sources',return_value=selected),patch.object(C,'EXPECTED',{relative}):specs=C.clinical_sources(raw,True)
            out=root/'clinical'
            with contextlib.redirect_stdout(io.StringIO()):r=B.build(specs,out)
            self.assertEqual(r['status'],'complete')
            source_id=specs[0]['id'];self.assertEqual(r['stages'][source_id]['terminal_empty_lines'],1)
            self.assertEqual(B.open_table(out,source_id).to_table()['__patient_key'].to_pylist(),['A'])
            with self.assertRaises(FileExistsError):B.build(specs,out)
            with patch.object(B,'build_stage',side_effect=AssertionError('should reuse')),contextlib.redirect_stdout(io.StringIO()):B.build(specs,out,resume=True)
            changed=[dict(specs[0],selection_driver_sha256='changed')]
            with self.assertRaisesRegex(B.BuildError,'incompatible_resume'):B.build(changed,out,resume=True)
    def test_bad_clinical_row_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();relative='Data-2025-04-03/CarDS_2435227_Patients.txt'
            path=raw/relative;path.parent.mkdir();path.write_text('PAT_MRN_ID\tBIRTH_DATE\nA\t1980-01-01\nBAD\n')
            schema=B.inspect(raw,relative)['schema_sha256']
            with patch.object(C,'sources',return_value=[(relative,'patients',schema)]),patch.object(C,'EXPECTED',{relative}):specs=C.clinical_sources(raw,True)
            with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(B.BuildError):B.build(specs,root/'out')
            self.assertEqual(json.loads((root/'out'/'summary.json').read_text())['status'],'failed')
            with self.assertRaises(B.BuildError):B.open_table(root/'out',specs[0]['id'])

if __name__=='__main__':unittest.main()
