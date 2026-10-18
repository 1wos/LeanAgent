#!/usr/bin/env python3
"""Save observed best-so-far trajectories; not statistical learning curves."""
import datetime
import hashlib
import json
from pathlib import Path
import statistics

BASE = Path(__file__).resolve().parents[1]

def main():
    schedule = json.loads((BASE / 'schedule.json').read_text())
    origin = datetime.datetime.fromisoformat(schedule['start_utc'])
    output = {'origin': schedule['start_utc'],
              'scope': 'Observed single-agent trajectory per effort; raw single-run score for historical points, repeated medians used in final summary.',
              'arms': {}}
    for variant in ['high', 'xhigh', 'ultra']:
        arm = {}
        for n in [1, 2, 3]:
            records = sorted((json.loads(p.read_text()) for p in (BASE / variant / f'runs/P{n:02d}').glob('*/result.json')),
                             key=lambda r: r['finished_at'])
            reference = hashlib.sha256((BASE / f'common/P{n:02d}/reference.lean').read_bytes()).hexdigest()
            baseline = [r for r in records if r['proof_sha256'] == reference and r.get('valid')][:3]
            if not baseline:
                continue
            bt = baseline[0]['proof_tokens']
            bh = statistics.median(r['raw_heartbeats'] for r in baseline)
            best = 1.0
            points = []
            for r in records:
                score = None
                if r.get('valid'):
                    score = 1.0 if r['proof_sha256'] == reference else 0.5 * (r['proof_tokens']/bt + r['raw_heartbeats']/bh)
                    best = min(best, score)
                points.append({'label': r['label'], 'elapsed_seconds': (datetime.datetime.fromisoformat(r['finished_at']) - origin).total_seconds(),
                               'valid': r.get('valid', False), 'proof_sha256': r['proof_sha256'],
                               'candidate_score': score, 'best_score_so_far': best})
            arm[str(n)] = points
        output['arms'][variant] = arm
    (BASE / 'analysis/trajectories.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
