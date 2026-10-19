#!/usr/bin/env python3
"""Parent-owned, bounded propose/verify/reduce loop; agents never run the verifier.

Filesystem mailbox is a transport adapter, not an OS security boundary. Each
model step uses a fresh agent. Record replay does not call a model or Lean.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys

BASE = Path(__file__).resolve().parent
TRIALS = ['run01', 'run02', 'run03']
ROUNDS = 3
MAX_REQUEST = 20000
MAX_RESPONSE = 5000
MAX_PROOF = 4000
MAX_FEEDBACK = 1200

INSTRUCTIONS = """Refactor only the provided Lean proof, preserving its statement and validity.
Return exactly one JSON object with exactly these keys:
{"action":"submit","proof":"by\\n  ...","hypothesis":"brief reason"}
The proof is a complete replacement proof term, at most 4000 Unicode characters.
The hypothesis is at most 240 characters. Entire JSON must be at most 5000 characters.
No markdown fences. No additional keys. Do not provide a shell command or file path.
No sorry, admit, axioms, unsafe, run_tac, run_elab, elab, macro, set_option,
native_decide, # commands, or reference to the target theorem itself.
Use only this request. Do not inspect source files, prior experiments, or other agents.
Do not run Lean, a verifier, web search, or delegate. The parent executes verification.
Each step is a fresh agent. The latest proposal and bounded feedback, plus the current
best valid proof, are your complete experimental memory. Try to improve or repair.
Minimize local_score = 0.5*(proof_tokens/baseline_tokens + raw_heartbeats/baseline_raw_heartbeats).
Baseline has score 1. Three proposals per independent trial. One proposal per step.
Only validated proofs are eligible. The parent selects minimum score, then tokens,
then proof SHA256. The original proof remains a fallback; no need to output a report.
"""


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'


def digest(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write_new(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(canonical(obj))


def environment():
    manifest = read(BASE/'common/manifest.json')
    paths = {str(BASE/'common'/k): v for k, v in manifest['files_sha256'].items()}
    paths[manifest['lean_binary']] = manifest['lean_binary_sha256']
    paths.update(read(BASE/'analysis/dependency-reference.json')['files'])
    actual = {p: digest(Path(p).read_bytes()) for p in paths}
    mismatch = [p for p in paths if paths[p] != actual[p]]
    if mismatch:
        raise ValueError('Frozen environment mismatch: ' + repr(mismatch[:3]))
    return {'file_count': len(actual), 'files': actual, 'mismatches': mismatch}


def frozen():
    for name, expected in read(BASE/'controller-manifest.json').items():
        if digest((BASE/name).read_bytes()) != expected:
            raise ValueError('Controller input modified: ' + name)


def verify(trial, path, label):
    with (BASE/'.lean.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        p = subprocess.run([sys.executable, str(BASE/'common/verify.py'),
                            '--variant', trial, '--problem', '2', '--candidate', str(path),
                            '--label', label, '--strategy', 'parent-controlled harness'],
                           capture_output=True, text=True)
        result = BASE/trial/'runs/P02'/label/'result.json'
        if not result.exists():
            raise RuntimeError('Verifier infrastructure failed: ' + p.stderr[-500:])
        return read(result)


def parse_response(raw):
    if len(raw) > MAX_RESPONSE:
        raise ValueError('response_limit')
    def unique(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                raise ValueError('duplicate_key')
            obj[k] = v
        return obj
    obj = json.loads(raw, object_pairs_hook=unique)
    if type(obj) is not dict or set(obj) != {'action', 'proof', 'hypothesis'}:
        raise ValueError('schema_keys')
    if obj['action'] != 'submit':
        raise ValueError('action_not_allowed')
    if type(obj['proof']) is not str or not obj['proof'].strip() or len(obj['proof']) > MAX_PROOF:
        raise ValueError('proof_limit_or_type')
    if type(obj['hypothesis']) is not str or len(obj['hypothesis']) > 240:
        raise ValueError('hypothesis_limit_or_type')
    return obj


def metric(proof, result):
    baseline = read(BASE/'baseline.json')
    tokens, hb = result['proof_tokens'], result['raw_heartbeats']
    numerator = tokens*baseline['median_raw_heartbeats'] + hb*baseline['proof_tokens']
    return {'proof': proof.strip()+'\n', 'proof_sha256': digest(proof.strip()+'\n'),
            'proof_tokens': tokens, 'raw_heartbeats': hb, 'rank_numerator': numerator,
            'local_score': numerator/(2*baseline['proof_tokens']*baseline['median_raw_heartbeats'])}


def initial_state():
    baseline = read(BASE/'baseline.json')
    original = (BASE/'common/P02/reference.lean').read_text()
    return {'step': 0, 'best': metric(original, {'proof_tokens': baseline['proof_tokens'],
                   'raw_heartbeats': baseline['median_raw_heartbeats']}), 'latest': None}


def make_request(state):
    obj = {'schema_version': 1, 'instructions': INSTRUCTIONS,
           'step': state['step']+1, 'total_steps': ROUNDS,
           'task_packet': (BASE/'common/packet.txt').read_text(),
           'baseline': read(BASE/'baseline.json'),
           'best': state['best'], 'latest': state['latest']}
    assert len(canonical(obj)) <= MAX_REQUEST
    return obj


def feedback(result):
    errors = [str(x.get('data', x)) if isinstance(x, dict) else str(x)
              for x in result.get('errors', [])]
    if result.get('error'):
        errors.append(result['error'])
    obj = {'valid': result.get('valid', False), 'status': result.get('status'),
           'proof_tokens': result.get('proof_tokens'), 'raw_heartbeats': result.get('raw_heartbeats'),
           'axioms': result.get('axioms'), 'error_count': len(errors),
           'diagnostics': '\n'.join(e[:450] for e in errors[:2])}
    while len(canonical(obj)) > MAX_FEEDBACK:
        obj['diagnostics'] = obj['diagnostics'][:-40]
    return obj


def reduce_event(before, raw, result):
    try:
        action = parse_response(raw)
        proof = action['proof'].strip()+'\n'
    except (ValueError, TypeError) as error:
        action = None
        proof = ''
        if result['status'] != 'protocol_rejected':
            raise AssertionError('invalid response was not rejected') from error
    best = before['best']
    if result.get('valid'):
        candidate = metric(proof, result)
        rank = lambda x: (x['rank_numerator'], x['proof_tokens'], x['proof_sha256'])
        if rank(candidate) < rank(best):
            best = candidate
    return {'step': before['step']+1, 'best': best,
            'latest': {'action': action, 'feedback': feedback(result)}}


def prepare(trial, state):
    if state['step'] >= ROUNDS:
        return
    folder = BASE/'mailbox'/f'{trial}_s{state["step"]+1}'
    write_new(folder/'request.json', make_request(state))


def initialize():
    write_new(BASE/'analysis/environment-before.json', environment())
    results = [verify('control', BASE/'common/P02/reference.lean', f'baseline_{i}') for i in range(1,4)]
    assert all(r['valid'] for r in results)
    write_new(BASE/'baseline.json', {'proof_tokens': results[0]['proof_tokens'],
                                    'median_raw_heartbeats': statistics.median(r['raw_heartbeats'] for r in results)})
    protocol = {'trials': 3, 'steps_per_trial': ROUNDS, 'fresh_agent_every_step': True,
                'reasoning_effort': 'high', 'fork_turns': 'none', 'model': 'inherited; exact ID unavailable',
                'max_request_characters': MAX_REQUEST, 'max_response_characters': MAX_RESPONSE,
                'max_proof_characters': MAX_PROOF, 'max_feedback_characters': MAX_FEEDBACK,
                'allowed_action': 'submit', 'selection': 'minimum integer score numerator, tokens, SHA256',
                'memory': 'task packet, baseline, best proof and metrics, latest proposal and feedback only',
                'backend': 'Codex subagent filesystem mailbox; not a direct API experiment',
                'agent_security': 'I/O restrictions are instructions; no OS sandbox for agent',
                'verifier_security': 'sandbox-exec denies network and all writes',
                'full_model_context': 'system/tools/identity not controlled; experiment request is bounded'}
    write_new(BASE/'protocol.json', protocol)
    names = ['harness.py', 'protocol.json', 'baseline.json', 'launch.txt', 'common/manifest.json']
    names += ['common/'+k for k in read(BASE/'common/manifest.json')['files_sha256']]
    write_new(BASE/'controller-manifest.json', {n:digest((BASE/n).read_bytes()) for n in names})
    for trial in TRIALS:
        prepare(trial, initial_state())


def ingest(trial, step):
    frozen()
    previous = BASE/trial/f'event_{step-1}.json'
    before = initial_state() if step == 1 else read(previous)['after']
    assert before['step'] == step-1 and 1 <= step <= ROUNDS
    eventpath = BASE/trial/f'event_{step}.json'
    if eventpath.exists():
        raise ValueError('duplicate_step')
    folder = BASE/'mailbox'/f'{trial}_s{step}'
    request = (folder/'request.json').read_text()
    assert request == canonical(make_request(before)), 'request tampered'
    raw = (folder/'response.json').read_text()
    try:
        action = parse_response(raw)
    except (ValueError, TypeError) as error:
        result = {'valid': False, 'status': 'protocol_rejected', 'error': str(error)}
    else:
        path = BASE/trial/f'candidate_{step}.lean'
        with path.open('x') as f:
            f.write(action['proof'].strip()+'\n')
        result = verify(trial, path, f'step_{step}')
    after = reduce_event(before, raw, result)
    event = {'step': step, 'request_sha256': digest(request), 'response_raw': raw,
             'response_sha256': digest(raw), 'before': before, 'result': result, 'after': after,
             'previous_event_sha256': digest(previous.read_bytes()) if step > 1 else None}
    write_new(eventpath, event)
    prepare(trial, after)
    return {'trial': trial, 'step': step, 'valid': result['valid'], 'feedback': feedback(result),
            'best_score': after['best']['local_score']}


def replay():
    frozen()
    checks = []
    for trial in TRIALS:
        state = initial_state()
        previous_hash = None
        for step in range(1, ROUNDS+1):
            path = BASE/trial/f'event_{step}.json'
            event = read(path)
            assert event['previous_event_sha256'] == previous_hash
            assert canonical(event['before']) == canonical(state)
            request = canonical(make_request(state))
            assert digest(request) == event['request_sha256']
            folder = BASE/'mailbox'/f'{trial}_s{step}'
            assert (folder/'request.json').read_text() == request
            assert (folder/'response.json').read_text() == event['response_raw']
            assert digest(event['response_raw']) == event['response_sha256']
            state = reduce_event(state, event['response_raw'], event['result'])
            assert canonical(state) == canonical(event['after'])
            previous_hash = digest(path.read_bytes())
            checks.append({'trial': trial, 'step': step, 'match': True,
                           'state_sha256': digest(canonical(state))})
    return {'mode': 'recorded receipts; zero model calls and zero verifier calls', 'checks': checks}


def selftest():
    good = {'action':'submit', 'proof':'by\n  trivial', 'hypothesis':'test'}
    bad = ['not json', canonical({**good, 'action':'shell'}), canonical({**good, 'path':'/tmp/x'}),
           canonical({**good, 'proof':'a'*4001}), canonical({**good, 'hypothesis':'a'*241}),
           '{"action":"submit","action":"shell","proof":"by trivial","hypothesis":""}',
           ' '*5001, canonical({**good, 'proof':123})]
    assert parse_response(canonical(good)) == good
    for raw in bad:
        try:
            parse_response(raw)
        except (ValueError, TypeError):
            continue
        raise AssertionError('invalid proposal accepted')
    return {'valid_schema_accepted': True, 'rejected_cases': len(bad)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['init', 'ingest', 'replay', 'selftest', 'environment'])
    p.add_argument('--trial', choices=TRIALS)
    p.add_argument('--step', type=int)
    args = p.parse_args()
    with (BASE/'.controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.action == 'init':
            initialize()
            result = {'initialized': True}
        elif args.action == 'ingest':
            result = ingest(args.trial, args.step)
        elif args.action == 'replay':
            result = replay()
        elif args.action == 'selftest':
            result = selftest()
        else:
            result = environment()
    print(canonical(result), end='')
