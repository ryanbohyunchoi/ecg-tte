#!/usr/bin/env python3
"""Step 2: frozen CLMBR-T inference on the MIMIC MEDS extract, with the Yale checkpoint, runtime and settings.

Run with the mosaic env exactly as scripts/run_trial_pipeline.sh does:
  CUDA_VISIBLE_DEVICES=<free GPU, never 7> LD_PRELOAD=$MOS/lib/libstdc++.so.6 $MOS/bin/python encode_mimic_clmbr.py \
      --meds-root <OUT>/meds --model-root /mnt/raid0/eo287/clmbr --numeric-mode code-only --max-tokens 4096 \
      --limit 0 --output-dir <OUT>/clmbr/<run>

Same as scripts/encode_comet_clmbr.py (whose functions are imported: config report, strict safetensors loading, error
frames, people streaming): femr 0.2.3 / meds 0.1.3 pinned, FEMRTokenizer + FEMRBatchProcessor, torch seed 20260923,
last max_tokens tokens after tokenization, the latest retained token representation (768-d), raw vectors.
Differences, both forced by MIMIC and recorded in summary.json:
  1. cutoff = the exact time zero (index_datetime), not index-date midnight (MIMIC t0 is an in-hospital timestamp;
     the MEDS extract holds only events strictly before it, checked again here);
  2. a subject with no tokenizer-supported clinical event is encoded from its birth event alone (a demographics-only
     embedding) instead of being skipped, so every analysed patient keeps an embedding (queue Step 2.4).
"""
import argparse
from collections import Counter
from datetime import timezone
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from build_shared_tables import atomic_json, digest  # noqa: E402
from encode_comet_clmbr import (InputError, load_exact_safetensors, resolved_config_report, safe_error_frames,  # noqa: E402
                                stream_people)

VERSION = 'mimic_clmbr_embeddings_v1'
MEDS_VERSION = 'mimic_meds_v1'
BIRTH = 'MEDS_BIRTH'


def verify_inputs(root):
    s = json.loads((root / 'summary.json').read_text())
    m = json.loads((root / 'manifest.json').read_text())
    if s.get('version') != MEDS_VERSION or s.get('status') != 'complete_cohort_meds' or m.get('version') != MEDS_VERSION:
        raise InputError('complete_meds_required')
    for n, h in m['outputs'].items():
        if digest(root / n) != h:
            raise InputError('meds_artifact_changed')
    roster = pq.read_table(root / 'restricted_cohort.parquet').to_pylist()
    if len({r['subject_id'] for r in roster}) != len(roster):
        raise InputError('duplicate_subject')
    return roster, m


def patient_events(rows, t0, birth_code):
    events = []
    for timestamp, group in itertools.groupby(rows, key=lambda r: r['time']):
        if timestamp is None or timestamp.tzinfo is not None or timestamp >= t0:
            raise InputError('non_preindex_event')
        events.append({'time': timestamp, 'measurements': [{'code': birth_code if r['code'] == BIRTH else r['code']} for r in group]})
    if any(a['time'] > b['time'] for a, b in zip(events, events[1:])):
        raise InputError('unsorted_events')
    return events


def select_vector(reps, timestamps, patient_ids, subject_id, t0, expected_dim):
    reps, timestamps, patient_ids = np.asarray(reps), np.asarray(timestamps), np.asarray(patient_ids)
    cutoff = t0.replace(tzinfo=timezone.utc).timestamp()
    if reps.ndim != 2 or reps.shape[1] != expected_dim or len(reps) != len(timestamps) or len(reps) != len(patient_ids) or not len(reps):
        raise InputError('representation_shape_invalid')
    if not np.all(patient_ids == subject_id) or not np.all(timestamps < cutoff) or np.any(np.diff(timestamps) < 0):
        raise InputError('representation_identity_or_cutoff_invalid')
    v = reps[-1].astype(np.float32)
    if not np.all(np.isfinite(v)) or np.linalg.norm(v) == 0:
        raise InputError('invalid_vector')
    return v


def encode(root, model_root, output, numeric_mode, max_tokens=4096, limit=100):
    if numeric_mode != 'code-only':
        raise InputError('code_only_required')
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    start = time.monotonic()
    s = dict(version=VERSION, status='running', counts_valid=False, numeric_mode=numeric_mode, max_tokens=max_tokens, limit=limit,
             loader_revision='direct_safetensors_v1', execution_stage='verify_meds',
             policy='As scripts/encode_comet_clmbr.py: frozen local model; latest retained token representation; last max_tokens '
                    'after FEMR tokenization; raw vectors. Cutoff = exact time zero; birth-only subjects encoded (demographics-only).')
    atomic_json(output / 'summary.json', s)
    try:
        roster, manifest = verify_inputs(root)
        meds_manifest_hash = digest(root / 'manifest.json')
        by_id = {r['subject_id']: r for r in roster}
        if limit:  # deterministic arm-balanced smoke selection (as Yale)
            arms = sorted({r['treatment_arm'] for r in roster})
            ordered = {a: iter(sorted(r['subject_id'] for r in roster if r['treatment_arm'] == a)) for a in arms}
            selected = []
            while len(selected) < min(limit, len(roster)):
                for a in arms:
                    pid = next(ordered[a], None)
                    if pid is not None and len(selected) < limit:
                        selected.append(pid)
            targets = set(selected)
        else:
            targets = set(by_id)
        s['execution_stage'] = 'runtime_imports'
        versions = {p: importlib.metadata.version(p) for p in ('femr', 'meds', 'torch', 'transformers', 'xformers', 'numpy', 'pyarrow')}
        s['runtime'] = versions
        if versions['femr'] != '0.2.3' or versions['meds'] != '0.1.3':
            raise InputError('requires_femr_0_2_3_and_meds_0_1_3')
        import torch
        import meds
        from femr.models.tokenizer import FEMRTokenizer
        from femr.models.processor import FEMRBatchProcessor
        from femr.models.transformer import FEMRModel
        from femr.models.config import FEMRModelConfig
        if not torch.cuda.is_available():
            raise InputError('cuda_required')
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        model_files = [model_root / n for n in ('config.json', 'dictionary.msgpack', 'model.safetensors')]
        hashes = {p.name: digest(p) for p in model_files}
        config = json.loads((model_root / 'config.json').read_text())
        resolved = FEMRModelConfig.from_pretrained(str(model_root), local_files_only=True)
        s.update(resolved_config_report(config, resolved))
        expected_dim = s['model_config']['hidden_size']
        if expected_dim != 768:
            raise InputError('expected_clmbr_t_768_dimensions')
        tokenizer = FEMRTokenizer.from_pretrained(str(model_root))
        if tokenizer.is_hierarchical:
            raise InputError('hierarchical_tokenizer_requires_explicit_ontology_contract')
        processor = FEMRBatchProcessor(tokenizer)
        torch.manual_seed(20260923)
        model = FEMRModel(resolved)
        s['checkpoint_loading'] = load_exact_safetensors(model, model_root / 'model.safetensors')
        model = model.eval().to('cuda')
        for parameter in model.parameters():
            parameter.requires_grad_(False)

        def move(x):
            if isinstance(x, dict):
                return {k: move(v) for k, v in x.items()}
            if isinstance(x, (list, tuple)):
                return type(x)(move(v) for v in x)
            return x.to('cuda') if torch.is_tensor(x) else x

        statuses, outputs, seen, totals = [], {}, set(), Counter()
        for path in sorted((root / 'data').glob('*.parquet')):
            vectors = []
            for pid, rows in stream_people(path):
                if pid not in targets:
                    continue
                if pid in seen:
                    raise InputError('subject_in_multiple_shards')
                seen.add(pid)
                r = by_id[pid]
                t0 = r['t0'].to_pydatetime() if hasattr(r['t0'], 'to_pydatetime') else r['t0']
                record = dict(subject_id=pid, patient_key=r['patient_key'], trial=r['trial'], pid=r['pid'], treatment_arm=r['treatment_arm'])
                s['execution_stage'] = 'prepare_patient_events'
                events = patient_events(rows, t0, meds.birth_code)
                if sum(m['code'] == meds.birth_code for e in events for m in e['measurements']) != 1:
                    raise InputError('birth_event_missing_or_duplicated')
                attempted = accepted = 0
                tokenizer.start_patient()
                for e in events:
                    for m in e['measurements']:
                        if m['code'] == meds.birth_code:
                            continue
                        attempted += 1
                        if tokenizer.get_feature_codes(e['time'], m)[0]:
                            accepted += 1
                totals['clinical_measurements'] += attempted
                totals['accepted_clinical_measurements'] += accepted
                if not accepted:  # difference 2: birth-only (demographics-only) embedding
                    events = [e for e in events if any(m['code'] == meds.birth_code for m in e['measurements'])]
                    events[0]['measurements'] = [m for m in events[0]['measurements'] if m['code'] == meds.birth_code]
                patient = {'patient_id': pid, 'events': events}
                s['execution_stage'] = 'tokenize_patient'
                preliminary = processor.convert_patient(patient)
                n = int(preliminary['transformer']['valid_tokens'].sum())
                if n < 1:
                    raise InputError('no_tokens')
                raw = processor.convert_patient(patient, offset=max(0, n - max_tokens), max_length=max_tokens, tensor_type='pt')
                s['execution_stage'] = 'model_forward'
                with torch.inference_mode():
                    _, result = model(**move(processor.collate([raw])))
                v = select_vector(result['representations'].detach().cpu().numpy(), result['timestamps'].detach().cpu().numpy(),
                                  result['patient_ids'].detach().cpu().numpy(), pid, t0, expected_dim)
                vectors.append(dict(record, embedding=v.tolist()))
                st = 'encoded' if accepted else 'encoded_birth_only'
                statuses.append(dict(record, status=st, tokens_available=n, tokens_retained=min(n, max_tokens),
                                     attempted=attempted, accepted=accepted))
                totals[st] += 1
                totals['truncated_patients'] += int(n > max_tokens)
                if (totals['encoded'] + totals['encoded_birth_only']) % 2000 == 0:
                    print('Encoded patients:', totals['encoded'] + totals['encoded_birth_only'], flush=True)
            if vectors:
                dest = output / ('restricted_embeddings_' + path.stem + '.parquet')
                pq.write_table(pa.Table.from_pylist(vectors), dest, compression='zstd')
                outputs[dest.name] = digest(dest)
            atomic_json(output / 'progress.json', dict(encoded=len(seen), target_patients=len(targets), completed_partitions=len(outputs)))
        if targets - seen:
            raise InputError('target_subject_without_meds_rows')
        pq.write_table(pa.Table.from_pylist(statuses), output / 'restricted_patient_status.parquet')
        outputs['restricted_patient_status.parquet'] = digest(output / 'restricted_patient_status.parquet')
        if hashes != {p.name: digest(p) for p in model_files}:
            raise InputError('model_changed')
        if digest(root / 'manifest.json') != meds_manifest_hash:
            raise InputError('meds_changed')
        atomic_json(output / 'manifest.json', dict(version=VERSION, meds_manifest_sha256=meds_manifest_hash, model_sha256=hashes,
                                                   runtime=versions, outputs=outputs, numeric_mode=numeric_mode, max_tokens=max_tokens))
        s['execution_stage'] = 'complete'
        s.update(status='complete_smoke' if limit else 'complete_embeddings', counts_valid=True, target_patients=len(targets),
                 embedding_dimension=expected_dim, totals=dict(totals), model_sha256=hashes,
                 status_by_arm={a: dict(Counter(r['status'] for r in statuses if r['treatment_arm'] == a)) for a in sorted({r['treatment_arm'] for r in statuses})})
    except importlib.metadata.PackageNotFoundError as exc:
        s.update(status='failed_encoding', counts_valid=False, error_type=type(exc).__name__, reason='required_runtime_package_missing')
    except Exception as exc:
        s.update(status='failed_encoding', counts_valid=False, error_type=type(exc).__name__,
                 reason=str(exc) if isinstance(exc, InputError) else 'runtime_failure_no_raw_error_emitted',
                 diagnostic_frames=safe_error_frames(exc))
    s['elapsed_seconds'] = round(time.monotonic() - start, 3)
    atomic_json(output / 'summary.json', s)
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('meds-root', 'model-root', 'output-dir'):
        p.add_argument('--' + arg, type=Path, required=True)
    p.add_argument('--numeric-mode', choices=['native', 'code-only'], required=True)
    p.add_argument('--max-tokens', type=int, default=4096)
    p.add_argument('--limit', type=int, default=100, help='0 for the full extract; default 100 is the smoke test')
    a = p.parse_args()
    s = encode(a.meds_root, a.model_root, a.output_dir, a.numeric_mode, a.max_tokens, a.limit)
    print('Finished:', s['status'], {k: s.get(k) for k in ('totals', 'reason', 'diagnostic_frames', 'elapsed_seconds')})
    return 0 if s['counts_valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
