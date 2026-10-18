#!/usr/bin/env python3
"""Read-only publication checks. No model calls, Lean execution, or file writes.

Run with Python 3 on macOS/Linux. Prints JSON; optional shell redirection can
save it. Historical absolute paths in records are never opened by this script.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_runs(alias):
    rows = {}
    for line in (BASE / alias / 'measurements.jsonl').read_text().splitlines():
        item = json.loads(line)
        for blob in item['files'].values():
            assert digest(blob['text'].encode('utf-8')) == blob['sha256']
        result = json.loads(item['files']['result.json']['text'])
        assert result['proof_sha256'] == item['files']['proof.lean']['sha256']
        path = item['run_directory'] + '/result.json'
        assert path not in rows
        rows[path] = result
    return rows


def main():
    provenance = read(BASE / 'provenance.json')
    for relative, entry in provenance['files'].items():
        assert digest((BASE / relative).read_bytes()) == entry['sha256'], relative
    runs = {alias: load_runs(alias) for alias in provenance['experiments']}

    effort = read(BASE / 'effort-comparison/analysis/final-comparison.json')
    main_runs = [r for r in runs['effort-comparison'].values() if r['variant'] in {'high', 'xhigh', 'ultra'}]
    baselines = [r for r in main_runs if r['label'].startswith('baseline_')]
    finals = [r for r in main_runs if r['label'].startswith('final_')]
    candidates = [r for r in main_runs if r not in baselines and r not in finals]
    assert len(main_runs) == effort['totals']['main_verifier_runs'] == 315
    assert len(baselines) == 27 and len(finals) == 45 and len(candidates) == 243
    assert sum(r['valid'] for r in candidates) == 176
    for row in effort['rows']:
        assert digest((BASE/'effort-comparison'/row['selected_path']).read_bytes()) == row['proof_sha256']
        recorded = [runs['effort-comparison'][rel] for rel in row['final_runs']]
        assert len(recorded) == 5 and all(r['valid'] for r in recorded)
        assert all(r['proof_sha256'] == row['proof_sha256'] and r['proof_tokens'] == row['proof_tokens'] for r in recorded)
        assert [r['raw_heartbeats'] for r in recorded] == row['raw_heartbeats']['values']
        median = statistics.median(r['raw_heartbeats'] for r in recorded)
        assert median == row['raw_heartbeats']['median']
        baseline = [r for r in baselines if r['variant'] == row['arm'] and r['problem'] == row['problem']]
        assert statistics.median(r['raw_heartbeats'] for r in baseline) == row['baseline_median_raw_heartbeats']
        score = .5*(row['proof_tokens']/row['baseline_proof_tokens'] + median/row['baseline_median_raw_heartbeats'])
        assert math.isclose(score, row['score'], rel_tol=1e-12)
    winners = {str(n):min((r for r in effort['rows'] if r['problem'] == n), key=lambda r:r['score'])['arm'] for n in [1, 2, 3]}
    assert winners == {'1':'xhigh','2':'high','3':'ultra'}

    repeat = read(BASE/'high-repeat/analysis/comparison.json')
    assert len(runs['high-repeat']) == 42
    first, final = set(), set()
    for trial in repeat['trials']:
        name=trial['trial']; f=trial['final']
        assert digest((BASE/'high-repeat'/f['path']).read_bytes()) == f['exact_sha256']
        selected = [r for r in runs['high-repeat'].values() if r['variant'] == name and r['label'].startswith('final_')]
        attempts = [r for r in runs['high-repeat'].values() if r['variant'] == name and r['label'].startswith('attempt_')]
        assert len(attempts) == 8 and sum(r['valid'] for r in attempts) == trial['valid_candidates']
        assert len(selected) == 5 and all(r['valid'] and r['proof_sha256'] == f['exact_sha256'] for r in selected)
        assert sorted(r['raw_heartbeats'] for r in selected) == sorted(f['raw_heartbeats']['values'])
        score = .5*(f['proof_tokens']/repeat['baseline']['proof_tokens'] + statistics.median(r['raw_heartbeats'] for r in selected)/repeat['baseline']['median_raw_heartbeats'])
        assert math.isclose(score,f['local_score'],rel_tol=1e-12)
        first.add(trial['first_candidate']['exact_sha256']);final.add(f['exact_sha256'])
    assert len(first) == len(final) == 3

    # Invoke only the original pure recorded-replay path; never initialize or verify.
    spec=importlib.util.spec_from_file_location('archived_parent_harness',BASE/'controlled-harness/harness.py')
    harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
    replay=harness.replay()
    assert len(replay['checks']) == 9 and all(r['match'] for r in replay['checks'])
    assert replay == read(BASE/'controlled-harness/analysis/record-replay.json')
    live=read(BASE/'controlled-harness/analysis/live-replay.json')
    fields={key:sum(row['comparisons'][key] for row in live) for key in live[0]['comparisons']}
    assert fields['valid'] == 9 and fields['raw_heartbeats'] == 7
    for row in live:
        old=runs['controlled-harness'][f"{row['trial']}/runs/P02/step_{row['step']}/result.json"]
        new=runs['controlled-harness'][f"control/runs/P02/replay_{row['trial']}_{row['step']}/result.json"]
        assert old['raw_heartbeats'] == row['old_heartbeats'] and new['raw_heartbeats'] == row['new_heartbeats']
        assert (old['valid'] == new['valid']) == row['comparisons']['valid']
    summary=read(BASE/'controlled-harness/analysis/summary.json')
    for trial in summary['trials']:
        proof=BASE/'controlled-harness'/trial['trial']/'selected.lean'
        assert digest(proof.read_bytes()) == trial['best']['proof_sha256']
    state=read(BASE/'controlled-harness/analysis/live-state-comparison.json')
    assert sum(t['selected_proof_same'] for t in state) == 3
    assert sum(s['request_same'] for t in state for s in t['steps']) == 8
    return {'status':'passed','scope':'Publication integrity, score recomputation from saved measurements, and fresh recorded-state replay; no new Lean or model runs.',
            'files_hashed':len(provenance['files']),'measurement_records':{k:len(v) for k,v in runs.items()},
            'effort':{'main_runs':315,'candidate_attempts':243,'valid_candidates':176,'final_passes':45,'lowest_score_by_problem':winners},
            'high_repeat':{'trials':3,'distinct_first_proofs':3,'distinct_final_proofs':3,'final_passes':15},
            'controlled_harness':{'fresh_record_replay_matches':9,'historical_live_validity_matches':9,'historical_live_heartbeat_matches':7,'historical_same_selection':3,'historical_same_request':8},
            'new_model_calls':0,'new_lean_processes':0}


if __name__ == '__main__':
    print(json.dumps(main(),ensure_ascii=False,indent=2))
