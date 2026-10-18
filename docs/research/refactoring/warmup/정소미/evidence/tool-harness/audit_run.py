"""Recompute a saved run's selection and check its files without Lean or a model call."""
from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path

from harness import read, sha


def audit(directory):
    directory = Path(directory)
    config, state, summary = (read(directory / name) for name in ('config.json', 'state.json', 'summary.json'))
    assert config['run_id'] == summary['run_id'], 'run ID mismatch'
    assert state['status'] == 'completed', 'evaluation not finalized'
    for name, expected in config['input_sha256'].items():
        assert sha(directory / name) == expected, f'input changed: {name}'
    attempts = state['attempts']
    assert len(attempts) <= config['max_evaluations'], 'evaluation budget exceeded'
    assert len({a['id'] for a in attempts}) == len(attempts), 'duplicated attempt ID'
    for item in [state['reference'], *attempts]:
        if 'candidate_sha256' in item and 'candidate' in item:
            candidate = directory / item['candidate']
            # Existing verifier hashes the declaration after removing final newlines.
            expected = hashlib.sha256(candidate.read_text().rstrip('\n').encode()).hexdigest() if 'name' in item else sha(candidate)
            assert expected == item['candidate_sha256'], 'candidate changed'
        if 'log_sha256' in item:
            assert sha(directory / item['log']) == item['log_sha256'], 'verification log changed'
    reference = dict(state['reference'], id='reference', candidate='reference.lean')
    valid = [reference] + [a for a in attempts if a['accepted']]
    def score(a):
        return a['proof_tokens'] if config['objective'] == 'length' else a['heartbeat']['heartbeats']
    selected = min(valid, key=lambda a: (score(a), a['proof_tokens'], a['id'] != 'reference', a['id']))
    assert summary['selected'] == state['selected'] == selected['id'], 'selection differs'
    assert summary['attempts'] == len(attempts), 'denominator differs'
    assert summary['accepted'] == sum(a['accepted'] for a in attempts), 'acceptance count differs'
    assert summary['selected_cost'] == score(selected) and summary['reference_cost'] == score(reference)
    assert math.isclose(summary['reduction'], 1-score(selected)/score(reference)), 'reduction differs'
    assert sha(directory / 'selected.lean') == summary['selected_sha256'], 'selected file changed'
    assert (directory / 'selected.lean').read_bytes() == (directory / selected['candidate']).read_bytes()
    agent = read(directory / 'agent.json') if (directory / 'agent.json').exists() else {}
    if agent.get('prompt_sha256'):
        assert sha(directory / 'prompt.txt') == agent['prompt_sha256'], 'prompt changed'
    return {'files_and_selection': 'passed', 'problem': config['problem'],
            'evaluation_status': state['status'], 'agent_status': agent.get('status', 'not_run'),
            'attempts': len(attempts), 'selected': selected['id'],
            'scope': 'Saved artifact consistency only; does not rerun Lean or the model.'}


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    print(json.dumps(audit(parser.parse_args().run_directory), ensure_ascii=False, indent=2))
