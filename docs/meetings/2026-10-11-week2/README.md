# LeanAgent Week 2

2026년 10월 11일 일요일 20:00–22:00.

Lean Refactor Arena의 Warm-up 15문제를 나누어 분석하고, 분야별 논문에서 증명 리팩터링에 활용할 방법을 조사.

## 공유 주제

- **Warm-up 문제 연구**: 담당 문제의 명제와 기존 증명 구조를 해석하고, 개선 접근법·시도 과정·검증 결과 또는 실험 계획을 공유합니다.
- **논문·학습 조사**: Lean&Mathlib, Autoformalization, Automated Theorem Proving(ATP), Verifier-guided Agent 분야의 개념과 연구 방법을 정리하고 담당 문제에 적용할 가능성을 살펴봅니다.

## 발표자료

HTML 발표자료를 기본으로 연결하며, 별도 HTML이 없는 경우 대표 공유 문서에 `(MD)`를 표시했습니다.

| 발표자 | 문제 | Warm-up 발표자료 | 논문·학습 발표자료 |
| --- | --- | --- | --- |
| 박채원 | 14·15 | [Putnam 문제 풀이와 Lean 증명 비교(MD)](../../research/refactoring/warmup/박채원/report.md) | Lean&Mathlib: [MIL 2장 정리(MD)](../../research/lean-mathlib/박채원/report.md) · [LeanDojo 분석(MD)](../../research/lean-mathlib/박채원/leandojo.md) |
| 남성우 | 1·2 | [Strata 치환·변수 추출 정리의 리팩터링](../../research/refactoring/warmup/남성우/presentation.html) | Autoformalization: [연구 방법과 Arena 적용 제안](../../research/autoformalization/남성우/presentation.html) |
| 박선영 | 8·11 | [증명 구조·개선 가설·실험 계획](../../research/refactoring/warmup/박선영/presentation.html) | Autoformalization: [연구 흐름과 논문 조사](../../research/autoformalization/박선영/presentation.html) |
| 권주원 | 3·6·13 | [상태 갱신·시간 정렬·정수 점화수열](../../research/refactoring/warmup/권주원/presentation.html) | ATP: [검색·생성·탐색·검증과 리팩터링 적용](../../research/automated-theorem-proving/권주원/presentation.html) |
| 손지연 | 7·12 | [명제 해석·증명 수정·실패와 해결 과정](../../research/refactoring/warmup/손지연/presentation.html) | ATP: [논문 28편의 검색·행동·탐색·검증 관점 정리](../../research/automated-theorem-proving/손지연/presentation.html) |
| 정소미 | 4·9 | [PhysLib·CSLib 증명 리팩터링과 검증](../../research/refactoring/warmup/정소미/presentation.html) | Verifier-guided Agent: Lean Refactor의 수정·검증·교정 반복 ([같은 발표자료](../../research/refactoring/warmup/정소미/presentation.html)) |
| 박성호 | 5·10 | [자동 리팩터링·검증 비용·버전별 결과(MD)](../../research/refactoring/warmup/박성호/report.md) | - |

## 주요 논의 사항

문제별 리팩터링 경험을 바탕으로, 에이전트에 어떤 정보를 주고 어디까지 수정을 맡길지 논의했습니다. 아래는 논의된 선택지와 열린 질문이며, 구체적인 적용 방식은 후속 실험으로 확인할 필요가 있습니다.

### 1. 범용 프롬프트와 문제별 특화

- 여러 문제에 공통으로 적용할 범용 프롬프트를 만들지, 문제의 도메인·출처·사용 라이브러리에 맞춰 프롬프트를 특화할지 검토했습니다.
- 공통 지침에 문제별 정보를 덧붙이는 방식도 비교할 수 있습니다. 이때 문제의 명제, 기존 증명, 사용 가능한 lemma, Lean·Mathlib 버전 중 어떤 정보를 제공할지 정해야 합니다.
- **열린 질문**: 동일한 프롬프트만으로 충분한가? 문제별 정보나 전략을 추가했을 때 개선 효과가 있는가?

### 2. Tactic 수정과 증명 구조 재설계

- 수정 후보가 중간에 실패했을 때 해당 지점만 고칠지, 앞선 단계와 중간 목표까지 포함해 증명 흐름을 다시 구성할지 논의했습니다.
- `simp` 같은 범용 자동화 tactic을 다른 tactic이나 명시적인 lemma 적용으로 치환하거나, 비용이 큰 부분만 리팩터링하는 접근을 검토했습니다.
- **열린 질문**: 개별 tactic의 치환으로 충분한가? 중간 단계를 나누거나 보조정리를 도입하는 구조적 변경이 필요한가?

### 3. Lemma 선택과 자동화 비용

- 기존 lemma를 재사용하거나 보조정리를 구성하는 방법, lemma 검색과 hammer 계열 도구 등 외부 자원을 활용하는 방법을 논의했습니다.
- `simp`가 사용하는 lemma 집합을 제한하는 방식과 `simp`를 사용하지 않는 방식을 실험 후보로 검토했습니다. `simp`의 일괄 제거 여부를 정하기보다, 원본·제한적 사용·대체 증명의 검증 비용을 비교할 필요가 있습니다.
- **열린 질문**: 어떤 lemma 집합과 tactic 조합이 필요한가? 후보를 찾는 탐색 비용과 최종 증명을 검증하는 비용을 어떻게 나누어 측정할 것인가?

### 4. AI Agent의 버전 호환성

- Claude·GPT 기반 에이전트가 대상 Lean·Mathlib 버전과 맞지 않는 lemma 이름이나 tactic 사용법을 제안하는지 확인할 필요가 있다는 질문이 나왔습니다.
- 실패 사례를 기록할 때 증명 전략의 문제와 버전·의존성 차이로 인한 문제를 구분하고, 실행 환경과 오류 메시지를 함께 남기는 방안을 검토할 수 있습니다.
- **열린 질문**: 버전 정보를 프롬프트에 명시하면 오류가 줄어드는가? 대상 환경의 검색·실행 결과를 피드백으로 주면 수정에 도움이 되는가?

### 후속 실험 정리 제안

위 논의를 비교 가능한 실험으로 이어가기 위해 다음 항목을 함께 기록하는 방안을 제안합니다.

- **환경과 기준**: Lean·Mathlib 버전, 사용 모델, 원본 증명, 변경 가능한 범위와 평가 지표.
- **비교 조건**: 범용/특화 프롬프트, tactic 치환/구조 변경, `simp` 사용 범위, lemma 검색·hammer 활용 여부를 한 번에 하나씩 바꾸어 비교.
- **결과와 비용**: 최종 증명의 검증 성공 여부, 검증 시간·연산량, 증명 길이와 함께 후보 생성·검색·재시도에 든 비용을 구분해 기록.
- **실패 원인**: 버전·의존성 문제, lemma 선택 문제, tactic 실패, 시간·자원 제한 등을 구분해 다음 시도의 근거로 활용.
