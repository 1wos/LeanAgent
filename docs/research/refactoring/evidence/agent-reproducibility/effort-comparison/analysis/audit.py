#!/usr/bin/env python3
"""Check recorded code hashes, frozen inputs and imported .olean fingerprints."""
import datetime
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def main():
    manifest_path = BASE / 'common/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest_hash = digest(manifest_path)
    mismatches = []
    for name, expected in manifest['files_sha256'].items():
        if digest(BASE / 'common' / name) != expected:
            mismatches.append({'kind': 'frozen_input', 'path': name})
    checked = 0
    for variant in ['high', 'xhigh', 'ultra']:
        for path in (BASE / variant / 'runs').glob('P*/*/result.json'):
            record = json.loads(path.read_text())
            checked += 1
            for key, filename in [('proof_sha256', 'proof.lean'), ('context_sha256', 'context.lean')]:
                if key in record and digest(path.with_name(filename)) != record[key]:
                    mismatches.append({'kind': key, 'result': str(path.relative_to(BASE))})
            if record['manifest_sha256'] != manifest_hash:
                mismatches.append({'kind': 'manifest_mismatch', 'result': str(path.relative_to(BASE))})
            if record.get('valid') and (record.get('exit_code') != 0 or record.get('errors')
                                       or record.get('axioms') is None
                                       or not set(record['axioms']) <= {'propext', 'Classical.choice', 'Quot.sound'}):
                mismatches.append({'kind': 'validity_record_inconsistent', 'result': str(path.relative_to(BASE))})
    before = json.loads((BASE / 'analysis/imported-artifacts-before.json').read_text())
    for path, expected in before['files'].items():
        if digest(Path(path)) != expected:
            mismatches.append({'kind': 'imported_artifact_changed', 'path': path})
    if digest(Path(manifest['lean_binary'])) != manifest['lean_binary_sha256']:
        mismatches.append({'kind': 'lean_binary_changed'})
    output = {'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'run_records_checked': checked, 'imported_artifacts_checked': before['file_count'],
              'frozen_files_checked': len(manifest['files_sha256']),
              'mismatches': mismatches, 'passed': not mismatches,
              'scope': 'File integrity and recorded validity consistency; not a complete security audit or independent kernel implementation.'}
    (BASE / 'analysis/integrity-audit.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(output, ensure_ascii=False))

if __name__ == '__main__':
    main()
