# Lean 평가 도구와 에이전트 실행 모듈

2026-10-18 · 정소미 · Week 3 실행관리·평가·재현

모델이 증명 후보를 작성하고, MCP 도구가 Lean 검증과 측정·기록·선택을 수행하는 실험용 모듈이다. 현재 실행 경로는 **Codex CLI → stdio MCP → Python 평가기 → Lean**이다. 4·9번의 고정 환경에서 실행당 하나의 프로세스가 상태를 기록하는 프로토타입이며, 범용 운영 시스템으로 검증한 범위는 아니다.

- [4번 실행 자료](results/p4/) · [9번 실행 자료](results/p9/)
- [기존 후보 28개 평가](../method-comparison/README.md): 과거 후보를 다시 평가한 별도 실험이다. 이 모듈의 새 후보 생성 실행과 결과를 합산하지 않는다.

## 실제 도구 호출 결과

길이 최소화를 목표로 각 문제를 한 번씩 실행했다. 요청 모델은 `gpt-5.6-sol`이며, CLI에서 실제 모델 식별값을 제공받지 못해 `actual_model=null`로 기록했다.

| 문제 | 참조 길이 | 후보 시도 | 유효 후보 | 최종 선택 | 선택 길이 | 길이 감소율 |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| [4번](results/p4/summary.json) | 851토큰 | 2 | 0 | 참조 증명 | 851토큰 | 0.00% |
| [9번](results/p9/summary.json) | 251토큰 | 3 | 1 | `candidate_03` | 131토큰 | 47.81% |

4번은 두 후보 모두 검증에 실패해 참조 증명을 유지했다. 9번은 첫 후보의 `grind` 실패, 두 번째 후보의 타입 오류를 확인한 뒤 세 번째 후보가 통과했다. 이 실행은 오류 확인·수정·재평가 경로와 실패 시 참조 증명 선택을 확인한 사례다. 각 문제 한 번의 결과이므로 일반적인 모델 성공률로 해석하지 않는다.

MCP 호출은 4번에서 `get_problem` 1회·`evaluate_candidate` 2회·`finish` 1회, 9번에서 각각 1회·3회·1회였다. 두 실행 모두 도구 호출이 완료됐고 에이전트가 직접 `finish`를 호출했다. **도구 호출 완료는 증명 검증 통과와 별도 상태**다. 근거는 각 실행의 `agent.json`과 `state.json`에 있다.

최초 `gpt-6-sol` 요청은 지원되지 않는 모델 오류로 후보 평가 0회, 에이전트 실행 `incomplete`로 종료됐다. [연결 오류 기록](results/provider-error/)으로 별도 보존하며, 위 후보 생성 실험의 시도 수에 포함하지 않는다.

## 세 도구의 계약

| 도구 | 입력 | 반환 및 동작 |
| --- | --- | --- |
| `get_problem` | 없음 | 고정 명제·문맥, `original_proof_body`, 참조 측정값, 목표 지표, 남은 평가 횟수를 반환한다. |
| `evaluate_candidate` | `proof: str` | 바깥 `by` 없는 **tactic 본문만** 받는다. 서버가 고정 명제와 `:= by`, 들여쓴 본문을 결합한다. 검증 결과·오류·길이·heartbeat·남은 횟수를 반환하고 기록한다. |
| `finish` | 없음 | 검증된 후보와 참조 증명 중 설정 지표가 가장 작은 증명을 선택한다. 유효한 개선 후보가 없으면 참조 증명을 유지한다. |

명제·환경·공리 조건과 실제 Lean 컴파일 결과를 기준으로 유효성을 판정한다. 길이는 구문 토큰 수, heartbeat는 검증 작업량 지표다. 에이전트에는 일반 shell·파일 조작 도구를 제공하지 않으며, 후보 검증에는 기존 [검증 절차](../reproducibility/README.md)를 사용한다.

## 환경과 실행

Python 3.10 이상과 `mcp==1.26.0`이 필요하다. 평가 상태 관리와 실행기는 Python 표준 라이브러리를 사용한다. 실제 모델 실행에는 로그인된 **Codex CLI 0.153.2**와 해당 계정에서 지원되는 모델이 필요하다. MCP 서버의 실행 디렉터리 잠금은 `fcntl`을 사용하므로 macOS/Linux를 대상으로 한다.

Lean 프로젝트는 [환경 준비 안내](../reproducibility/README.md#필요한-환경)에 따라 준비한다. 이 모듈은 `p4-4.32`와 `p9-4.32` 두 환경을 사용한다. 아래 명령은 **이 README가 있는 폴더**에서 실행한다.

```sh
python3 -m venv /tmp/leanagent-tools-venv
source /tmp/leanagent-tools-venv/bin/activate
python3 -m pip install -r requirements.txt
cp ../reproducibility/repos.example.json /tmp/leanagent-repos.json
```

복사한 JSON의 경로를 준비한 checkout의 절대 경로로 수정한다. 아래 모델이 실행 계정에서 지원되는지 확인하고, **아직 존재하지 않는 출력 폴더**를 지정한다. 실행 환경에 따라 지원되는 다른 모델로 변경할 수 있다.

```sh
python3 run_agent.py \
  --repos /tmp/leanagent-repos.json \
  --problem 9 \
  --output /tmp/leanagent-tool-p9-new \
  --objective length \
  --max-evaluations 3 \
  --timeout 60 \
  --agent-timeout 600 \
  --model gpt-5.6-sol
```

4번은 `--problem 4`와 새 출력 폴더를 사용한다. `--objective heartbeat`도 지원한다. `--model`을 생략하면 CLI 기본 설정을 사용하며, 실제 사용 모델이 확인됐다는 뜻은 아니다.

`--max-evaluations`는 실패·수정 시도를 포함한 **후보 평가 호출 상한**이다. 참조 증명 검증은 이 횟수에 포함하지 않는다. 모델 API 요청 횟수나 금액 상한으로 해석하지 않는다. `--timeout`은 Lean 컴파일 한 번의 제한이며, 도구는 전체 검증과 heartbeat 측정을 수행하므로 호출 제한을 `2 × timeout + 40초`로 설정한다. 에이전트 제한은 이보다 길어야 하며, 실행기는 `agent-timeout > 2 × timeout + 45초`를 요구한다. 종료 신호 후 정리 대기 시간이 추가될 수 있다.

## 프롬프트와 연결 범위

[prompt_pack.py](prompt_pack.py)는 공통 실행 원칙인 **META**, 후보 작성 절차인 **CREATE**, 오류 수정 절차인 **REPAIR**와 실행 조건을 조합한다. 현재 실행기는 이 프롬프트를 Codex CLI에 전달한다. 제공자별 프롬프트 파일은 모델 호출 없이 내보낼 수 있다.

```sh
python3 prompt_pack.py \
  --provider all \
  --objective length \
  --max-evaluations 3 \
  --output /tmp/leanagent-prompt-pack
```

OpenAI Responses, Anthropic Messages, Google GenAI Python SDK에 맞춘 **프롬프트 필드**를 각각 JSON으로 저장한다. 모델·인증·생성 제한·도구 등록과 도구 응답을 연결하는 반복 실행은 포함하지 않는다. 세 제공자 SDK의 실제 연결이나 호출을 완료한 결과가 아니다. A2A와 Langfuse 공식 연동도 구현하지 않았다.

## 기록과 상태 해석

| 파일 | 확인할 내용 |
| --- | --- |
| `config.json`, `environment.json` | 고정 문제·목표·제한, 프로젝트와 의존성, 입력·실행 코드의 SHA-256 |
| `events.jsonl` | 평가 도구의 입력·반환값·실행 상태 추적 |
| `agent-events.jsonl`, `agent-stderr.log`, `agent.json` | CLI 이벤트와 오류, 모델 요청값, 사용량 보고, 종료 상태 |
| `state.json`, `candidates/`, `logs/` | 후보별 상태·증명·Lean 원시 로그와 해시 |
| `summary.json`, `selected.lean` | 선택 결과·감소율·선택 증명의 해시 |

`requested_model`은 요청한 값이다. `actual_model`이 `null`이고 `model_status`가 `not_observed`이면 실제 모델을 확인하지 못한 상태로 읽는다. `reported_usage`는 CLI가 보고한 토큰 사용량이며 내부 모델 API 호출 수를 뜻하지 않는다. 금액을 제공받지 못한 `cost_usd`는 `null`로 남긴다.

입력 거부, 검증 실패, 실행 오류와 중단 상태를 구분해 저장한다. 실행 도중 남은 `running` 후보는 다시 열 때 `interrupted`로 기록하며, 해당 평가 횟수를 복구하지 않는다. 모델이 정상적으로 `finish`를 호출하지 못했더라도 실행기가 유효한 참조·후보로 결과를 정리할 수 있다. 이때 **`summary.json` 생성과 에이전트 정상 완료는 구분**하며, `agent.json`의 `status`, `agent_called_finish`, `finalized_by`, `timed_out`를 함께 확인한다. 실행기 자체가 강제 종료된 경우 자동 복구를 보장하지 않는다.

상태·예산·선택 규칙은 모델이나 Lean 호출 없이 다음 명령으로 확인한다.

```sh
python3 test_harness.py
```

저장된 실행의 입력·후보·로그·선택 파일 해시, 시도 수와 유효 수, 선택 규칙과 감소율은 다음 명령으로 다시 검사한다. Lean 검증이나 모델 호출을 수행하지 않는 자료 일관성 검사다.

```sh
python3 audit_run.py results/p4
python3 audit_run.py results/p9
```

현재 대상은 고정된 두 문제와 기존 로컬 빌드 환경이다. 여러 실행자가 동시에 쓰는 분산 실행, 독립된 컴퓨터·새 설치 환경에서의 재현은 확인하지 않았다.
