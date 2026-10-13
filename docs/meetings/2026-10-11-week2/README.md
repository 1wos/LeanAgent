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

## 자료 참고사항

- 정소미님의 슬라이드는 Warm-up 4·9 실험과 논문 조사를 함께 담으므로 두 열에서 같은 파일을 연결합니다.
- 박선영님의 Warm-up 자료는 개선 가설과 실험 계획을 다룹니다. 최적화 후보의 개선 성능은 아직 측정하지 않았습니다.
- 남성우님의 논문 발표에 있는 Arena 적용 제안과 Warm-up 1·2의 실제 풀이·검증 결과는 구분해서 확인합니다.
- 박성호님의 공유 문서에는 방법과 관련 참고문헌이 포함되어 있습니다.

검증 결과를 비교할 때는 각 자료에 명시된 Lean 버전, 측정 환경과 검증 범위를 함께 확인합니다.
