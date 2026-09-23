import sys
from pathlib import Path
from datetime import datetime, date, timezone
import json
import tempfile
import unittest
from types import SimpleNamespace
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_shared_tables import digest
from build_comet_meds import build, DOMAINS, BIRTH, event_time
from encode_comet_clmbr import verify_inputs,patient_events,select_vector,resolved_config_report
from audit_comet_clmbr_inputs import InputError

class MedsPipelineTests(unittest.TestCase):
    def fixture(self,root):
        src=root/'source';src.mkdir();gold=root/'gold';gold.mkdir()
        rows=[dict(patient_key='privateA',treatment_arm='carvedilol_candidate',index_date=date(2020,1,2)),dict(patient_key='privateB',treatment_arm='metoprolol_tartrate_candidate',index_date=date(2020,1,2))]
        p=src/'restricted_cleaned_baseline.parquet';pq.write_table(pa.Table.from_pylist(rows),p)
        (src/'summary.json').write_text(json.dumps(dict(status='complete_mice_preparation',counts_valid=True,rows=2,denominators={'carvedilol_candidate':1,'metoprolol_tartrate_candidate':1})))
        (src/'manifest.json').write_text(json.dumps({'outputs':{p.name:digest(p)}}))
        (gold/'person').mkdir()
        pq.write_table(pa.table({'person_id':[1,2],'person_source_value':['privateA','privateB'],'birth_datetime':[datetime(1960,1,1),None],'gender_concept_id':[8507,8532]}),gold/'person'/'part.parquet')
        for domain,(cid,dates,value) in DOMAINS.items():
            (gold/domain).mkdir()
            data={'person_id':[1,1,1,2,3,1],cid:[10,10,99,10,10,0],dates[-1]:[date(2020,1,1),date(2020,1,2),date(2020,1,1),date(2020,1,1),date(2020,1,1),date(2020,1,1)]}
            if value:data.update({value:[3.2,float('inf'),None,4.1,2.2,None],'unit_source_value':['mg/dL']*6})
            pq.write_table(pa.table(data),gold/domain/'part.parquet')
        concept=root/'CONCEPT.csv';concept.write_text('concept_id\tvocabulary_id\tconcept_code\n10\tSNOMED\t1234\n')
        return src,gold,concept
    def test_build_cutoff_mapping_shards_values_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src,gold,concept=self.fixture(root);out=root/'out'
            result=build(src,gold,concept,out,2)
            self.assertEqual(result['status'],'complete_cohort_meds',result)
            self.assertEqual(result['rows'],11) # five clinical events each, one exact birth
            self.assertEqual(result['arm_coverage']['metoprolol_tartrate_candidate']['with_exact_birth'],0)
            self.assertNotIn('privateA',str(result))
            rows=[]; owners={}
            for p in (out/'data').glob('*.parquet'):
                r=pq.read_table(p).to_pylist();rows+=r
                self.assertEqual([(x['subject_id'],x['time']) for x in r],sorted((x['subject_id'],x['time']) for x in r))
                for pid in {x['subject_id'] for x in r}:
                    self.assertNotIn(pid,owners);owners[pid]=p
            self.assertTrue(all(r['time']<datetime(2020,1,2) for r in rows))
            self.assertEqual(sum(r['code']==BIRTH for r in rows),1)
            measurements=[r for r in rows if r['source_domain']=='measurement']
            self.assertTrue(all(r['numeric_value'] is not None and r['unit']=='mg/dL' for r in measurements))
            roster,manifest=verify_inputs(out);self.assertEqual(len(roster),2)
            p=out/'metadata'/'dataset.json';p.write_text('{}')
            with self.assertRaises(InputError):verify_inputs(out)
    def test_required_domain_stops_and_no_source_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src,gold,concept=self.fixture(root)
            (gold/'measurement'/'part.parquet').unlink()
            result=build(src,gold,concept,root/'out')
            self.assertFalse(result['counts_valid']);self.assertEqual(result['reason'],'required_gold_domain_missing')
    def test_event_adapter_numeric_and_time(self):
        row=dict(subject_id=1,time=datetime(2020,1,1),code='LOINC/1',numeric_value=4.5,unit='mg/dL')
        native=patient_events([row],date(2020,1,2),'SNOMED/birth','native')
        self.assertEqual(native[0]['measurements'][0]['numeric_value'],4.5)
        self.assertNotIn('numeric_value',patient_events([row],date(2020,1,2),'x','code-only')[0]['measurements'][0])
        with self.assertRaises(InputError):patient_events([row],date(2020,1,1),'x','native')
        self.assertIsNone(event_time('2020-01-01T00:00:00Z'))
    def test_representation_identity_and_no_future_fallback(self):
        t=datetime(2020,1,1,tzinfo=timezone.utc).timestamp()
        self.assertEqual(select_vector([[1,2],[3,4]],[t,t],[1,1],1,date(2020,1,2),2).tolist(),[3,4])
        for ids,times in [([2,2],[t,t]),([1,1],[t,t+86400])]:
            with self.assertRaises(InputError):select_vector([[1,2],[3,4]],times,ids,1,date(2020,1,2),2)


class ConfigResolutionTests(unittest.TestCase):
    def test_missing_serialized_default_not_missing_dimension(self):
        resolved=SimpleNamespace(transformer_config=SimpleNamespace(hidden_size=768,n_layers=12,n_heads=12,vocab_size=65536,attention_width=496,is_hierarchical=False))
        report=resolved_config_report({'transformer_config':{'n_layers':12,'vocab_size':65536}},resolved)
        self.assertIsNone(report['raw_model_config']['hidden_size'])
        self.assertEqual(report['model_config']['hidden_size'],768)
        self.assertIn('hidden_size',report['model_config_defaulted_fields'])
        self.assertNotIn('n_layers',report['model_config_defaulted_fields'])
    def test_explicit_dimensions_are_not_overridden(self):
        for value in (512,None):
            resolved=SimpleNamespace(transformer_config=SimpleNamespace(hidden_size=value))
            report=resolved_config_report({'transformer_config':{'hidden_size':value}},resolved)
            self.assertEqual(report['model_config']['hidden_size'],value)
            self.assertNotIn('hidden_size',report['model_config_defaulted_fields'])
