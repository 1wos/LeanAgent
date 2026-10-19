#!/usr/bin/env python3
"""Aggregate stored verifier evidence without executing Lean or model calls."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import statistics

BASE = Path(__file__).resolve().parents[1]

def spread(values):
    values = [x for x in values if x is not None]
    if not values:
        return None
    return {'n': len(values), 'min': min(values), 'median': statistics.median(values),
            'max': max(values), 'unique_values': len(set(values))}

def collect():
    output = {'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'schedule': json.loads((BASE / 'schedule.json').read_text()),
              'interpretation': 'Single agent trajectory per reasoning effort. Lean repeats are not independent LLM trials.',
              'arms': {}}
    all_finals = {}
    for variant in ['high', 'xhigh', 'ultra']:
        records = []
        for p in sorted((BASE / variant / 'runs').glob('P*/*/result.json')):
            try:
                r = json.loads(p.read_text())
                r['result_path'] = str(p.relative_to(BASE))
                records.append(r)
            except (OSError, json.JSONDecodeError):
                pass
        arm = {'verification_count': len(records), 'valid_verification_count': sum(r.get('valid', False) for r in records),
               'problems': {}, 'earliest_verification_started_at': min((r['started_at'] for r in records), default=None),
               'latest_verification_finished_at': max((r['finished_at'] for r in records), default=None)}
        for number in [1, 2, 3]:
            original_hash = hashlib.sha256((BASE / f'common/P{number:02d}/reference.lean').read_bytes()).hexdigest()
            group = [r for r in records if r['problem'] == number]
            baseline = sorted((r for r in group if r['proof_sha256'] == original_hash and r.get('valid')),
                              key=lambda r: r['started_at'])[:3]
            candidates = [r for r in group if r['proof_sha256'] != original_hash]
            eligible = [r for r in group if r.get('valid')]
            result = {'verification_count': len(group), 'valid_verification_count': len(eligible),
                      'invalid_verification_count': len(group) - len(eligible),
                      'distinct_candidate_hashes': len({r['proof_sha256'] for r in candidates}),
                      'distinct_valid_candidate_hashes': len({r['proof_sha256'] for r in candidates if r.get('valid')}),
                      'baseline': {'proof_tokens': baseline[0]['proof_tokens'] if baseline else None,
                                   'raw_heartbeats': spread([r.get('raw_heartbeats') for r in baseline]),
                                   'wall_seconds': spread([r.get('wall_seconds') for r in baseline])}}
            if baseline and eligible:
                bt = baseline[0]['proof_tokens']
                bh = statistics.median(r['raw_heartbeats'] for r in baseline)
                by_hash = collections.defaultdict(list)
                for r in eligible:
                    by_hash[r['proof_sha256']].append(r)
                def score(r):
                    # Baseline is exactly 1; candidate selection uses repeated median,
                    # not the most favorable single heartbeat observation.
                    if r['proof_sha256'] == original_hash:
                        return 1.0
                    h = statistics.median(x['raw_heartbeats'] for x in by_hash[r['proof_sha256']])
                    return 0.5 * (r['proof_tokens'] / bt + h / bh)
                best = min(eligible, key=lambda r: (score(r), r['proof_tokens'], r['proof_sha256']))
                same = [r for r in group if r['proof_sha256'] == best['proof_sha256']]
                valid_same = [r for r in same if r.get('valid')]
                result['best_observed'] = {k: best.get(k) for k in ['label', 'proof_sha256', 'proof_tokens', 'raw_heartbeats', 'axioms', 'result_path']}
                median_hb = statistics.median(r['raw_heartbeats'] for r in valid_same)
                result['best_observed'].update(local_score=score(best),
                                              median_raw_heartbeats=median_hb,
                                              token_reduction=1-best['proof_tokens']/bt,
                                              heartbeat_reduction=1-median_hb/bh,
                                              same_hash_verifications=len(same),
                                              same_hash_all_valid=all(r.get('valid') for r in same),
                                              repeated_raw_heartbeats=spread([r['raw_heartbeats'] for r in valid_same]),
                                              repeated_wall_seconds=spread([r['wall_seconds'] for r in valid_same]))
                all_finals[(variant, number)] = best['proof_sha256']
            arm['problems'][str(number)] = result
        output['arms'][variant] = arm
    output['cross_arm_best_hashes'] = {str(p): {v: all_finals.get((v, p)) for v in output['arms']} for p in [1, 2, 3]}
    return output

if __name__ == '__main__':
    output = collect()
    (BASE / 'analysis/summary.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    for variant, arm in output['arms'].items():
        compact = {p: {'verified': r['verification_count'], 'unique_candidates': r['distinct_candidate_hashes'],
                       'baseline_hb': r['baseline']['raw_heartbeats'],
                       'best': r.get('best_observed', {}).get('local_score')}
                   for p, r in arm['problems'].items()}
        print(variant, json.dumps(compact))
