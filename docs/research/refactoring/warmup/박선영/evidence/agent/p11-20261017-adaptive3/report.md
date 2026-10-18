# P11 순차 리팩터링 실험 보고서

2026-10-17 · 세션 `p11-20261017-adaptive3` · 최대 후보 3개 / 실제 평가 3개

## 결론

**평가된 세 후보 중 최선은 [a003](attempts/a003/candidate.lean)이다.** 새로 측정한 원본 대비 heartbeat는 **45,537 → 38,337 (15.81% 감소)**, proof tokens는 **1,906 → 1,379 (27.65% 감소)**했다. 기존 selected를 재현한 a001보다도 각각 **7.92%, 16.73% 감소**했다.

세 후보 모두 명제 보존·금지 패턴·Lean 컴파일·공리·별도 heartbeat 측정을 통과했다. 단, **a003 평가 이후 skill 파일 drift가 감지되어 마지막 helper review 저장은 거절되었다.** 따라서 평가 완료와 세션 마감 완료를 구분한다. 현재 원장에는 `best=a003`, a001/a002는 `reviewed`, a003는 `evaluated/passed`로 남아 있다. 마지막 해석은 이 보고서에 남기며, helper reflection을 완료했다고 주장하지 않는다.

기존 `P11/selected.lean`, `candidates.json`, 작성자 루트의 기존 `report.md`, 발표 HTML, legacy metrics는 갱신하지 않았다. 세션 best는 최종 채택이나 공식 점수가 아니다.

## 환경과 평가 방법

- 정리: `Binius.BinaryBasefold.fold_advances_evaluation_poly`.
- 준비된 기존 checkout: `/Users/parksunyoung/orca/workspaces/LeanAgent/sunyoung-week2/solution/.lake-env/ArkLib`.
- Lean **v4.31.0**, ArkLib 커밋 `c1712f6c496d0aef04f09bae42aec13811b3273f`.
- 원본 소스: `ArkLib/ProofSystem/Binius/BinaryBasefold/Prelude.lean`.
- 정책: [동결 snapshot](../../metrics/agent/p11-20261017-adaptive3/policy-snapshot.json), v1. 유효성 → heartbeat 최소 → 동률일 때 tokens 최소.
- 후보 예산 3회, subprocess별 timeout 180초, 연속 무개선 한계 3회. 기준선은 별도 1회.
- 원본 전체 파일 문맥에서 대상 선언만 교체하고 검증했다. 대상 정리의 기존 `.olean`을 import하여 검증을 대신하지 않았다.
- 모든 실행은 `python3 -I .../experiment.py`의 baseline/evaluate 경로를 사용했다. 다운로드, checkout 변경, 권한 설정 변경, 외부 LLM API 호출 없음.
- 전체 명제 prefix와 금지 패턴 검사, `#print axioms`, 별도 `#count_heartbeats` 측정 유지.
- 아래 tokens는 공유 proof tokenizer의 값이며 LLM 토큰이나 API 비용이 아니다.

## 실측 결과

감소율은 양수가 개선을 뜻한다. 부모 관계는 `reference → a001 → a002 → a003`이다.

| 실행 | 변경 / 종류 | 검증 | heartbeat | 원본 대비 감소 | 부모 대비 감소 | proof tokens | 원본 대비 감소 | 부모 대비 감소 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reference | 새 기준선 | 통과 | 45,537 | — | — | 1,906 | — | — |
| a001 | 미사용 계수 정의 제거 / **기존 결과 재현** | 통과 | 41,636 | 8.5667% | 8.5667% | 1,656 | 13.1165% | 13.1165% |
| a002 | 마지막 계수별 등식 재구성 / 새 실험 | 통과 | 39,123 | 14.0852% | 6.0356% | 1,441 | 24.3966% | 12.9831% |
| **a003** | 중간 calc의 두 ring 단계 통합 / 새 실험 | **통과** | **38,337** | **15.8113%** | **2.0090%** | **1,379** | **27.6495%** | **4.3026%** |

원본과 세 후보의 공리 집합은 모두 `Classical.choice`, `Quot.sound`, `propext`이다. **대상 정리의 `sorryAx` 의존성이나 새 공리 추가는 없다.** 전체 파일의 다른 기존 선언에서 발생하는 `declaration uses sorry` 경고와 deprecated/linter 경고는 로그에 남아 있다. 이를 숨기거나 전체 ArkLib가 sorry-free라고 주장하지 않는다.

## 순차 선택과 성공 이유

### 1. a001 — 이전 결과를 재현해 부모 확보

- 사전 근거: 기존 작성자 보고서·원본·selected·result JSON을 읽고, `P₀_coeffs/P₁_coeffs`가 후속 계산에 사용되지 않으며 실제 `P₀/P₁`는 별도의 refinement 정의임을 확인했다.
- 등록 전략: `remove-unused`, `kind=reproduction`, 부모 `reference`.
- 변경: 두 미사용 `set` 블록과 소개 주석만 제거한 기존 selected를 그대로 복사해 새 세션에서 검증했다.
- 관측: 기존 41,636 heartbeat / 1,656 tokens를 재현했고, 새 원본보다 3,901 heartbeat / 250 tokens 줄었다.
- 해석: 필요 없는 지역 정의 및 그 인덱스 증명의 elaboration을 제거한 효과와 일치한다. **기존 성공의 재현이지 새 발견이 아니다.**
- 다음 선택: 성공한 a001을 부모로 유지하고, 아직 남은 마지막 계수별 등식 블록 하나만 변경한다.

[가설](attempts/a001/hypothesis.json) · [후보](attempts/a001/candidate.lean)

### 2. a002 — C의 준동형 법칙과 ring으로 계수별 등식 증명

- 사전 근거: a001의 통과 결과와 review를 읽었다. 마지막 `sum_congr` 내부는 같은 basis에 붙는 계수들의 가환환 항등식인데, 기존 코드는 `conv`에서 계수와 `Fin` 인덱스 증명을 다시 적고 있었다.
- 등록 전략: `restructure-algebra`, 부모 `a001`.
- 변경 범위: 마지막 `intro j hj` 뒤의 계산 블록만 다음으로 교체했다. 다른 qMap/fiber/main calc는 보존했다.

```lean
      simp only [Polynomial.C_add, Polynomial.C_mul]
      ring
```

- 관측: 부모 대비 **2,513 heartbeat / 215 tokens 감소**, 검증 통과.
- 성공 이유: `C`가 덧셈·곱셈을 보존한다는 법칙으로 목표를 정규화하면 `ring`으로 등식을 닫을 수 있었다. 특정 계수의 인덱스 증명을 다시 작성하고 곱셈 순서를 수동 조정할 필요가 없어졌다.
- 해석 한계: 단일 블록 교체의 전체 선언 비용 차이를 측정했다. 각 `conv`, 인덱스 elaboration, `ring`에 비용이 얼마나 귀속되는지는 profiling하지 않았다.
- 다음 선택: 같은 전략을 무조건 일반화하지 않고, 별개 main calc의 중복 ring 정규화도 줄어드는지 마지막 예산으로 검사한다.

[가설](attempts/a002/hypothesis.json) · [후보](attempts/a002/candidate.lean)

### 3. a003 — 연속 두 ring 단계를 하나로 통합

- 사전 근거: a002의 39,123 heartbeat 결과와 review를 읽었다. main calc에서 같은 항들의 전개형 중간 등식을 거쳐 다시 `x₁-x₀`로 묶는 두 연속 `ring` 단계가 있었다.
- 등록 전략: `restructure-algebra`, 부모 `a002`.
- 변경 범위: 전개형 중간 `calc` 등식 하나를 생략하고, 바로 아래 공통인자 형태로 가는 등식을 `ring` 한 번으로 증명하도록 했다. fiber 차이 증명과 a002의 마지막 계수 계산은 그대로 유지했다.

```lean
    _ = P₀.eval y.val * ((1 - r_chal) * (x₁.val - x₀.val)) +
        P₁.eval y.val * ((x₁.val - x₀.val) * r_chal) := by ring
```

- 관측: 부모 대비 **786 heartbeat / 62 tokens 감소**, 검증 통과. a003의 평가 종료 시각은 `2026-10-17T08:05:36.369527+00:00`이다.
- 성공 이유: 중간 전개식을 따로 증명하지 않아도 환 항등식으로 목표가 닫혔다. 이 경우에는 `ring` 호출과 중간 등식 elaboration을 줄인 구조가 실제 비용 감소로 이어졌다.
- 한계: a002 위에서의 증분 효과다. 원본에서 독립적으로 적용한 효과나 다른 정리에서도 같은 결과를 보장하지 않는다.
- 다음 행동: 후보 예산 3/3 소진으로 추가 후보를 만들지 않는다. 아래 drift 때문에 helper review/reflect도 더 진행하지 않는다.

[가설](attempts/a003/hypothesis.json) · [최선 후보](attempts/a003/candidate.lean)

## 실패·중단 사유와 상태 구분

**Lean 후보 실패는 0개**다. 실패 사례를 만들기 위해 불필요한 후보를 추가하지 않았다. 다음은 증명 실패와 별개의 운영 문제다.

1. 주변 경계 정리 탐색 에이전트가 API 도구 호출 파싱 오류로 중단됐다. 이것은 Lean 컴파일 실패나 전략의 수학적 실패가 아니다. 확인되지 않은 경계 정리를 후보에 사용하지 않았고 qMap/fiber 블록을 보존했다.
2. a003의 평가·측정·원장 저장까지 성공한 뒤 `review` 호출에서 다음 오류가 발생했다.

```text
Skill/evaluator/benchmark drift; start a new session
```

읽기 전용 해시 대조에서 변경 파일은 `.claude/skills/lean-refactor/SKILL.md`였다.

- 세션 시작 해시: `898f0aea55c3b1d36d68b33645166e7fe8849971fd77dc30d9e27fffb34cfe0d`
- review 거절 후 관측 해시: `d9fb7b8f2c57e095304dfebb57254c9708072855d8ae9430cd619a31f7f6e2e5`

이 실험에서는 해당 skill 파일을 편집하지 않았다. 변경 주체·의도는 확인하지 않았다. drift를 우회하거나 snapshot/원장을 수동 수정하거나 파일을 되돌리지 않았다. JSON 요약용 후속 파이프도 정상 JSON을 받지 못해 `JSONDecodeError`가 났는데, 이는 review 거절에 따른 후속 오류이지 Lean 실패가 아니다.

- a001/a002: helper review 저장 완료.
- a003: `status=passed`, `phase=evaluated`, `improved=true`; helper review 저장 미완료.
- `best=a003`은 평가 시 이미 저장된 상태다.
- helper `reflect`: **미실행**. 미완료 review와 drift 상태에서 강행하지 않았으며 reflection 파일을 임의로 만들지 않았다.
- 중단 후 후보·가설·결과의 저장 해시 **11개 모두 일치**함을 읽기 전용으로 확인했다. 이는 현재 환경 전체를 재검증했다는 뜻이 아니다.
- `git diff --check` 통과. 본 작업에서 검증기 코드를 수정하지 않았으며 Python 단위 테스트를 새로 실행하지 않았다.

## 조건부 회고 — helper reflection 아님

관측은 기존 최적화 재현 1회와 누적 대수 재구성 2회다. 세 후보가 서로 다른 전략 3개를 입증한 것은 아니다.

정책 제안: `restructure-algebra` 적용 조건에 “계수의 환 준동형 법칙으로 인덱스 재기술을 피할 수 있는 합의 항별 등식”, “동일 항에 대한 연속 ring 정규화의 중간 등식 생략”을 검토 사례로 추가할 수 있다. **활성 정책은 변경하지 않았다.**

반례·추가 검증 조건: 단일 ring 목표가 커지면 오히려 비용이 늘 수 있고, 비가환 구조나 인덱스의 definitional equality가 맞지 않으면 이번 형태는 실패할 수 있다. 안정된 skill 상태의 새 세션에서 기준선을 다시 만들고 독립 ablation과 나머지 지정 버전(v4.29.0/v4.30.0)을 확인해야 일반화 범위를 넓힐 수 있다. 이번 요청에서는 추가 실행하지 않는다.

## 원시 근거

- [분석과 proof map](analysis.md)
- [세션 원장: best·비교율·저장된 review](../../metrics/agent/p11-20261017-adaptive3/session.json)
- [기준선 JSON](../../metrics/agent/p11-20261017-adaptive3/baseline/result.json) · [검증 로그](../../metrics/agent/p11-20261017-adaptive3/baseline/check.log) · [heartbeat 로그](../../metrics/agent/p11-20261017-adaptive3/baseline/heartbeat.log)
- [a001 JSON](../../metrics/agent/p11-20261017-adaptive3/attempts/a001/result.json) · [검증 로그](../../metrics/agent/p11-20261017-adaptive3/attempts/a001/check.log) · [heartbeat 로그](../../metrics/agent/p11-20261017-adaptive3/attempts/a001/heartbeat.log)
- [a002 JSON](../../metrics/agent/p11-20261017-adaptive3/attempts/a002/result.json) · [검증 로그](../../metrics/agent/p11-20261017-adaptive3/attempts/a002/check.log) · [heartbeat 로그](../../metrics/agent/p11-20261017-adaptive3/attempts/a002/heartbeat.log)
- [a003 JSON](../../metrics/agent/p11-20261017-adaptive3/attempts/a003/result.json) · [검증 로그](../../metrics/agent/p11-20261017-adaptive3/attempts/a003/check.log) · [heartbeat 로그](../../metrics/agent/p11-20261017-adaptive3/attempts/a003/heartbeat.log)

공식 서버 점수, 전체 버전 호환성, 일반화된 학습 성능, wall-clock 속도 향상은 주장하지 않는다. 완료된 로컬 측정 결과와 중단된 기록 절차를 분리해 보존한다.
