# 박선영 Warm-up P11 A/C 분리 확인 실험

2026-10-17 · 세션 `p11-20261017-ac-check4`.

## 범위와 현재 상태

미사용 계수 정의만 제거한 B를 공통 부모로, 마지막 계수 계산 재구성(A)과 중간 calc의 두 ring 단계 통합(C)의 효과를 분리했다. 자유 최적화 탐색이 아니라 사전 지정 네 조건의 확인 실험이다.

- **완료:** 새 원본 baseline 및 후보 4/4개 모두 검증·측정 통과. 모든 review·회고 저장 완료, 잔여 예산 0.
- **질문의 답:** 이 P11/v4.31.0 환경에서는 C가 A 없이도 heartbeat를 줄였다. 수치·원인 추정·한계는 보고서에서 구분한다.
- **세션 best:** a004(B+A+C). 기존 selected 및 발표자료의 채택 상태는 변경하지 않았다.
- 마지막 반영 시도: **a004**, 문서 작성일 2026-10-17.

## 대표 자료

- [상세 보고서: 세 조건 대비·결과·해석·한계](report.md)
- [사전 분석: 질문·고정 네 조건·허용 변경 범위](analysis.md)

## 증명과 변경 근거

| ID | 조건 | 부모 | 후보 | 가설 | 부모 대비 diff |
| --- | --- | --- | --- | --- | --- |
| reference | 새 기준선 | — | [원본](reference.lean) | — | — |
| a001 | B | reference | [코드](attempts/a001/candidate.lean) | [가설](attempts/a001/hypothesis.json) | [diff](attempts/a001/parent.diff) |
| a002 | B+A | a001 | [코드](attempts/a002/candidate.lean) | [가설](attempts/a002/hypothesis.json) | [diff](attempts/a002/parent.diff) |
| a003 | B+C | a001 | [코드](attempts/a003/candidate.lean) | [가설](attempts/a003/hypothesis.json) | [diff](attempts/a003/parent.diff) |
| a004 | B+A+C | a001 | [코드](attempts/a004/candidate.lean) | [가설](attempts/a004/hypothesis.json) | [diff](attempts/a004/parent.diff) |

- 조건 간 추가 대조: [B+A→B+A+C](C-after-A.diff) · [B+C→B+A+C](A-after-C.diff).

## 루트 metrics 근거

- [세션 원장](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/session.json) · [동결 정책](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/policy-snapshot.json) · [회고](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/reflection.json)
- [원본 측정](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/baseline/result.json) · [B](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a001/result.json) · [B+A](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a002/result.json) · [B+C](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a003/result.json) · [B+A+C](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/attempts/a004/result.json)
- [세 대비의 계산 기록](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/contrasts.json) · [동일성·범위·해시 검증](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/verification.json) · [보존 대상 실행 전 해시](../../../../../../../../metrics/warmup/박선영/agent/p11-20261017-ac-check4/protected-before.json)
- 각 실행의 원시 `check.log`/`heartbeat.log`는 보고서의 원시 근거 표에서 연결한다. 측정 파일은 이 evidence 폴더에 복제하지 않는다.

## 관련 자료

- [이전 adaptive3 보고서](../p11-20261017-adaptive3/report.md): 수정하지 않고 보존했다. **이전 a003(B+A+C)은 이번 a004에 대응**하며 이번 a003은 B+C다.
- [작성자 자료 안내](../../../README.md).
