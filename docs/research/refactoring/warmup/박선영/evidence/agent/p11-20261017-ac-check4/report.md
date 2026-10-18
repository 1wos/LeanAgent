# P11 구조 변경 A/C 분리 확인 실험

작성: 2026-10-17 · 세션 `p11-20261017-ac-check4` · 마지막 포함 시도 `a004` · 모든 평가/review/회고 완료

## 1. 결론

**이 P11의 고정 환경에서는 C가 A 없이도 heartbeat를 줄였다.** B→B+C는 **41,636→40,850**, 즉 **786 heartbeat(1.8878%) 감소**했다. A가 있는 경우의 C 추가 효과도 B+A→B+A+C에서 **39,123→38,337**, 즉 **786 heartbeat(2.0090%) 감소**였다. 두 감소율의 차이는 출발 값이 다르기 때문이다.

네 후보 모두 명제 보존·전체 문맥 컴파일·공리·별도 heartbeat 검사를 통과했다. 실패/중단/재시도 없이 **고정 예산 4/4개**를 사용했고 원본 baseline은 별도로 새로 측정했다. 비교 부모는 B의 경우 reference, 나머지 세 경우 모두 **B(a001)**로 명시했다.

세션 best는 **[a004 = B+A+C](attempts/a004/candidate.lean)**: 38,337 heartbeat / 1,379 proof tokens이다. 원본 대비 각각 15.8113% / 27.6495%, B 대비 각각 7.9234% / 16.7271% 감소했다. 이것은 지정 네 조건 안에서의 최선이며 새 최적화 발견이나 전역 최적성은 아니다. 기존 selected와 발표자료는 변경하지 않았다.

## 2. 질문과 사전 고정 설계

- B: 미사용 `P₀_coeffs/P₁_coeffs` 및 소개 주석만 제거한 기존 후보.
- A: 마지막 `sum_congr`의 `intro j hj` 다음 계산을 `simp only [Polynomial.C_add, Polynomial.C_mul]`와 `ring`으로 바꾸는 기존 변경. 기존 `h_j_lt` 삭제도 이 블록 변경에 포함한다.
- C: main calc의 연속 두 ring 단계 중 전개형 중간 등식 3행을 없애고 바로 `x₁-x₀`로 묶는 기존 변경.

[이전 세션 보고서](../p11-20261017-adaptive3/report.md)·분석·가설·후보·측정 JSON·review를 읽었다. 이전 실험은 B→B+A→B+A+C의 누적 순서여서 **B+C가 없었다.** 따라서 C의 효과가 A 없이도 나타나는지 확인하는 것이 이번 목적이며, 결과에 따라 새로운 최적화를 탐색하지 않았다.

[실행 전 분석/허용 범위](analysis.md)에 네 조건을 고정하고 매 후보 작성·복사 전에 helper `plan`으로 가설과 허용 diff를 등록했다. 실패 후보 수정이나 다섯 번째 후보는 허용하지 않았다. B+A+C는 요청된 기존 조합의 재현이며 임의의 두 변경 혼합이 아니다.

| 새 ID | 조건 | 명시적 부모 | 전략 | 종류·선택 이유 |
| --- | --- | --- | --- | --- |
| a001 | B | reference | remove-unused | 과거 a001 재현. 네 조건의 공통 비교 기반 확보 |
| a002 | B+A | a001(B) | restructure-algebra | 과거 a002 재현. A만의 효과를 현재 환경에서 확인 |
| a003 | B+C | a001(B) | restructure-algebra | 사전 지정 확인 실험. A 없는 C가 주 질문이며 마지막 계수 계산은 B 그대로 |
| a004 | B+A+C | a001(B) | restructure-algebra | 과거 a003 재현. A가 있을 때 C의 추가 효과와 비교 |

**새 a003은 B+C이고, 이전 a003은 B+A+C다.** 번호가 아니라 조건과 세션 이름으로 구분해야 한다. B+A와 B+A+C의 코드/수치 재현을 새 전략 성공으로 세지 않는다.

## 3. 환경과 검증 방법

- 문제: `Binius.BinaryBasefold.fold_advances_evaluation_poly`.
- 저장소: [Verified-zkEVM/ArkLib](https://github.com/Verified-zkEVM/ArkLib), 기존 준비된 checkout.
- 커밋: `c1712f6c496d0aef04f09bae42aec13811b3273f`, Lean **v4.31.0**.
- 소스: `ArkLib/ProofSystem/Binius/BinaryBasefold/Prelude.lean`.
- 정책: [v1 snapshot](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/policy-snapshot.json), 유효성 → 최소 heartbeat → 동률이면 최소 tokens.
- 예산: 후보 4개, 원본 별도 1회, subprocess당 timeout 180초, patience 4. best 갱신 여부 때문에 지정 조건을 생략하지 않도록 시작할 때 고정했다.
- 현재 helper/검증기/benchmark/skill/protocol 및 checkout fingerprint를 새로 고정했다. 이전 세션과 skill/protocol 해시가 달라 새 세션을 사용했으며 이전 세션을 복구·수정하지 않았다.
- 임시 전체 소스에서 대상 선언만 교체해 `lake env lean`으로 컴파일하고 `#print axioms`를 검사했다. 이후 별도 임시 소스에서 대상 선언만 `#count_heartbeats`로 측정했다. 기존 대상 정리 `.olean` import로 검증을 대신하지 않았다.
- 원본 및 네 조건 모두 공리는 `Classical.choice`, `Quot.sound`, `propext`로 동일하다. 대상 정리에 **sorryAx나 새 공리 추가 없음**.
- 전체 소스의 다른 기존 선언에는 `declaration uses sorry`, deprecated/linter 경고가 남아 있다. 원본에도 있는 경고이며 대상 정리의 공리 검사와 구분한다. 전체 ArkLib가 sorry-free라는 주장은 하지 않는다.
- proof tokens는 공유 proof tokenizer의 수치로, LLM 토큰/API 비용이 아니다. 시간은 원시 JSON에 있지만 heartbeat 감소를 wall-clock 속도 향상으로 해석하지 않는다.

사용자가 허용한 기존 환경에서만 실행했다. 다운로드·tracked checkout 소스 변경·유료 API 호출·skill/도구/정책 수정은 하지 않았다.

## 4. 이번 세션 실측값

모두 이번 세션에서 새로 측정한 값이다. 기존 세션의 수치를 재사용하지 않았다. 감소율은 양수가 비용 감소이며 비교 분모는 해당 원본/부모다.

| 실행 | 조건 | 상태 | Heartbeat | 원본 대비 감소 | 부모 대비 감소 | Proof tokens | 원본 대비 감소 | 부모 대비 감소 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reference | 새 원본 기준선 | passed | 45,537 | — | — | 1,906 | — | — |
| a001 | B | passed / reviewed | 41,636 | 8.5667% | 8.5667% | 1,656 | 13.1165% | 13.1165% |
| a002 | B+A | passed / reviewed | 39,123 | 14.0852% | 6.0356% | 1,441 | 24.3966% | 12.9831% |
| a003 | B+C | passed / reviewed | 40,850 | 10.2927% | 1.8878% | 1,594 | 16.3694% | 3.7440% |
| **a004** | **B+A+C** | **passed / reviewed** | **38,337** | **15.8113%** | **7.9234%** | **1,379** | **27.6495%** | **16.7271%** |

a003의 원장 `improved=false`는 **그때의 best인 B+A를 갱신하지 못했다**는 뜻이다. 부모 B보다 비용이 감소했다는 사실과 모순되지 않으며, 검증 실패 또는 C 효과 없음으로 해석하면 안 된다.

## 5. 요청한 효과의 분리

[세 비교의 계산 기록](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/contrasts.json)은 저장된 유효한 result JSON에서 계산했다. Lean을 추가 실행하지 않았고 helper의 부모 관계를 바꾸지 않았다.

| 질문 | 비교 | Heartbeat 감소 | Heartbeat 감소율 | Tokens 감소 | Tokens 감소율 |
| --- | --- | ---: | ---: | ---: | ---: |
| B 대비 A의 효과 | B → B+A | 2,513 | 6.0356% | 215 | 12.9831% |
| **B 대비 C의 효과(A 없음)** | **B → B+C** | **786** | **1.8878%** | **62** | **3.7440%** |
| B+A 대비 C의 추가 효과 | B+A → B+A+C | 786 | 2.0090% | 62 | 4.3026% |

### 측정 사실

- A 없는 C도 786 heartbeat를 줄였으므로 주 질문의 답은 이 환경에서 **예**다.
- A가 있을 때도 C의 절대 감소량은 786으로 같았다.
- heartbeat 상호작용 대비는 `(38,337−39,123)−(40,850−41,636)=0`이다. tokens 대비도 `(1,379−1,441)−(1,594−1,656)=0`이다.
- B 대비 결합 감소량 3,299 heartbeat는 이번 측정에서 `2,513+786`과 같았다.
- 원본/B/B+A/B+A+C의 수치는 과거 관측과 일치했다. B+C는 과거 세션에 없던 확인 조건이다.

### 원인 추정 — 실측과 구분

- C가 중간 등식 elaboration과 반복 ring 정규화 한 단계를 줄여 비용이 감소했다는 설명과 일치한다.
- A는 `Polynomial.C`의 환 준동형 법칙으로 마지막 계수 등식을 재구성해 수동 conv와 인덱스 증명 재기술을 피한다는 설명과 일치한다.
- **세부 tactic profiling은 하지 않았다.** 따라서 786 heartbeat 전체를 특정 tactic 한 번의 내부 비용이라고 단정하지 않는다.
- 상호작용 대비 0은 이 네 측정에서 가산적으로 보인다는 뜻일 뿐, A와 C의 보편적 독립성이나 다른 정리에서도 동일한 효과를 증명하지 않는다.

## 6. 허용 변경 범위 검증

각 후보를 seal/evaluate하기 전에 부모 diff를 읽었으며 다음 파일에 보존했다.

| 조건 | 가설 | 부모 대비 diff | 최종 코드와 확인 |
| --- | --- | --- | --- |
| B | [a001 가설](attempts/a001/hypothesis.json) | [두 미사용 정의 삭제](attempts/a001/parent.diff) | [a001](attempts/a001/candidate.lean): 이전 a001과 byte-identical |
| B+A | [a002 가설](attempts/a002/hypothesis.json) | [마지막 블록만 교체](attempts/a002/parent.diff) | [a002](attempts/a002/candidate.lean): 이전 a002와 byte-identical |
| B+C | [a003 가설](attempts/a003/hypothesis.json) | [중간 calc 3행만 삭제](attempts/a003/parent.diff) | [a003](attempts/a003/candidate.lean): 삭제 내용이 이전 C와 동일, 마지막 계수 계산 B와 동일 |
| B+A+C | [a004 가설](attempts/a004/hypothesis.json) | [A/C 두 블록만 변경](attempts/a004/parent.diff) | [a004](attempts/a004/candidate.lean): 이전 a003과 byte-identical |

추가 대조: [A 유무에 따른 C diff](C-after-A.diff) 및 [C 유무에 따른 A diff](A-after-C.diff). A/C 각각의 추가·삭제 내용이 다른 조건에서도 동일함을 확인했다. Python은 이 diff/해시와 수치를 검사했을 뿐 후보를 생성하지 않았다. 재현 후보는 사전 등록 후 기존 코드 복사, B+C는 B 복사 후 에이전트의 정확한 3행 삭제로 작성했다.

## 7. 종료 상태·실패·한계

- 원본 1개 + 후보 4개 평가 완료. 후보 실패 **0**, timeout **0**, 권한 차단 **0**, 무결성/검증기 오류 **0**, 추가 수정 시도 **0**.
- 모든 후보 review 및 [helper 회고](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/reflection.json) 저장 완료. 남은 예산 **0**. 새 후보를 만들지 않는다.
- 회고의 정책 변경 제안은 **없음**. 활성 정책/skill/검증기 변경 없음.
- [보존 대상 실행 전 해시](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/protected-before.json)에 등록한 이전 세션·skill·P11 원본/selected·기존 지표·발표 HTML 등 **48개 파일 모두 불변**이다.
- [검증 기록](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/verification.json)의 부모·예산·동일성·차이 범위·원시 결과/원장 일치·저장 해시·공리 검사 **36개 모두 통과**했다. 이는 전체 dependency binary에 대한 완전한 attestation은 아니다.
- 기존 세션 a003의 미완료 review는 그대로 보존했다. 이번 a004의 완료와 혼동하지 않는다.
- 이번 작업은 도구 구현을 바꾸지 않았으므로 Python 회귀 테스트를 새로 실행하지 않았다. 실제 후보는 기존 검증기로 모두 컴파일/공리/heartbeat 검사했다.
- 조건당 1회, 단일 정리/고정 커밋/v4.31.0에 한정된다. 다른 Lean 버전·정리·공식 서버 점수·반복 실행 분포는 확인하지 않았다.
- 다음 실험은 이번 요청 범위에 없으므로 실행하지 않는다. 다른 문맥의 가산성이나 세부 원인 확인이 필요하다면 별도 요청과 새 실험 설계가 필요하다.

## 8. 원시 결과와 기록

- [세션 원장: best·명시적 부모·비교율·review](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/session.json)
- [동결 정책](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/policy-snapshot.json) · [회고](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/reflection.json) · [파생 비교](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/contrasts.json)

| 실행 | 원시 결과 | 전체 문맥 검증 로그 | 별도 heartbeat 로그 |
| --- | --- | --- | --- |
| reference | [JSON](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/baseline/result.json) | [check](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/baseline/check.log) | [heartbeat](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/baseline/heartbeat.log) |
| a001 / B | [JSON](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a001/result.json) | [check](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a001/check.log) | [heartbeat](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a001/heartbeat.log) |
| a002 / B+A | [JSON](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a002/result.json) | [check](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a002/check.log) | [heartbeat](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a002/heartbeat.log) |
| a003 / B+C | [JSON](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a003/result.json) | [check](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a003/check.log) | [heartbeat](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a003/heartbeat.log) |
| a004 / B+A+C | [JSON](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a004/result.json) | [check](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a004/check.log) | [heartbeat](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a004/heartbeat.log) |

원시 측정/상태는 루트 metrics에만 두며 evidence에 복제하지 않았다. 이 보고서는 저장된 결과를 해석한 문서이고 최종 채택 선언이 아니다.
