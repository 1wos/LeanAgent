# 남성우 Verifier-guided Agent

2026-10-18 주간 공유. 2026-10-12–17에 작업한 Lean Refactor Arena 검증·수리·선택 파이프라인의 설계, 구현 범위, Warm-up 15문제 모의 실행 결과를 다룹니다. 문제 풀이 자체보다 검증·수리 harness를 설명하는 분야별 발표자료입니다.

- 발표자료: [presentation.html](presentation.html) — 전체 읽기 / 발표 모드, 키보드 탐색, 인쇄 지원. 파일을 내려받아 브라우저에서 열 수 있습니다.
- 상세 보고서: [report.md](report.md)
- 측정 기록: [metrics.json](metrics.json) — 공식 점수가 아닌 로컬 모의 점수
- 검증 근거: [실험 안내와 재현 절차](evidence/warmup-2026-10-15/README.md) · [문제별 결과](evidence/warmup-2026-10-15/REPORT.md) · [선택 proof](evidence/warmup-2026-10-15/selected.json) · [감사 결과](evidence/warmup-2026-10-15/audit.json)
- 관련 자료: [기존 Warm-up 1·2번 발표](../../refactoring/warmup/남성우/README.md) · [이번 주 공유 목차](../../../meetings/2026-10-18-week3/README.md)

15문제의 36개 지정 버전 조합에서 원본과 선택 증명을 확인했습니다. 최종 선택은 14문제 개선, 8번 원본 보존입니다. Escalation은 프롬프트 12개 출력에서 끝났으며 실제 모델 호출은 하지 않았습니다. AST 기반 보호, 신뢰 가능한 tactic-state 인증, 실제 모델 반복 수리 루프는 후속 과제입니다.
