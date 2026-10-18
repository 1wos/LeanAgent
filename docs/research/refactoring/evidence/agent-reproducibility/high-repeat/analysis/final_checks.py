#!/usr/bin/env python3
"""Select by the preregistered rule, then repeat each selected proof five times."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def main():
    baseline = read(BASE / 'baseline.json')
    selections = []
    for trial in ['run01', 'run02', 'run03']:
        state = read(BASE / trial / 'gate_state.json')
        assert len(state['submissions']) == 8
        assert all('finished_at' in s for s in state['submissions'])
        options = [dict(label='reference', score=1.0, proof_tokens=baseline['proof_tokens'],
                        attempt=0, proof_path='common/P02/reference.lean')]
        for entry in state['submissions']:
            if not entry.get('valid'):
                continue
            result = read(BASE / entry['result_path'])
            options.append(dict(label=entry['label'], score=entry['score'],
                                proof_tokens=result['proof_tokens'], attempt=entry['attempt'],
                                proof_path=str(Path(entry['result_path']).with_name('proof.lean'))))
        selected = min(options, key=lambda r: (r['score'], r['proof_tokens'], r['attempt']))
        selected['trial'] = trial
        selections.append(selected)
    selection_path = BASE / 'analysis/selections.json'
    if selection_path.exists():
        assert read(selection_path) == selections
    else:
        selection_path.write_text(json.dumps(selections, indent=2) + '\n')
    for selected in selections:
        trial = selected['trial']
        for n in range(1, 6):
            label = f'final_{n:02d}'
            result_path = BASE / trial / 'runs/P02' / label / 'result.json'
            if result_path.exists():
                record = read(result_path)
            else:
                lock = (BASE / '.lean.lock').open('a')
                fcntl.flock(lock, fcntl.LOCK_EX)
                command = [sys.executable, str(BASE / 'common/verify.py'), '--variant', trial,
                           '--problem', '2', '--candidate', str(BASE / selected['proof_path']),
                           '--label', label, '--parent', selected['label'],
                           '--strategy', 'Parent final repetition; not agent feedback or a new model generation']
                process = subprocess.run(command, capture_output=True, text=True)
                fcntl.flock(lock, fcntl.LOCK_UN)
                if not result_path.exists():
                    raise RuntimeError(process.stderr[-1000:])
                record = read(result_path)
            print(json.dumps(dict(trial=trial, repeat=n, valid=record['valid'],
                                  raw_heartbeats=record.get('raw_heartbeats')), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
