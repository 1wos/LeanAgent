#!/usr/bin/env python3
"""Re-run a saved proof snapshot through the frozen verifier on this host.

Example: python3 analysis/replay.py high/runs/P01/example/result.json --label replay_example
Run from the experiment root after sourcing the project environment script.
This uses saved proof bytes, not a new model response.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('result', type=Path)
    p.add_argument('--label', required=True)
    args = p.parse_args()
    result = args.result.resolve()
    data = json.loads(result.read_text())
    proof = result.with_name('proof.lean')
    if hashlib.sha256(proof.read_bytes()).hexdigest() != data['proof_sha256']:
        p.error('Saved proof hash differs from result record')
    command = [sys.executable, str(BASE / 'common/verify.py'), '--variant', 'control',
               '--problem', str(data['problem']), '--candidate', str(proof),
               '--label', args.label, '--parent', f'{data["variant"]}/{data["label"]}',
               '--strategy', 'Replay saved proof snapshot; no model call']
    return subprocess.run(command).returncode

if __name__ == '__main__':
    raise SystemExit(main())
