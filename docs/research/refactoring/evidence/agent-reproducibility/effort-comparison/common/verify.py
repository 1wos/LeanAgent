#!/usr/bin/env python3
"""Frozen local verifier: original full context, scoped heartbeat, transitive axioms.

This is an experimental local metric, not the Arena official evaluator.
Lean runs with one thread, bounded memory/time, no network or filesystem writes.
The surrounding coding agents are NOT operating-system sandboxed.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import textwrap
import time

COMMON = Path(__file__).resolve().parent
BASE = COMMON.parent
sys.path.insert(0, str(COMMON))
from proof_tokens import proof_length

INSTRUMENT = '''
set_option Elab.async false
set_option maxHeartbeats 200000
set_option maxRecDepth 1000
open Lean Elab Command in
elab "#experiment_count " c:command : command => do
  let before ← IO.getNumHeartbeats
  elabCommand c
  let after ← IO.getNumHeartbeats
  logInfo m!"EXPERIMENT_HEARTBEATS_RAW {after - before}"

'''

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant', required=True, choices=['high', 'xhigh', 'ultra', 'control'])
    p.add_argument('--problem', required=True, type=int, choices=[1, 2, 3])
    p.add_argument('--candidate', required=True, type=Path, help='Proof term only, usually beginning with by')
    p.add_argument('--label', required=True)
    p.add_argument('--parent', default='reference')
    p.add_argument('--strategy', default='unspecified')
    args = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.label):
        p.error('label must use ASCII letters, digits, underscores or hyphens')
    folder = BASE / args.variant
    folder.mkdir(exist_ok=True)
    lock = (folder / '.verification.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX)
    out = folder / 'runs' / f'P{args.problem:02d}' / args.label
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((COMMON / 'manifest.json').read_text())
    row = json.loads((COMMON / f'P{args.problem:02d}/metadata.json').read_text())
    proof = args.candidate.read_text().strip() + '\n'
    (out / 'proof.lean').write_text(proof)
    record = {'schema_version': 1, 'variant': args.variant, 'problem': args.problem,
              'label': args.label, 'parent': args.parent, 'strategy': args.strategy,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'proof_sha256': sha(proof.encode()), 'manifest_sha256': sha((COMMON / 'manifest.json').read_bytes()),
              'toolchain': manifest['toolchain'], 'source_revision': manifest['source_revision'],
              'limits': manifest['limits'], 'candidate_path': str(args.candidate.resolve()),
              'metric_scope': 'target declaration elaboration including command-wrapper overhead; not official Arena heartbeat'}
    try:
        for name, expected in manifest['files_sha256'].items():
            if sha((COMMON / name).read_bytes()) != expected:
                raise ValueError(f'Frozen input modified: {name}')
        # Experimental proof-language restriction; the Lean process is separately sandboxed.
        denied = re.search(r'\b(sorry|admit|sorryAx|axiom|unsafe|run_tac|run_elab|elab|macro|set_option|native_decide)\b|(?m:^\s*#)', proof)
        if denied:
            raise ValueError(f'Candidate contains forbidden syntax: {denied.group()}')
        if re.search(r'\b' + re.escape(row['name'].split('.')[-1]) + r'\b', proof):
            raise ValueError('Direct reference to the target theorem is forbidden')
        source = (COMMON / f'P{args.problem:02d}/source.lean').read_text()
        if source.count(row['src']) != 1:
            raise ValueError('Target declaration is not unique in frozen source')
        replacement = '#experiment_count\n' + row['statement'] + ' :=\n' + textwrap.indent(proof, '  ')
        replacement += f'\n#print axioms _root_.{row["name"]}\n#check _root_.{row["name"]}\n'
        source = source.replace(row['src'], replacement, 1)
        lines = source.splitlines(keepends=True)
        last_import = max(i for i, line in enumerate(lines) if line.startswith('import '))
        lines.insert(last_import + 1, 'import Lean\n' + INSTRUMENT)
        context = out / 'context.lean'
        context.write_text(''.join(lines))
        record['context_sha256'] = sha(context.read_bytes())
        declaration = row['statement'] + ' := ' + proof
        record['proof_tokens'] = proof_length(declaration, row['statement'])
        cmd = ['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*) (deny file-write*)',
               manifest['lean_binary'], '-j1', '-M1536', '-T200000', '--json', str(context)]
        record['command'] = cmd
        env = os.environ.copy()
        env['LEAN_PATH'] = manifest['lean_path']
        start = time.monotonic()
        with (out / 'stdout.jsonl').open('w') as stdout, (out / 'stderr.txt').open('w') as stderr:
            proc = subprocess.Popen(cmd, cwd=out, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                proc.wait(timeout=manifest['limits']['wall_seconds_per_verification'])
                record['status'] = 'completed'
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                record['status'] = 'timeout'
        record['wall_seconds'] = time.monotonic() - start
        record['exit_code'] = proc.returncode
        messages = []
        for line in (out / 'stdout.jsonl').read_text().splitlines():
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                messages.append({'severity': 'unparsed', 'data': line})
        record['errors'] = [m for m in messages if m.get('severity') == 'error']
        record['warnings'] = [m for m in messages if m.get('severity') == 'warning']
        text = '\n'.join(str(m.get('data', '')) for m in messages)
        heartbeats = re.findall(r'EXPERIMENT_HEARTBEATS_RAW (\d+)', text)
        record['raw_heartbeats'] = int(heartbeats[0]) if len(heartbeats) == 1 else None
        record['heartbeats'] = record['raw_heartbeats'] / 1000 if record['raw_heartbeats'] is not None else None
        axiom_line = next((str(m.get('data', '')) for m in messages
                           if row['name'] in str(m.get('data', '')) and 'depends on axioms' in str(m.get('data', ''))), None)
        if axiom_line:
            match = re.search(r'depends on axioms:\s*\[([^]]*)\]', axiom_line)
            record['axioms'] = [x.strip() for x in match.group(1).split(',') if x.strip()] if match else None
        elif any(row['name'] in str(m.get('data', '')) and 'does not depend on any axioms' in str(m.get('data', '')) for m in messages):
            record['axioms'] = []
        else:
            record['axioms'] = None
        record['valid'] = (record['status'] == 'completed' and proc.returncode == 0
                           and not record['errors'] and record['raw_heartbeats'] is not None
                           and record['axioms'] is not None
                           and set(record['axioms']) <= {'propext', 'Classical.choice', 'Quot.sound'})
    except Exception as error:
        record.update(status='harness_error', valid=False, error=str(error))
    record['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    with (folder / 'events.jsonl').open('a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(json.dumps(record, ensure_ascii=False))
    return 0 if record.get('valid') else 1

if __name__ == '__main__':
    raise SystemExit(main())
