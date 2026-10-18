#!/usr/bin/env python3
"""Bound task input, submissions and feedback for three fresh-agent trials.

Only the verifier subprocess has an OS sandbox. Agent read restrictions remain
instructions. Full diagnostics stay on disk for the parent, not in agent output.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def frozen_check():
    manifest = read(BASE / 'common/manifest.json')
    for name, expected in manifest['files_sha256'].items():
        if sha((BASE / 'common' / name).read_bytes()) != expected:
            raise ValueError('Frozen input modified: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'submit'])
    parser.add_argument('--trial', required=True, choices=['run01', 'run02', 'run03'])
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--hypothesis', default='')
    args = parser.parse_args()
    trial = BASE / args.trial
    lock = (trial / '.gate.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX)
    frozen_check()
    state_path = trial / 'gate_state.json'
    state = read(state_path) if state_path.exists() else {'submissions': []}
    if args.action == 'start':
        if 'started_at' in state:
            parser.error('Start packet already delivered; reuse your conversation copy')
        packet = (BASE / 'common/packet.txt').read_text()
        assert len(packet) <= 12000
        state.update(started_at=now(), packet_sha256=sha(packet.encode()), packet_characters=len(packet))
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        print(packet, end='')
        return 0
    if 'started_at' not in state:
        parser.error('Read the start packet first')
    if len(state['submissions']) >= 8:
        parser.error('Eight-submission budget exhausted')
    number = len(state['submissions']) + 1
    label = f'attempt_{number:02d}'
    entry = dict(attempt=number, label=label, submitted_at=now(), hypothesis=args.hypothesis[:240])
    state['submissions'].append(entry)
    state_path.write_text(json.dumps(state, indent=2) + '\n')
    feedback = dict(attempt=number, remaining=8-number, valid=False)
    try:
        if args.candidate is None:
            raise ValueError('Candidate path is required; submission consumed')
        candidate = args.candidate.resolve()
        if not candidate.is_relative_to((trial / 'candidates').resolve()):
            raise ValueError('Candidate must be inside your candidates directory')
        proof = candidate.read_text()
        entry.update(candidate_path=str(candidate.relative_to(BASE)),
                     submitted_sha256=sha(proof.encode()), submitted_characters=len(proof))
        if len(proof) > 4000:
            raise ValueError('Candidate exceeds 4000 Unicode characters; submission consumed')
        global_lock = (BASE / '.lean.lock').open('a')
        fcntl.flock(global_lock, fcntl.LOCK_EX)
        command = [sys.executable, str(BASE / 'common/verify.py'), '--variant', args.trial,
                   '--problem', '2', '--candidate', str(candidate), '--label', label,
                   '--parent', f'attempt_{number-1:02d}' if number > 1 else 'reference',
                   '--strategy', args.hypothesis[:240]]
        process = subprocess.run(command, capture_output=True, text=True)
        fcntl.flock(global_lock, fcntl.LOCK_UN)
        result_path = trial / 'runs/P02' / label / 'result.json'
        if not result_path.exists():
            raise RuntimeError('Verifier failed before recording a result: ' + process.stderr[-400:])
        result = read(result_path)
        baseline = read(BASE / 'baseline.json')
        score = (0.5 * (result['proof_tokens'] / baseline['proof_tokens']
                        + result['raw_heartbeats'] / baseline['median_raw_heartbeats'])
                 if result.get('valid') else None)
        feedback.update(valid=result.get('valid', False), proof_tokens=result.get('proof_tokens'),
                        raw_heartbeats=result.get('raw_heartbeats'), local_score=score,
                        axioms=result.get('axioms'))
        errors = [str(e.get('data', e)) if isinstance(e, dict) else str(e)
                  for e in result.get('errors', [])]
        if result.get('error'):
            errors.append(result['error'])
        # Bound each diagnostic too, so a large first goal cannot hide every later error.
        feedback['diagnostics'] = '\n'.join(e[:500] for e in errors[:3])
        feedback['error_count'] = len(errors)
        entry.update(result_path=str(result_path.relative_to(BASE)), valid=feedback['valid'], score=score)
    except Exception as error:
        feedback['diagnostics'] = str(error)[:900]
        entry.update(valid=False, gate_error=str(error))
    encoded = json.dumps(feedback, ensure_ascii=False, separators=(',', ':'))
    while len(encoded) + 1 > 1500:
        feedback['diagnostics'] = feedback.get('diagnostics', '')[:-40]
        encoded = json.dumps(feedback, ensure_ascii=False, separators=(',', ':'))
    output = encoded + '\n'
    entry.update(feedback_characters=len(output), feedback_sha256=sha(output.encode()), finished_at=now())
    (trial / f'feedback_{number:02d}.json').write_text(output)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    print(encoded)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
