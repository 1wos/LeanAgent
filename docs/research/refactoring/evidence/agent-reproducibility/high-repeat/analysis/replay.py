#!/usr/bin/env python3
"""Recheck a saved proof through the frozen verifier without a model call."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial', required=True, choices=['run01', 'run02', 'run03'])
    p.add_argument('--label', required=True)
    args = p.parse_args()
    comparison = json.loads((BASE / 'analysis/comparison.json').read_text())
    row = next(r for r in comparison['trials'] if r['trial'] == args.trial)
    command = [sys.executable, str(BASE / 'common/verify.py'), '--variant', 'control',
               '--problem', '2', '--candidate', str(BASE / row['final']['path']),
               '--label', args.label, '--parent', args.trial,
               '--strategy', 'Replay selected proof; no model call']
    return subprocess.run(command).returncode


if __name__ == '__main__':
    raise SystemExit(main())
