# P11 A/C 분리 확인 실험 분석

2026-10-17 · `p11-20261017-ac-check4` · 실행 전 고정 설계

## 질문과 범위

중간 calc의 연속 두 ring 단계 통합(C)이 마지막 계수 계산 재구성(A) 없이도 heartbeat를 줄이는가? 자유 최적화 탐색은 하지 않는다. 기존 `p11-20261017-adaptive3`의 분석·보고서·가설·후보·원시 결과·원장 review를 읽고 A/C의 실제 diff를 확인했다. 이전 기록은 수정하지 않는다.

기존 관측(이번 측정 아님): 원본 45,537/1,906, B 41,636/1,656, B+A 39,123/1,441, B+A+C 38,337/1,379 (heartbeat/tokens). 기존에는 C를 B+A 위에서만 평가했고 B+C가 없어 C의 A 없는 효과를 알 수 없었다. 과거 a003은 평가 통과 후 skill drift로 review 미완료였으며 이 상태를 보존한다.

## 고정 환경과 예산

- 기존 승인된 ArkLib checkout, Lean v4.31.0, commit `c1712f6c496d0aef04f09bae42aec13811b3273f`.
- init이 origin/commit/toolchain/clean tracked source를 확인하고 현재 코드·환경 fingerprint를 저장했다. 이전 세션과 skill/protocol 해시는 다르므로 새 기준선을 측정한다. 기존 수치를 재사용하지 않는다.
- 후보 4개 고정, 별도 원본 baseline 1회. timeout은 subprocess당 180초, patience 4로 고정 네 조건을 best 갱신 여부와 무관하게 비교한다.
- policy snapshot v1: 유효성 → 최소 heartbeat → 동률일 때 최소 tokens.
- 다운로드·tracked checkout 변경·skill/도구/정책 수정·외부 유료 API 호출 없음.
- 실패 후보는 수정/재시도하지 않는다. 환경·검증기·무결성 오류나 권한 거절이면 즉시 중단하고 관측된 상태까지 보고한다. B가 실패하면 나머지 조건의 유효 부모가 없으므로 중단한다.

## 명제와 proof map

`fold_advances_evaluation_poly`는 한 단계 fold한 평가값이 갱신 계수 `(1-r)*even + r*odd`의 다음 단계 다항식 평가와 같음을 보인다. 원본 statement 전체를 보존한다.

원본 단계: (1) y와 fiberMap/x₀/x₁, 현재/다음 계수 정의 (2) qMap(x₀)=qMap(x₁)=y (3) basis 합과 cast/bit 계산으로 x₁-x₀=1 (4) evenRefinement/oddRefinement 및 evaluation_poly_split_identity로 두 평가식 도출 (5) fold 정의를 가중합으로 전개하여 ring 계산 (6) 다항식 합을 sum_congr로 분해해 계수별 등식 증명.

지역 사용: `h_eval_qMap_x₀/x₁`는 `h_equation_39_x₀/x₁`에, `hx₀/hx₁`와 cast/bit 사실은 `h_fiber_diff`에, `h_fiber_diff`는 main calc에, `new_coeffs/P₀/P₁`는 마지막 계수 계산에 쓰인다. `P₀_coeffs/P₁_coeffs`만 후속 계산에서 쓰이지 않으며 B에서 제거한다. `h_j_lt`는 A의 기존 마지막 블록에 포함되어 함께 제거된다. 이번 실험에서 이를 별도 최적화하지 않는다.

주변 정의: 원본 소스 623–633행의 `fold`는 두 fiber 평가의 가중합이다. `evaluation_poly_split_identity`는 P(X)=P₀(qMap X)+X*P₁(qMap X)를 주며, `Polynomial.C_add/C_mul`은 마지막 계수 합/곱을 다항식 상수로 보내는 환 준동형 법칙이다. 기존 proof에 쓰인 경계 정리와 qMap/fiber 계산은 모두 유지한다. 줄 수를 성능 증거로 보지 않는다.

## 고정 네 조건과 허용 변경

| 새 ID | 조건 | 명시적 부모 | 종류 | 허용 변경 / 동일성 검사 |
| --- | --- | --- | --- | --- |
| a001 | B | reference | reproduction | 두 미사용 계수 정의와 소개 주석만 제거; 과거 a001과 byte-identical |
| a002 | B+A | a001 | reproduction | 마지막 `intro j hj` 다음 계산 블록만 `simp only [Polynomial.C_add, Polynomial.C_mul]; ring`으로 교체; 과거 a002와 byte-identical |
| a003 | B+C | a001 | experiment (확인용 ablation) | main calc의 전개형 중간 등식 3행만 삭제; 마지막 계수 계산은 B와 byte-identical |
| a004 | B+A+C | a001 | reproduction | 위 A/C 두 블록만 변경; 과거 a003과 byte-identical. 두 변경의 조합 재현이지 새 혼합 탐색 아님 |

각 후보 작성/복사 전에 helper plan으로 가설·허용 범위를 등록한다. best는 선택 지표일 뿐 부모 결정에 사용하지 않는다. B+A+C의 결합 변경은 사용자가 지정한 과거 후보 재현이며, 독립 조건 두 개의 결과 이후에 실행한다.

## 사전 가설과 비교

- A의 효과: HB(B) − HB(B+A).
- A 없는 C의 효과(주 질문): HB(B) − HB(B+C).
- A가 있을 때 C의 추가 효과: HB(B+A) − HB(B+A+C).
- 각 감소율의 분모는 해당 비교의 출발 조건. tokens도 같은 방법으로 비교한다.
- 상호작용 진단: `[HB(B+A+C) − HB(B+A)] − [HB(B+C) − HB(B)]`. 0이면 이번 측정값에서 가산적이며 보편적 독립성을 뜻하지 않는다.
- 가설: C가 A 없이도 중복 ring 정규화/중간 등식 elaboration을 줄일 수 있다. 반례 가능성: 지역 문맥·정규화 목표 변화로 감소량이 다르거나 증가할 수 있다.
- 과거 수치의 재현을 새 최적화 발견으로 세지 않는다. 조건당 1회, 한 정리·한 버전의 결과로 통계적 유의성/다른 정리 일반화/공식 서버 점수를 주장하지 않는다.

## 기록

새 metrics 세션에 원시 JSON/로그, 보존 대상 해시 manifest와 검증 결과를 저장한다. 각 attempt의 evidence에 부모 대비 diff를 저장한다. 실행 종료 후 이 폴더의 README.md/report.md에서 실제 존재하는 근거에만 상대 링크를 연결한다. selected·발표 HTML·기존 대표 보고서는 변경하지 않는다.
