import json
from pathlib import Path
import sys
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_comet_runs as C

class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.run=Path(self.tmp.name)/'comet-candidates-synthetic'
        self.report=self.run/'report';self.report.mkdir(parents=True)

    def completed(self):
        pq.write_table(pa.table({'patient_key':['SECRET_SYNTHETIC']}),self.report/'restricted_candidates.parquet')
        manifest=dict(version='comet_candidates_v1',rows=1,core_manifest_sha256='synthetic',
                      candidate_sha256=C.sha256(self.report/'restricted_candidates.parquet'))
        summary=dict(version='comet_candidates_v1',candidate_patient_keys=1,core_manifest_sha256='synthetic',
                     status='complete_provisional_candidates',counts_valid=True)
        (self.report/'summary.json').write_text(json.dumps(summary))
        (self.report/'restricted_manifest.json').write_text(json.dumps(manifest))

    def test_complete_hash_footer_and_no_values(self):
        self.completed();r=C.check(self.run)
        self.assertEqual(r['check'],'complete_candidate_artifact_verified')
        self.assertNotIn('SECRET',json.dumps(r));self.assertFalse(r['final_eligible_cohort'])

    def test_building_not_assumed_running_and_missing_summary(self):
        self.assertEqual(C.check(self.run)['check'],'no_saved_summary')
        (self.report/'summary.json').write_text('{"status":"building","counts_valid":false}')
        self.assertEqual(C.check(self.run)['check'],'not_complete_process_state_unknown')

    def test_missing_or_corrupt_artifact_is_not_success(self):
        self.completed();path=self.report/'restricted_candidates.parquet';path.unlink()
        self.assertEqual(C.check(self.run)['check'],'completion_artifact_missing')
        path.write_bytes(b'BROKEN')
        self.assertEqual(C.check(self.run)['check'],'candidate_hash_mismatch')

    def test_bad_json_and_mismatched_row_count(self):
        (self.report/'summary.json').write_text('bad')
        self.assertEqual(C.check(self.run)['check'],'check_failed_no_raw_error_export')
        self.completed();p=self.report/'restricted_manifest.json';m=json.loads(p.read_text());m['rows']=2;p.write_text(json.dumps(m))
        self.assertEqual(C.check(self.run)['check'],'row_count_mismatch')

if __name__=='__main__':unittest.main()
