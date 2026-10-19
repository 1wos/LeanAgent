#!/usr/bin/env python3
"""Finish unrecorded inputs with three workers; retain all completed measurements."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import compare_methods as m

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--repos', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
protocol = json.loads((a.output / 'protocol.json').read_text())
assert m.sha(m.HERE / 'protocol.json') == m.sha(a.output / 'protocol.json')
records = json.loads((a.output / 'results.json').read_text())
done = {(r['problem'], r['candidate_id']) for r in records}
manifest = json.loads((a.output / 'environment.json').read_text())
repos = {k: Path(v).resolve() for k, v in json.loads(a.repos.read_text()).items()}
pending = [x for x in protocol['inputs'] if (x['problem'], x['id']) not in done]
order = {tag: i for i, tag in enumerate(manifest['execution_order'])}
pending.sort(key=lambda x: order[f"P{x['problem']}-{x['id']}"])
for env in sorted({x['environment'] for x in pending}):
    m.replay.check_environment(repos[env], protocol['environments'][env])
for x in pending:
    assert m.sha(m.EVIDENCE / x['path']) == x['sha256']
    # An interrupted, unrecorded input is rerun; completed logs are untouched.
    (a.output / 'logs' / f"P{x['problem']}-{x['id']}.log").unlink(missing_ok=True)
manifest['continuation'] = {'started_utc': datetime.now(timezone.utc).isoformat(),
    'completed_before_continuation': len(records), 'workers': 3,
    'script_sha256': m.sha(Path(__file__)),
    'reason': 'Shorten execution latency. Wall-clock times are not used for selection or performance claims.'}
m.save(a.output / 'environment.json', manifest)

def run(x):
    tag = f"P{x['problem']}-{x['id']}"
    spec = protocol['environments'][x['environment']]
    result = m.replay.run_one(repos[x['environment']], spec, m.EVIDENCE / x['path'], tag,
        protocol['timeout_seconds'], a.output / 'logs' / f'{tag}.log', protocol['expected_axioms'])
    result.update(problem=x['problem'], candidate_id=x['id'], role=x['role'],
        environment=x['environment'], input_path=x['path'], input_sha256=x['sha256'])
    return result

with ThreadPoolExecutor(max_workers=3) as workers:
    futures = [workers.submit(run, x) for x in pending]
    for f in as_completed(futures):
        result = f.result()
        records.append(result)
        m.save(a.output / 'results.json', records)
        print(f"{len(records)}/30 P{result['problem']}-{result['candidate_id']}: {result['status']}", flush=True)
manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
m.save(a.output / 'environment.json', manifest)
assert len(records) == len(protocol['inputs'])
assert all(r['accepted'] for r in records if r['role'] == 'reference')
