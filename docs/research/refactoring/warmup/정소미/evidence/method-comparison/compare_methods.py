#!/usr/bin/env python3
"""Fresh verification of a frozen pool, then retrospective evaluation-method comparison."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import platform
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
sys.path.insert(0, str(EVIDENCE / 'reproducibility'))
import run_replay as replay


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def measure(stage, repos_path, output):
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new, empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'logs').mkdir()
    protocol = json.loads((HERE / 'protocol.json').read_text())
    save(output / 'protocol.json', protocol)
    inputs = protocol['inputs']
    repos = {k: Path(v).resolve() for k, v in json.loads(repos_path.read_text()).items()}
    manifest = {'started_utc': datetime.now(timezone.utc).isoformat(), 'stage': stage,
                'system': platform.platform(), 'python': platform.python_version(),
                'protocol_sha256': sha(HERE / 'protocol.json'),
                'scripts_sha256': {str(p.relative_to(EVIDENCE)): sha(p) for p in
                    [Path(__file__), EVIDENCE / 'reproducibility/run_replay.py',
                     EVIDENCE / 'verify_candidate.py', EVIDENCE / 'proof_tokens.py']},
                'environments': {}}
    for env in sorted({x['environment'] for x in inputs}):
        spec = protocol['environments'][env]
        manifest['environments'][env] = replay.check_environment(repos[env], spec)
        if sha(EVIDENCE / spec['statement']) != spec['statement_sha256']:
            raise ValueError('Statement hash mismatch')
    for x in inputs:
        if sha(EVIDENCE / x['path']) != x['sha256']:
            raise ValueError(f"Input hash mismatch: {x['path']}")
    random.Random(protocol['order_seed']).shuffle(inputs)
    manifest['execution_order'] = [f"P{x['problem']}-{x['id']}" for x in inputs]
    save(output / 'environment.json', manifest)
    records = []
    for x in inputs:
        tag = f"P{x['problem']}-{x['id']}"
        spec = protocol['environments'][x['environment']]
        result = replay.run_one(repos[x['environment']], spec, EVIDENCE / x['path'],
                                tag, protocol['timeout_seconds'], output / 'logs' / f'{tag}.log',
                                protocol['expected_axioms'])
        result.update(problem=x['problem'], candidate_id=x['id'], role=x['role'],
                      environment=x['environment'], input_path=x['path'], input_sha256=x['sha256'])
        records.append(result)
        save(output / 'results.json', records)
        print(f"{tag}: {result['status']}; L={result.get('proof_tokens')}; "
              f"HB={result.get('heartbeat', {}).get('heartbeats')}", flush=True)
    manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
    save(output / 'environment.json', manifest)
    # Historical invalid attempts are experimental inputs, not a runner error.
    if any(r['role'] == 'reference' and not r['accepted'] for r in records):
        raise RuntimeError('Reference failed; do not interpret candidate metrics')


def analyze(pool, output):
    output.mkdir(parents=True, exist_ok=True)
    protocol = json.loads((HERE / 'protocol.json').read_text())
    measured = json.loads((pool / 'results.json').read_text())
    expected = {(x['problem'], x['id']) for x in protocol['inputs'] if x['problem'] in protocol['pool_problems']}
    if {(r['problem'], r['candidate_id']) for r in measured} != expected or len(measured) != len(expected):
        raise ValueError('Pool missing or duplicated measurements')
    metrics, policy_rows, budget_rows, frontier_rows, intervals = [], [], [], [], []
    for problem in protocol['pool_problems']:
        runs = [r for r in measured if r['problem'] == problem]
        reference = next(r for r in runs if r['role'] == 'reference')
        assert reference['accepted']
        L0, H0 = reference['proof_tokens'], reference['heartbeat']['heartbeats']
        candidates = [r for r in runs if r['role'] == 'candidate']
        valid = [r for r in candidates if r['accepted']]
        for field, baseline in [('length', L0), ('heartbeat', H0)]:
            value = lambda r: r['proof_tokens'] if field == 'length' else r['heartbeat']['heartbeats']
            signed = [(1 - value(r) / baseline) if r['accepted'] else 0.0 for r in candidates]
            conditional = [1 - value(r) / baseline for r in valid]
            metrics.append({'problem': problem, 'metric': field, 'attempts': len(candidates),
                'valid': len(valid), 'failed': len(candidates)-len(valid),
                'valid_fraction': len(valid)/len(candidates),
                'improved_fraction_all_attempts': sum(v > 0 for v in signed)/len(candidates),
                'valid_only_mean_improvement': statistics.mean(conditional),
                'failure_inclusive_mean_improvement': statistics.mean(signed),
                'denominator_gap_percentage_points': 100*(statistics.mean(conditional)-statistics.mean(signed))})
            # Exhaustive subsets of this finite, adaptive historical pool: no IID inference.
            effective = [min(baseline, value(r)) if r['accepted'] else baseline for r in candidates]
            for k in sorted(set(protocol['k_values'] + [len(candidates)])):
                if k > len(candidates):
                    continue
                count = math.comb(len(candidates), k)
                average_min = sum(min(s) for s in itertools.combinations(effective, k)) / count
                budget_rows.append({'problem': problem, 'metric': field, 'pool_size': len(candidates),
                    'k': k, 'subsets': count, 'expected_min_at_k': average_min,
                    'expected_red_at_k': 1 - average_min / baseline})
        def cost(r, w):
            return w*r['proof_tokens']/L0 + (1-w)*r['heartbeat']['heartbeats']/H0
        def choose(w):
            return min(valid + [reference], key=lambda r: (cost(r,w), r['proof_tokens'], r['heartbeat']['heartbeats'], r['candidate_id']))
        for name, w in [('length_only',1.0),('heartbeat_only',0.0),('equal_normalized_length_heartbeat',0.5)]:
            r = choose(w)
            policy_rows.append({'problem':problem,'policy':name,'length_weight':w,'selected':r['candidate_id'],
                'proof_tokens':r['proof_tokens'],'heartbeat':r['heartbeat']['heartbeats'],
                'length_reduction':1-r['proof_tokens']/L0,'heartbeat_reduction':1-r['heartbeat']['heartbeats']/H0,
                'joint_reduction':1-cost(r,0.5)})
        for r in valid:
            l,h=r['proof_tokens'],r['heartbeat']['heartbeats']
            dominated=any(s['proof_tokens']<=l and s['heartbeat']['heartbeats']<=h and
                (s['proof_tokens']<l or s['heartbeat']['heartbeats']<h) for s in valid)
            if not dominated:
                frontier_rows.append({'problem':problem,'candidate':r['candidate_id'],'proof_tokens':l,'heartbeat':h})
        # All pairwise crossings delimit intervals on which the linear selector is constant.
        points={0.0,1.0}
        for a,b in itertools.combinations(valid+[reference],2):
            da=(a['proof_tokens']-b['proof_tokens'])/L0
            db=(a['heartbeat']['heartbeats']-b['heartbeat']['heartbeats'])/H0
            if da != db:
                w=-db/(da-db)
                if 0<w<1: points.add(w)
        edges=sorted(points)
        for lo,hi in zip(edges,edges[1:]):
            chosen=choose((lo+hi)/2)['candidate_id']
            if intervals and intervals[-1]['problem']==problem and intervals[-1]['selected']==chosen:
                intervals[-1]['length_weight_high']=hi
            else:
                intervals.append({'problem':problem,'length_weight_low':lo,'length_weight_high':hi,'selected':chosen})
    for name,rows in [('failure_accounting',metrics),('selection',policy_rows),('budget_curve',budget_rows),
                       ('pareto_frontier',frontier_rows),('weight_intervals',intervals)]:
        write_csv(output/f'{name}.csv',rows)
        save(output/f'{name}.json',rows)
    summary={'pool_attempts':sum(r['role']=='candidate' for r in measured),
             'pool_valid':sum(r['role']=='candidate' and r['accepted'] for r in measured),
             'pool_reference_runs':sum(r['role']=='reference' for r in measured),
             'limitations':['adaptive historical pool, not IID samples','two pool problems',
                            'one fresh verification per candidate','no model or full algorithm comparison'],
             'pool_results_sha256':sha(pool/'results.json')}
    save(output/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['pool','analyze'])
    p.add_argument('--repos',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--pool',type=Path)
    a=p.parse_args()
    if a.action=='analyze':
        if not a.pool: p.error('--pool is required')
        analyze(a.pool,a.output)
    else:
        if not a.repos: p.error('--repos is required')
        measure(a.action,a.repos,a.output)


if __name__=='__main__':
    main()
