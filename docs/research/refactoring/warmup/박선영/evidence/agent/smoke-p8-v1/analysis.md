# P8 어댑터 smoke 준비

목표: 기존 검증 후보를 새 세션 ledger로 재현해 evaluator 연결을 확인한다. 새로운 최적화 발견이 아니다.

## 단계·의존성

- 원본은 `parallelReduction_diamond : Diamond ParallelReduction`이다. 첫 reduction과 두 번째 reduction을 case 분해해 공통 항과 두 경로를 구성한다.
- par/par는 하위 항의 Diamond를 재귀적으로 얻어 `.par`로 조립한다.
- par/red_S는 `Sab_irreducible`에서 `h`를 얻고 `h.2.2`로 형태를 정리한 뒤, 두 번의 par 및 `grind`로 남은 경로를 구성한다.
- 역사적 후보는 해당 분기만 `exact .par (.par h.1 hb') (.par h.2.1 hb')`로 바꾼다. `h.1`, `h.2.1`, `hb'`라는 구체적 증거가 있으므로 `explicit-evidence` 전략의 적용 근거가 있다.
- 다른 분기와 명제는 그대로 둔다. 기존 407→412 tokens, 1,382→1,320 heartbeat는 과거 v4.31.0 관측이지 이번 세션의 측정이 아니다.

## 이번 세션의 실제 상태

`init`의 읽기 전용 환경 검사와 snapshot 저장까지만 수행했다. `baseline` 도구 호출은 Claude Code auto mode classifier가 외부 CSLib 코드 실행 승인을 요구하며 거부했다. Python evaluator와 Lean은 시작되지 않았다. 우회·재시도하지 않았고 `session.json`의 baseline을 `blocked`, `execution=not_started`로 기록했다.

baseline이 없으므로 후보 hypothesis 등록·seal·평가·회고는 수행하지 않았다. 새 heartbeat, 후보 통과, 새 전략 성공을 주장하지 않는다. 이 세션 이후 baseline 거부 기록 기능과 protocol이 보완되어 초기 code fingerprint도 이전 버전이다. 향후 실행이 승인되면 이 기록은 보존하고 최신 코드로 새 세션을 만든다.
