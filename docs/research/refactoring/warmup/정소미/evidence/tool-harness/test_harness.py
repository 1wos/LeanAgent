"""State regressions without Lean or model calls: python test_harness.py."""
import tempfile
from pathlib import Path

from harness import Experiment, read, save, sha


def fixture(directory, budget=4, objective='length'):
    directory.mkdir()
    (directory / 'logs').mkdir()
    (directory / 'candidates').mkdir()
    (directory / 'statement.lean').write_text('theorem example_target : True\n')
    (directory / 'reference.lean').write_text('theorem example_target : True := by trivial\n')
    (directory / 'context.lean').write_text('')
    save(directory / 'config.json', {
        'run_id': directory.name, 'problem': 9, 'objective': objective,
        'max_evaluations': budget,
        'input_sha256': {name: sha(directory / name) for name in
                         ('statement.lean', 'reference.lean', 'context.lean')}})
    save(directory / 'state.json', {
        'status': 'active', 'attempts': [], 'selected': None,
        'reference': {'accepted': True, 'proof_tokens': 10,
                      'heartbeat': {'heartbeats': 100}}})
    return Experiment.open(directory)


def check():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        experiment = fixture(root / 'budget')
        calls = []
        def fail(candidate, tag):
            calls.append(tag)
            assert candidate.read_text().startswith('theorem example_target : True := by\n  ')
            return {'accepted': False, 'status': 'verification_failed'}
        experiment._measure = fail
        for index, proof in enumerate([None, '', 'set_option maxHeartbeats 0', 'exact missing']):
            result = experiment.evaluate_candidate(proof)
            assert not result['accepted'] and result['remaining_evaluations'] == 3 - index
            assert len(read(experiment.directory / 'state.json')['attempts']) == index + 1
        assert calls == ['candidate_04']
        assert experiment.evaluate_candidate('trivial')['status'] == 'budget_exhausted'
        summary = experiment.finish()
        assert summary['selected'] == 'reference' and summary['reduction'] == 0
        assert (experiment.directory / 'selected.lean').read_bytes() == (experiment.directory / 'reference.lean').read_bytes()
        assert experiment.finish() == summary
        assert experiment.evaluate_candidate('trivial')['status'] == 'run_closed'
        assert len(experiment.state['attempts']) == 4

        interrupted = fixture(root / 'interrupted', budget=1)
        interrupted.state['attempts'].append({'id': 'candidate_01', 'status': 'running', 'accepted': False})
        interrupted._save()
        restarted = Experiment.open(interrupted.directory)
        assert restarted.state['attempts'][0]['status'] == 'interrupted'
        assert not restarted.state['attempts'][0]['accepted']
        assert restarted.evaluate_candidate('trivial')['status'] == 'budget_exhausted'
        assert restarted.finish()['selected'] == 'reference'

        for objective in ('length', 'heartbeat'):
            selected = fixture(root / objective, budget=2, objective=objective)
            results = iter([
                {'accepted': True, 'status': 'accepted', 'proof_tokens': 12, 'heartbeat': {'heartbeats': 120}},
                {'accepted': True, 'status': 'accepted', 'proof_tokens': 8, 'heartbeat': {'heartbeats': 80}}])
            selected._measure = lambda candidate, tag: next(results)
            selected.evaluate_candidate('trivial')
            selected.evaluate_candidate('exact True.intro')
            assert selected.finish()['selected'] == 'candidate_02'
    print('Harness checks passed: invalid-input budget, closed run, interrupted restart, reference fallback and selection.')


if __name__ == '__main__':
    check()
