#!/usr/bin/env python3
"""Audit recorded traces; reexecute each proposed proof once without a model."""
import itertools
import json
from pathlib import Path
import statistics
import sys

import harness as h

BASE = h.BASE
sys.path.insert(0, str(BASE/'common'))
from proof_tokens import lex, remove_comments


def lexical_hash(proof):
    return h.digest(json.dumps(lex(remove_comments(proof)).split(), ensure_ascii=False))


def live_replay():
    results = []
    for trial in h.TRIALS:
        for step in range(1,h.ROUNDS+1):
            event = h.read(BASE/trial/f'event_{step}.json')
            old = event['result']
            if old['status'] == 'protocol_rejected':
                continue
            label = f'replay_{trial}_{step}'
            saved = BASE/'control/runs/P02'/label/'result.json'
            new = h.read(saved) if saved.exists() else h.verify('control', BASE/trial/f'candidate_{step}.lean', label)
            keys = ['proof_sha256', 'context_sha256', 'valid', 'proof_tokens', 'raw_heartbeats', 'axioms', 'status']
            comparisons = {k: old.get(k) == new.get(k) for k in keys}
            old_fb, new_fb = h.feedback(old), h.feedback(new)
            comparisons['feedback'] = old_fb == new_fb
            results.append({'trial':trial,'step':step,'comparisons':comparisons,
                            'old_heartbeats':old.get('raw_heartbeats'), 'new_heartbeats':new.get('raw_heartbeats')})
            print(json.dumps({'live_replay':label,'comparisons':comparisons}),flush=True)
    (BASE/'analysis/live-replay.json').write_text(h.canonical(results))
    return results


def compare_live_states():
    rows = []
    for trial in h.TRIALS:
        state = h.initial_state()
        steps = []
        for step in range(1,h.ROUNDS+1):
            event = h.read(BASE/trial/f'event_{step}.json')
            new = h.read(BASE/'control/runs/P02'/f'replay_{trial}_{step}'/'result.json')
            input_same = h.digest(h.canonical(h.make_request(state))) == event['request_sha256']
            state = h.reduce_event(state,event['response_raw'],new)
            steps.append({'step':step,'request_same':input_same,'state_same':state==event['after']})
        rows.append({'trial':trial,'steps':steps,
                     'selected_proof_same':state['best']['proof_sha256']==event['after']['best']['proof_sha256'],
                     'best_score':state['best']['local_score']})
    (BASE/'analysis/live-state-comparison.json').write_text(h.canonical(rows))
    return rows


def main():
    h.frozen()
    record_replay = h.replay()
    (BASE/'analysis/record-replay.json').write_text(h.canonical(record_replay))
    live = live_replay()
    compare_live_states()
    trials = []
    request_sizes, response_sizes, feedback_sizes = [], [], []
    all_records = list((BASE/'control/runs/P02').glob('*/result.json'))
    for trial in h.TRIALS:
        events = [h.read(BASE/trial/f'event_{i}.json') for i in range(1,h.ROUNDS+1)]
        for i, event in enumerate(events,1):
            folder = BASE/'mailbox'/f'{trial}_s{i}'
            request_sizes.append(len((folder/'request.json').read_text()))
            response_sizes.append(len(event['response_raw']))
            feedback_sizes.append(len(h.canonical(h.feedback(event['result']))))
            if event['result']['status'] != 'protocol_rejected':
                saved = BASE/trial/f'runs/P02/step_{i}/result.json'
                assert h.read(saved) == event['result']
                all_records.append(saved)
                assert h.digest((BASE/trial/f'candidate_{i}.lean').read_bytes()) == event['result']['proof_sha256']
        best = events[-1]['after']['best']
        (BASE/trial/'selected.lean').write_text(best['proof'])
        label = f'final_{trial}'
        saved = BASE/'control/runs/P02'/label/'result.json'
        final = h.read(saved) if saved.exists() else h.verify('control', BASE/trial/'selected.lean', label)
        all_records.append(saved)
        first_proof = h.parse_response(events[0]['response_raw'])['proof'].strip()+'\n'
        trials.append({'trial':trial,'valid_candidates':sum(e['result']['valid'] for e in events),
                       'protocol_rejections':sum(e['result']['status']=='protocol_rejected' for e in events),
                       'first_request_sha256':events[0]['request_sha256'],
                       'first_proof_sha256':h.digest(first_proof),'first_lexical_sha256':lexical_hash(first_proof),
                       'best':best,'best_lexical_sha256':lexical_hash(best['proof']),
                       'selected_from':next((i for i,e in enumerate(events,1)
                                            if e['result'].get('valid') and e['result']['proof_sha256']==best['proof_sha256']), 'baseline'),
                       'final_check_valid':final['valid'],'final_check_heartbeats':final.get('raw_heartbeats'),
                       'final_check_score':h.metric(best['proof'],final)['local_score'] if final['valid'] else None})
    audit = h.environment()
    before = h.read(BASE/'analysis/environment-before.json')
    assert audit['files'] == before['files']
    (BASE/'analysis/environment-after.json').write_text(h.canonical(audit))
    intervals = []
    for path in set(all_records):
        result = h.read(path)
        if 'context_sha256' in result:
            assert h.digest((path.parent/'context.lean').read_bytes()) == result['context_sha256']
        if 'command' in result:
            intervals.append((result['started_at'],result['finished_at'],str(path)))
    intervals.sort()
    overlaps = [(a[2],b[2]) for a,b in zip(intervals,intervals[1:]) if b[0] < a[1]]
    assert not overlaps
    pairs = []
    for a,b in itertools.combinations(trials,2):
        pairs.append({'a':a['trial'],'b':b['trial'],
                      'same_first_proof':a['first_proof_sha256']==b['first_proof_sha256'],
                      'same_final_proof':a['best']['proof_sha256']==b['best']['proof_sha256'],
                      'same_final_lexical':a['best_lexical_sha256']==b['best_lexical_sha256']})
    summary = {'trials':trials,'pairs':pairs,'record_replay_passes':len(record_replay['checks']),
               'live_replays':len(live),'live_replays_all_fields_equal':sum(all(r['comparisons'].values()) for r in live),
               'request_characters':request_sizes,'response_characters':response_sizes,'feedback_characters':feedback_sizes,
               'frozen_files_checked':audit['file_count'],'verifier_runs':len(set(all_records)),
               'serial_overlap_count':len(overlaps),'selftest':h.selftest()}
    (BASE/'analysis/summary.json').write_text(h.canonical(summary))
    print(json.dumps({k:v for k,v in summary.items() if k not in ['trials','pairs']},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
