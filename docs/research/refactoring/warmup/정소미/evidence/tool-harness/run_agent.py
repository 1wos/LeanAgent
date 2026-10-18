"""Run a real CLI agent against the local Lean evaluation MCP tools."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from harness import Experiment, HERE, read, save, sha, timestamp
from prompt_pack import build_prompt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--problem', required=True, type=int, choices=[4, 9])
    parser.add_argument('--repos', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--objective', choices=['length', 'heartbeat'], default='length')
    parser.add_argument('--max-evaluations', type=int, default=3)
    parser.add_argument('--timeout', type=int, default=60, help='Seconds per Lean compilation')
    parser.add_argument('--agent-timeout', type=int, default=600)
    parser.add_argument('--model', help='Explicit CLI model; omitted uses the CLI default')
    args = parser.parse_args()
    if args.agent_timeout <= 2 * args.timeout + 45:
        parser.error('agent-timeout must exceed 2*timeout+45')
    repo = Path(read(args.repos)[f'p{args.problem}-4.32']).expanduser()
    output = args.output.resolve()
    experiment = Experiment.create(output, repo, args.problem, args.objective, args.max_evaluations, args.timeout)
    prompt = build_prompt(args.objective, args.max_evaluations)
    (output / 'prompt.txt').write_text(prompt)
    argv = ['codex', 'exec', '--ignore-user-config', '--ephemeral', '--json',
            '--skip-git-repo-check', '-C', str(output), '-s', 'read-only',
            '-c', 'approval_policy="never"', '-c', 'features.shell_tool=false',
            '-c', 'features.unified_exec=false',
            '-c', 'mcp_servers.lean_eval.command=' + json.dumps(sys.executable),
            '-c', 'mcp_servers.lean_eval.args=' + json.dumps([str(HERE / 'tool_server.py'), '--run-dir', str(output)]),
            '-c', 'mcp_servers.lean_eval.startup_timeout_sec=20',
            '-c', f'mcp_servers.lean_eval.tool_timeout_sec={2 * args.timeout + 40}',
            '-c', 'mcp_servers.lean_eval.required=true']
    if args.model:
        argv += ['--model', args.model]
    argv += ['-']
    metadata = {'schema_version': 1, 'backend': 'codex_cli_mcp', 'requested_model': args.model,
                'actual_model': None, 'model_status': 'not_observed', 'started_utc': timestamp(),
                'cli_version': subprocess.check_output(['codex', '--version'], text=True).strip(),
                'mcp_version': importlib.metadata.version('mcp'), 'command': argv,
                'prompt_sha256': sha(output / 'prompt.txt'), 'prompt_module_sha256': sha(HERE / 'prompt_pack.py'),
                'cost_usd': None, 'cost_status': 'not_reported_by_cli',
                'agent_timeout_seconds': args.agent_timeout}
    save(output / 'agent.json', metadata)
    started = time.monotonic()
    timed_out = False
    with (output / 'agent-events.jsonl').open('w') as events, (output / 'agent-stderr.log').open('w') as errors:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=events, stderr=errors,
                                   text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=args.agent_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2 * args.timeout + 40)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    usage, calls, errors = [], {}, []
    for line in (output / 'agent-events.jsonl').read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append({'type': 'malformed_cli_event'})
            continue
        if event.get('type') == 'turn.completed':
            usage.append(event.get('usage', {}))
        if event.get('type') in ('turn.failed', 'error'):
            errors.append(event)
        item = event.get('item', {})
        if item.get('type') == 'mcp_tool_call':
            calls[item['id']] = {'server': item.get('server'), 'tool': item.get('tool'), 'status': item.get('status')}
    metadata.update(finished_utc=timestamp(), seconds=round(time.monotonic()-started, 3),
                    exit_code=process.returncode, timed_out=timed_out, reported_usage=usage,
                    mcp_calls=list(calls.values()), errors=errors,
                    usage_scope='CLI turn usage; not the count of internal model API requests.')
    experiment = Experiment.open(output)
    metadata['agent_called_finish'] = experiment.state['status'] == 'completed'
    if experiment.state['status'] == 'active':
        experiment.finish()
        metadata['finalized_by'] = 'runner_after_agent_exit'
    else:
        metadata['finalized_by'] = 'agent'
    metadata['status'] = ('completed' if process.returncode == 0 and not timed_out and not errors
                          and metadata['agent_called_finish'] else 'incomplete')
    save(output / 'agent.json', metadata)
    print(json.dumps({'status': metadata['status'], 'output': str(output),
                      'summary': read(output / 'summary.json')}, ensure_ascii=False))
    return 0 if metadata['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
