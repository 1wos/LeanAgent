#!/usr/bin/env python3
"""Audit bounded-context records and compare independent trial outputs."""
import datetime
import difflib
import hashlib
import itertools
import json
from pathlib import Path
import statistics
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'common'))
from proof_tokens import lex, remove_comments


def read(path):
    return json.loads(path.read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(proof):
    return dict(exact_sha256=sha(proof.encode()),
                lexical_sha256=sha(' '.join(lex(remove_comments(proof)).split()).encode()))


def spread(values):
    return dict(values=values, min=min(values), median=statistics.median(values),
                max=max(values), spread=max(values)-min(values))


def main():
    baseline = read(BASE / 'baseline.json')
    selection = {s['trial']: s for s in read(BASE / 'analysis/selections.json')}
    protocol = read(BASE / 'protocol.json')
    rows, proofs, mismatches = [], {}, []
    frozen = read(BASE / 'analysis/frozen-before.json')
    for path, expected in frozen.items():
        if sha((BASE / path).read_bytes()) != expected:
            mismatches.append('frozen:' + path)
    imported = read(BASE / 'analysis/imported-artifacts-before.json')
    for path, expected in imported['files'].items():
        if sha(Path(path).read_bytes()) != expected:
            mismatches.append('import:' + path)
    manifest = read(BASE / 'common/manifest.json')
    manifest_hash = sha((BASE / 'common/manifest.json').read_bytes())
    if sha(Path(manifest['lean_binary']).read_bytes()) != manifest['lean_binary_sha256']:
        mismatches.append('Lean binary changed')
    intervals, all_records = [], []
    for trial in ['run01', 'run02', 'run03', 'control']:
        for path in sorted((BASE / trial / 'runs/P02').glob('*/result.json')):
            r = read(path)
            all_records.append(r)
            for key, filename in [('proof_sha256', 'proof.lean'), ('context_sha256', 'context.lean')]:
                if key in r and sha(path.with_name(filename).read_bytes()) != r[key]:
                    mismatches.append(str(path.relative_to(BASE)) + ':' + key)
            if r['manifest_sha256'] != manifest_hash:
                mismatches.append(str(path.relative_to(BASE)) + ':manifest')
            if r.get('valid') and (r.get('exit_code') != 0 or r.get('errors')
                                   or r.get('axioms') is None
                                   or not set(r['axioms']) <= {'propext', 'Classical.choice', 'Quot.sound'}):
                mismatches.append(str(path.relative_to(BASE)) + ':invalid validity record')
            intervals.append((r['started_at'], r['finished_at']))
    intervals.sort()
    overlaps = sum(a[1] > b[0] for a, b in zip(intervals, intervals[1:]))
    if overlaps:
        mismatches.append('Overlapping verifier records')
    for trial in ['run01', 'run02', 'run03']:
        state = read(BASE / trial / 'gate_state.json')
        entries = state['submissions']
        assert len(entries) == 8 and all('finished_at' in e for e in entries)
        assert state['packet_sha256'] == sha((BASE / 'common/packet.txt').read_bytes())
        feedback_lengths = []
        attempts = []
        for e in entries:
            feedback = (BASE / trial / f'feedback_{e["attempt"]:02d}.json').read_text()
            assert len(feedback) <= 1500 and len(feedback) == e['feedback_characters']
            assert sha(feedback.encode()) == e['feedback_sha256']
            feedback_lengths.append(len(feedback))
            submitted = (BASE / e['candidate_path']).read_text()
            assert len(submitted) <= 4000 and sha(submitted.encode()) == e['submitted_sha256']
            r = read(BASE / e['result_path']) if e.get('result_path') else {}
            attempts.append(dict(attempt=e['attempt'], valid=e['valid'], score=e.get('score'),
                                 proof_tokens=r.get('proof_tokens'), raw_heartbeats=r.get('raw_heartbeats'),
                                 proof_sha256=r.get('proof_sha256'), hypothesis=e['hypothesis'],
                                 result_path=e.get('result_path'), candidate_path=e['candidate_path']))
        first_path = BASE / entries[0]['result_path']
        first_proof = first_path.with_name('proof.lean').read_text()
        final_paths = sorted((BASE / trial / 'runs/P02').glob('final_*/result.json'))
        assert len(final_paths) == 5
        finals = [read(p) for p in final_paths]
        final_proof = final_paths[0].with_name('proof.lean').read_text()
        assert len({r['proof_sha256'] for r in finals}) == 1
        assert len({r['context_sha256'] for r in finals}) == 1
        raw = spread([r['raw_heartbeats'] for r in finals])
        tokens = finals[0]['proof_tokens']
        score = 0.5 * (tokens / baseline['proof_tokens'] + raw['median'] / baseline['median_raw_heartbeats'])
        selected_dir = BASE / trial / 'selected'
        selected_dir.mkdir(exist_ok=True)
        (selected_dir / 'proof.lean').write_text(final_proof)
        proofs[trial] = dict(first=first_proof, final=final_proof)
        rows.append(dict(trial=trial, started_at=state['started_at'], finished_at=entries[-1]['finished_at'],
                         candidate_attempts=8, valid_candidates=sum(e['valid'] for e in entries),
                         invalid_candidates=sum(not e['valid'] for e in entries),
                         packet_sha256=state['packet_sha256'], packet_characters=state['packet_characters'],
                         feedback_characters=feedback_lengths, total_feedback_characters=sum(feedback_lengths),
                         delivered_domain_characters=state['packet_characters']+sum(feedback_lengths),
                         first_candidate=dict(**fingerprint(first_proof), valid=attempts[0]['valid'],
                                              path=str(first_path.with_name('proof.lean').relative_to(BASE))),
                         selection=selection[trial], final=dict(**fingerprint(final_proof), proof_tokens=tokens,
                         raw_heartbeats=raw, local_score=score, valid_repeats=sum(r['valid'] for r in finals),
                         axioms=finals[0]['axioms'], path=f'{trial}/selected/proof.lean',
                         wall_seconds=spread([r['wall_seconds'] for r in finals])), attempts=attempts,
                         completion=read(BASE / trial / 'completion.json')))
    pairs = []
    diff_dir = BASE / 'analysis/diffs'
    diff_dir.mkdir(exist_ok=True)
    for a, b in itertools.combinations(rows, 2):
        pair = dict(a=a['trial'], b=b['trial'])
        for phase, field in [('first', 'first_candidate'), ('final', 'final')]:
            pair[phase + '_exact_match'] = a[field]['exact_sha256'] == b[field]['exact_sha256']
            pair[phase + '_lexical_match'] = a[field]['lexical_sha256'] == b[field]['lexical_sha256']
            delta = ''.join(difflib.unified_diff(proofs[a['trial']][phase].splitlines(True),
                                               proofs[b['trial']][phase].splitlines(True),
                                               fromfile=a['trial'], tofile=b['trial']))
            (diff_dir / f'{phase}_{a["trial"]}_{b["trial"]}.diff').write_text(delta)
        pairs.append(pair)
    output = dict(generated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  protocol=protocol, baseline=baseline, trials=rows, pairwise=pairs,
                  first_exact_distinct=len({r['first_candidate']['exact_sha256'] for r in rows}),
                  final_exact_distinct=len({r['final']['exact_sha256'] for r in rows}),
                  final_lexical_distinct=len({r['final']['lexical_sha256'] for r in rows}),
                  final_score_distribution=spread([r['final']['local_score'] for r in rows]),
                  interpretation='Lexical comparison ignores comments/whitespace; it is not a semantic equivalence proof.')
    audit = dict(passed=not mismatches, mismatches=mismatches, frozen_files_checked=len(frozen),
                 imported_artifacts_checked=imported['file_count'], run_records_checked=len(all_records),
                 observed_verifier_overlaps=overlaps, packet_hash_identical=len({r['packet_sha256'] for r in rows})==1,
                 all_submission_counts_eight=True, all_feedback_within_cap=True,
                 agent_filesystem_isolation='instruction-only; completion reports are self-reports',
                 checked_at_utc=output['generated_at_utc'])
    (BASE / 'analysis/comparison.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    (BASE / 'analysis/audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
    assert audit['passed'], audit
    print(json.dumps(audit, ensure_ascii=False))
    for r in rows:
        print(r['trial'], 'valid candidates', r['valid_candidates'], 'tokens', r['final']['proof_tokens'],
              'HB', r['final']['raw_heartbeats']['median'], 'score', r['final']['local_score'],
              'repeat valid', r['final']['valid_repeats'])
    print('Pairs:', json.dumps(pairs))


if __name__ == '__main__':
    main()
