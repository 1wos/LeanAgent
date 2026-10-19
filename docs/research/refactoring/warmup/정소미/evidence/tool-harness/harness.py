"""Local, single-writer evaluation state shared by the MCP server and runner."""
from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
import textwrap
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
sys.path.insert(0, str(EVIDENCE / 'reproducibility'))
import run_replay as replay


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Experiment:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.config = read(self.directory / 'config.json')
        self.state = read(self.directory / 'state.json')
        # ponytail: one local process writes a run; use a transactional store for multi-worker runs.
        self.lock = threading.RLock()

    @classmethod
    def create(cls, directory, repo, problem, objective='length', max_evaluations=3, timeout=60):
        if problem not in (4, 9) or objective not in ('length', 'heartbeat'):
            raise ValueError('Supported problems: 4, 9; objectives: length, heartbeat')
        if not 1 <= max_evaluations <= 20 or not 1 <= timeout <= 300:
            raise ValueError('max_evaluations must be 1..20; timeout must be 1..300 seconds')
        directory, repo = Path(directory).resolve(), Path(repo).resolve()
        directory.mkdir(parents=True, exist_ok=False)
        (directory / 'logs').mkdir()
        (directory / 'candidates').mkdir()
        protocol_path = EVIDENCE / 'method-comparison/protocol.json'
        protocol = read(protocol_path)
        spec = protocol['environments'][f'p{problem}-4.32']
        config = dict(schema_version=1, run_id=str(uuid.uuid4()), created_utc=timestamp(),
                      problem=problem, repo=str(repo), spec=spec, objective=objective,
                      max_evaluations=max_evaluations, timeout_seconds=timeout,
                      expected_axioms=protocol['expected_axioms'])
        save(directory / 'config.json', config)
        save(directory / 'state.json', {'status': 'initializing', 'attempts': [], 'selected': None})
        experiment = cls(directory)
        try:
            environment = replay.check_environment(repo, spec)
            if sha(EVIDENCE / spec['statement']) != spec['statement_sha256']:
                raise ValueError('Statement hash mismatch')
            reference = next(x for x in protocol['inputs'] if x['problem'] == problem and x['role'] == 'reference')
            reference_path = EVIDENCE / reference['path']
            if sha(reference_path) != reference['sha256']:
                raise ValueError('Reference hash mismatch')
            source = repo / spec['source_file']
            (directory / 'context.lean').write_text('\n'.join(source.read_text().splitlines()[:spec['start']-1]))
            (directory / 'reference.lean').write_bytes(reference_path.read_bytes())
            (directory / 'statement.lean').write_bytes((EVIDENCE / spec['statement']).read_bytes())
            inputs = ['reference.lean', 'statement.lean', 'context.lean']
            config['input_sha256'] = {name: sha(directory / name) for name in inputs}
            save(directory / 'config.json', config)
            save(directory / 'environment.json', {
                'environment': environment, 'python': platform.python_version(),
                'platform': platform.platform(), 'protocol_sha256': sha(protocol_path),
                'scripts_sha256': {str(p.relative_to(EVIDENCE)): sha(p) for p in
                    [HERE / 'harness.py', HERE / 'tool_server.py', HERE / 'run_agent.py',
                     EVIDENCE / 'reproducibility/run_replay.py', EVIDENCE / 'verify_candidate.py',
                     EVIDENCE / 'proof_tokens.py']},
                'scope': 'Existing local build cache; not an independent clean-install reproduction.'})
            result = experiment._measure(directory / 'reference.lean', 'reference')
            if not result['accepted']:
                raise ValueError('Reference verification failed; no candidate evaluation permitted')
            experiment.state.update(status='active', reference=result)
            experiment._save()
            experiment._event('run_started', {'problem': problem, 'reference': result})
            return experiment
        except Exception as error:
            experiment.state.update(status='initialization_failed', error=f'{type(error).__name__}: {error}')
            experiment._save()
            raise

    @classmethod
    def open(cls, directory):
        experiment = cls(directory)
        for name, expected in experiment.config.get('input_sha256', {}).items():
            if sha(experiment.directory / name) != expected:
                raise ValueError(f'Run input changed: {name}')
        for attempt in experiment.state['attempts']:
            if attempt['status'] == 'running':
                attempt.update(status='interrupted', accepted=False)
                experiment._event('evaluation_interrupted', {'attempt': attempt['id']})
        experiment._save()
        return experiment

    def _save(self):
        save(self.directory / 'state.json', self.state)

    def _event(self, kind, data):
        event = {'schema_version': 1, 'run_id': self.config['run_id'], 'time_utc': timestamp(),
                 'event': kind, **data}
        with (self.directory / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + '\n')

    def _measure(self, candidate, tag):
        log = self.directory / 'logs' / f'{tag}.log'
        result = replay.run_one(Path(self.config['repo']), self.config['spec'], candidate, tag,
                                self.config['timeout_seconds'], log, self.config['expected_axioms'])
        result['log'] = str(log.relative_to(self.directory))
        result['log_sha256'] = sha(log)
        return result

    def get_problem(self):
        with self.lock:
            statement = (self.directory / 'statement.lean').read_text().rstrip('\n')
            reference = (self.directory / 'reference.lean').read_text()
            suffix = reference[len(statement):].lstrip()
            if not suffix.startswith(':= by'):
                raise ValueError('This prototype supports tactic proofs only')
            result = {'problem': self.config['problem'], 'statement': statement,
                      'original_proof_body': textwrap.dedent(suffix[len(':= by'):]).strip(),
                      'source_context': (self.directory / 'context.lean').read_text(),
                      'objective': self.config['objective'], 'reference_metrics': self.state['reference'],
                      'remaining_evaluations': self.config['max_evaluations'] - len(self.state['attempts']),
                      'input_contract': 'Supply only tactic body, without outer by or any declarations.'}
            self._event('tool_result', {'tool': 'get_problem', 'result': result})
            return result

    def evaluate_candidate(self, proof):
        with self.lock:
            if self.state['status'] != 'active':
                result = {'accepted': False, 'status': 'run_closed'}
                self._event('tool_rejected', {'tool': 'evaluate_candidate', 'result': result})
                return result
            if len(self.state['attempts']) >= self.config['max_evaluations']:
                result = {'accepted': False, 'status': 'budget_exhausted', 'remaining_evaluations': 0}
                self._event('tool_rejected', {'tool': 'evaluate_candidate', 'result': result})
                return result
            tag = f"candidate_{len(self.state['attempts']) + 1:02d}"
            attempt = {'id': tag, 'status': 'running', 'accepted': False, 'started_utc': timestamp()}
            self.state['attempts'].append(attempt)
            self._save()  # Reserve the slot before validation or compilation; failure still counts.
            self._event('tool_started', {'tool': 'evaluate_candidate', 'attempt': tag, 'proof': proof})
            started = time.monotonic()
            try:
                if not isinstance(proof, str) or not proof.strip() or len(proof.encode()) > 65536:
                    raise ValueError('Expected a nonempty tactic body of at most 65536 UTF-8 bytes')
                proof = textwrap.dedent(proof).strip()
                stripped = replay.proof_tokens.remove_comments(proof)
                if re.search(r'(?m)^\s*(?:#|(?:theorem|lemma|example|namespace|section|end|import|set_option)\b)', stripped):
                    raise ValueError('Commands, declarations and environment changes are not accepted')
                statement = (self.directory / 'statement.lean').read_text().rstrip('\n')
                candidate = self.directory / 'candidates' / f'{tag}.lean'
                candidate.write_text(statement + ' := by\n' + textwrap.indent(proof, '  ') + '\n')
                attempt.update(candidate=str(candidate.relative_to(self.directory)), candidate_sha256=sha(candidate))
                result = self._measure(candidate, tag)
                attempt.update(result)
            except ValueError as error:
                attempt.update(status='invalid_input', accepted=False, error=str(error))
            except Exception as error:
                attempt.update(status='execution_error', accepted=False, error=f'{type(error).__name__}: {error}')
            attempt.update(finished_utc=timestamp(), seconds=round(time.monotonic() - started, 3))
            self._save()
            result = dict(attempt, remaining_evaluations=self.config['max_evaluations'] - len(self.state['attempts']))
            self._event('tool_result', {'tool': 'evaluate_candidate', 'attempt': tag, 'result': result})
            return result

    def finish(self):
        with self.lock:
            if self.state['status'] == 'completed':
                return read(self.directory / 'summary.json')
            if self.state['status'] != 'active':
                raise ValueError('No valid initialized run to finish')
            reference = dict(self.state['reference'], id='reference', candidate='reference.lean')
            valid = [reference] + [a for a in self.state['attempts'] if a['accepted']]
            metric = self.config['objective']
            def score(a):
                return a['proof_tokens'] if metric == 'length' else a['heartbeat']['heartbeats']
            selected = min(valid, key=lambda a: (score(a), a['proof_tokens'], a['id'] != 'reference', a['id']))
            summary = {'schema_version': 1, 'run_id': self.config['run_id'], 'problem': self.config['problem'],
                       'objective': metric, 'attempts': len(self.state['attempts']),
                       'accepted': sum(a['accepted'] for a in self.state['attempts']),
                       'selected': selected['id'], 'selected_candidate': selected['candidate'],
                       'selected_cost': score(selected), 'reference_cost': score(reference),
                       'reduction': 1 - score(selected) / score(reference),
                       'cost_usd': None, 'cost_status': 'not_reported', 'finished_utc': timestamp()}
            (self.directory / 'selected.lean').write_bytes((self.directory / selected['candidate']).read_bytes())
            summary['selected_sha256'] = sha(self.directory / 'selected.lean')
            save(self.directory / 'summary.json', summary)
            self.state.update(status='completed', selected=selected['id'])
            self._save()
            self._event('run_completed', {'summary': summary})
            return summary
