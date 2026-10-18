"""Integration checks: rejected actions must never reach the executor."""
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import harness as h


def run():
    outcomes = [h.selftest()]
    real_base = h.BASE
    initial = h.initial_state()
    # A temporary mailbox, independent of the recorded experimental runs.
    with tempfile.TemporaryDirectory(prefix='harness-guard-') as directory:
        base = Path(directory)
        for name in ['common/packet.txt', 'baseline.json']:
            dest = base/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((real_base/name).read_bytes())
        folder = base/'mailbox/run01_s1'
        folder.mkdir(parents=True)
        with patch.object(h, 'BASE', base), patch.object(h, 'frozen'), patch.object(h, 'initial_state', return_value=initial), patch.object(h, 'verify', side_effect=AssertionError('unauthorized execution')) as executor:
            folder.joinpath('request.json').write_text(h.canonical(h.make_request(initial)))
            folder.joinpath('response.json').write_text(h.canonical({'action':'shell','proof':'by trivial','hypothesis':''}))
            out = h.ingest('run01',1)
            assert not out['valid']
            event = h.read(base/'run01/event_1.json')
            assert event['result']['status'] == 'protocol_rejected'
            assert event['after']['step'] == 1
            assert not (base/'run01/candidate_1.lean').exists()
            assert executor.call_count == 0
            outcomes.append({'forbidden_action_not_executed':True, 'rejection_consumes_step':True})
            try:
                h.ingest('run01',1)
            except ValueError as error:
                assert str(error) == 'duplicate_step'
            else:
                raise AssertionError('duplicate step accepted')
            outcomes.append({'duplicate_step_rejected':True})
            # Tampering with an already prepared request must stop before execution.
            request = base/'mailbox/run01_s2/request.json'
            request.write_text(request.read_text()+' ')
            try:
                h.ingest('run01',2)
            except AssertionError as error:
                assert str(error) == 'request tampered'
            else:
                raise AssertionError('tampered request accepted')
            outcomes.append({'tampered_request_rejected':True})
            h.write_new(base/'run01/event_3.json', {'after':{**initial,'step':3}})
            try:
                h.ingest('run01',4)
            except AssertionError:
                pass
            else:
                raise AssertionError('budget overflow accepted')
            assert executor.call_count == 0
            outcomes.append({'budget_overflow_rejected':True,'executor_calls_for_all_invalid_cases':0})
    (real_base/'analysis/guard-tests.json').write_text(h.canonical(outcomes))
    print(json.dumps(outcomes))


if __name__ == '__main__':
    run()
