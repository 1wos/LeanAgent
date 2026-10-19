#!/usr/bin/env python3
"""Repeat one saved verification command with its exact context path fixed.

Separate post-window control: not an additional agent optimization attempt.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import statistics
import subprocess
import time

BASE = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('result', type=Path)
    p.add_argument('--repeats', type=int, default=3)
    args = p.parse_args()
    path = args.result.resolve()
    saved = json.loads(path.read_text())
    assert saved['valid']
    context = path.with_name('context.lean')
    assert hashlib.sha256(context.read_bytes()).hexdigest() == saved['context_sha256']
    manifest = json.loads((BASE / 'common/manifest.json').read_text())
    env = os.environ.copy()
    env['LEAN_PATH'] = manifest['lean_path']
    out = BASE / 'analysis/same-path-control'
    out.mkdir(exist_ok=False)
    records = []
    for i in range(args.repeats):
        start = time.monotonic()
        stdout_path = out / f'{i+1}.stdout.jsonl'
        stderr_path = out / f'{i+1}.stderr.txt'
        started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with stdout_path.open('w') as stdout, stderr_path.open('w') as stderr:
            proc = subprocess.Popen(saved['command'], cwd=path.parent, env=env,
                                    stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
        messages = [json.loads(line) for line in stdout_path.read_text().splitlines() if line.strip()]
        values = [int(m.group(1)) for x in messages
                  if (m := re.search(r'EXPERIMENT_HEARTBEATS_RAW (\d+)', str(x.get('data', ''))))]
        row = {'repeat': i+1, 'started_at': started_at, 'wall_seconds': time.monotonic()-start,
               'exit_code': proc.returncode, 'raw_heartbeats': values[0] if len(values)==1 else None,
               'errors': [x for x in messages if x.get('severity')=='error']}
        records.append(row)
        print(json.dumps(row), flush=True)
    result = {'source_result': str(path.relative_to(BASE)), 'context_sha256': saved['context_sha256'],
              'command': saved['command'], 'fixed_context_path': str(context),
              'control': 'Same stored context bytes, same absolute input path, same cwd and command; fresh process each repeat, after agent window.',
              'records': records, 'all_compiled': all(x['exit_code']==0 and not x['errors'] for x in records),
              'raw_heartbeat_range': [min(x['raw_heartbeats'] for x in records), max(x['raw_heartbeats'] for x in records)],
              'raw_heartbeat_median': statistics.median(x['raw_heartbeats'] for x in records)}
    (out / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')

if __name__ == '__main__':
    main()
