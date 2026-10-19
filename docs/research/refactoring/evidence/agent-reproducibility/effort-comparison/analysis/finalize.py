#!/usr/bin/env python3
"""Normalize selected final results from saved verification records; no model calls."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import statistics

BASE = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def stats(values):
    return dict(values=values, min=min(values), median=statistics.median(values),
                max=max(values), spread=max(values) - min(values))


def main():
    schedule = read(BASE / 'schedule.json')
    rows, failures, totals = [], {}, collections.Counter()
    for arm in ['high', 'xhigh', 'ultra']:
        result = read(BASE / arm / 'results.json')
        details = []
        for p in result['problems']:
            number, selected = p['problem'], p['selected']
            records = []
            for path in sorted((BASE / arm / 'runs' / f'P{number:02d}').glob('*/result.json')):
                record = read(path)
                record['_path'] = str(path.relative_to(BASE))
                records.append(record)
            baseline = [r for r in records if r['label'].startswith('baseline')]
            finals = [r for r in records if r['label'].startswith('final_')]
            candidates = [r for r in records if r not in baseline and r not in finals]
            assert len(baseline) == 3 and len(finals) == 5
            assert all(r['valid'] for r in baseline + finals)
            assert len({r['context_sha256'] for r in finals}) == 1
            assert {r['proof_sha256'] for r in finals} == {selected['proof_sha256']}
            selected_path = Path(selected.get('candidate_path') or selected['path'])
            assert hashlib.sha256(selected_path.read_bytes()).hexdigest() == selected['proof_sha256']
            assert all(schedule['start_utc'] <= r['started_at'] < schedule['deadline_utc'] for r in records)
            bt = baseline[0]['proof_tokens']
            bh = statistics.median(r['raw_heartbeats'] for r in baseline)
            raw = stats([r['raw_heartbeats'] for r in finals])
            score = 0.5 * (selected['proof_tokens'] / bt + raw['median'] / bh)
            assert abs(score - selected['score']) < 1e-12
            counts = dict(tested=len(candidates), valid=sum(r['valid'] for r in candidates),
                          invalid=sum(not r['valid'] for r in candidates))
            totals.update(candidate_attempts=counts['tested'], valid_candidate_attempts=counts['valid'],
                          invalid_candidate_attempts=counts['invalid'], baseline_runs=len(baseline),
                          final_runs=len(finals), main_verifier_runs=len(records))
            rows.append(dict(arm=arm, problem=number, name=p['name'], baseline_proof_tokens=bt,
                             baseline_median_raw_heartbeats=bh,
                             selected_path=str(selected_path.relative_to(BASE)),
                             proof_sha256=selected['proof_sha256'], proof_tokens=selected['proof_tokens'],
                             raw_heartbeats=raw, score=score, axioms=selected['axioms'],
                             candidate_attempts=counts, final_runs=[r['_path'] for r in finals],
                             final_valid_count=len(finals)))
            for r in candidates:
                if r['valid']:
                    continue
                error = '\n'.join(str(e) for e in r.get('errors', []))
                low = error.lower()
                category = 'other_lean_error'
                for needle, label in [('maximum number of heartbeats', 'heartbeat_limit'),
                                      ('type mismatch', 'type_mismatch'),
                                      ('unsolved goals', 'unsolved_goals'),
                                      ('unknown tactic', 'unknown_tactic'),
                                      ('case tag', 'case_tag'),
                                      ('made no progress', 'no_progress')]:
                    if needle in low:
                        category = label
                        break
                details.append(dict(result=r['_path'], category=category, first_error=error[:500]))
        failures[arm] = dict(categories=dict(collections.Counter(d['category'] for d in details)), details=details)
    assert dict(totals) == dict(candidate_attempts=243, valid_candidate_attempts=176,
                               invalid_candidate_attempts=67, baseline_runs=27,
                               final_runs=45, main_verifier_runs=315)
    output = dict(generated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  scope='One agent trajectory per effort; final score uses five saved final verification runs.',
                  schedule=schedule, totals=dict(totals), rows=rows,
                  post_window_control='analysis/same-path-control/summary.json')
    (BASE / 'analysis/final-comparison.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    (BASE / 'analysis/failure-summary.json').write_text(json.dumps(dict(
        generated_at_utc=output['generated_at_utc'],
        classification='Heuristic category from saved diagnostics; all 67 failed candidate attempts included.',
        arms=failures), ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(totals), ensure_ascii=False))
    for r in rows:
        print(r['arm'], r['problem'], r['proof_tokens'], r['raw_heartbeats']['median'], round(r['score'], 6))


if __name__ == '__main__':
    main()
