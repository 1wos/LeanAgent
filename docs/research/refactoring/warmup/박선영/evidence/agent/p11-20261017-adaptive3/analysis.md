# P11 순차 리팩터링 분석

- 세션: `p11-20261017-adaptive3`, 2026-10-17.
- 요청: 최대 3개 후보를 순차 평가하고 결과를 읽어 다음 전략을 결정한다. 수정 재시도도 예산에 포함한다.
- 환경: 기존 승인된 ArkLib checkout, Lean v4.31.0, `c1712f6c496d0aef04f09bae42aec13811b3273f`. 다운로드/checkout 변경 없음.
- 정책: 세션의 `policy-snapshot.json` v1. 유효성 → heartbeat 최소 → 동률이면 proof tokens 최소.
- 기준선: 새 실행에서 검증 통과, 45,537 heartbeat, 1,906 proof tokens, 공리 `Classical.choice`, `Quot.sound`, `propext`.

## 목표와 proof map

명제 `Binius.BinaryBasefold.fold_advances_evaluation_poly`는 평가 다항식의 값을 한 단계 fold하면 계수를 `(1-r)*even + r*odd`로 갱신한 다음 단계 평가 다항식의 값과 같다는 내용이다. benchmark statement 전체를 보존한다.

원본 `reference.lean`의 줄 번호 기준:

| 구간 | 역할 | 생성 사실과 사용처 |
| --- | --- | --- |
| 25–47 | y 도입, fiber 두 점, 현재 다항식과 새 계수 정의 | `fiberMap`→`x₀/x₁`, `P_i`→분해 평가식, `new_coeffs`→다음 다항식/마지막 합 |
| 48–62 | qMap이 두 fiber 점을 y로 보냄 | `h_eval_qMap_x₀/x₁`→129–134 분해 평가식 |
| 63–111 | basis 표현에서 `x₁-x₀=1` 증명 | `hx₀/hx₁`→fiber 차이; `h_index`, cast/bit 보조 사실은 해당 블록 내부 사용; `h_cast_1`은 명시적 후속 참조 없음 |
| 112–126 | 다음 다항식, 짝/홀 refinement 정의 | `P₀_coeffs/P₁_coeffs`는 이후 참조 없음; 실제 `P₀/P₁`는 별도 `evenRefinement/oddRefinement` 정의를 사용 |
| 127–140 | 다항식 분해를 x₀/x₁에서 평가, fold 정의 | `h_P_i_eval`→두 평가식; `h_fold_def`→calc 첫 단계 |
| 142–155 | fold 값을 두 refinement의 가중합으로 정리 | 두 평가식과 `h_fiber_diff` 사용; `ring` 세 번의 중간 계산 |
| 156–184 | refinement 가중합과 새 계수 다항식의 평가 일치 | `eval_C_mul`, `eval_add`, `mul_sum`, `sum_add_distrib`, `sum_congr`; `h_j_lt`는 명시적 후속 참조 없음 |

줄 수는 병목의 증거가 아니다. 자동화나 중복 elaboration이 비용에 영향을 줄 수 있다는 가설이며 전체 선언 heartbeat로만 개선을 판정한다. `omega`는 지역 산술 사실을 암묵적으로 사용할 수 있어 명시적 이름 참조가 없다는 것만으로 임의 삭제하지 않는다.

## 주변 정의와 현재 확인 범위

- 대상 파일: `ArkLib/ProofSystem/Binius/BinaryBasefold/Prelude.lean`, 원본 선언 시작 815행.
- `fold`는 두 fiber 점에서의 함수값을 선형 가중합으로 결합한다. 원본 `h_fold_def := rfl`이 그 연결을 확인한다.
- `intermediateEvaluationPoly`는 계수와 basis 다항식의 합이며, 마지막 단계에서 펼쳐 `Finset.sum_congr`로 계수별 등식을 증명한다.
- `evaluation_poly_split_identity`는 현재 다항식을 `P₀(qMap X) + X*P₁(qMap X)`로 분해한다.
- `iteratedQuotientMap_k_eq_1_is_qMap`, `is_fiber_iff_generates_quotient_point`, `pointToIterateQuotientIndex_qMap_total_fiber_eq_self`를 조합하여 qMap의 fiber 평가를 얻는다.
- `qMap_total_fiber_basis_sum_repr`와 `normalizedWᵢ_eval_βᵢ_eq_1`로 fiber 차이 1을 얻는다.
- 추가 경계 정리 탐색은 API 도구 호출 오류로 완료되지 않았다. 이 탐색 실패는 Lean 후보 실패가 아니다. 주석 속 `qMap_eval_fiber_eq_self`를 실제 사용 가능한 정리라고 가정하지 않았고, 이번 후보에서는 qMap/fiber 블록을 바꾸지 않았다. 직접 확인한 `fold` 정의는 대상 파일 623–633행이다.

## 이전 결과를 읽은 이유와 첫 가설

기존 `../../../../report.md`가 아닌 작성자 루트 `docs/research/refactoring/warmup/박선영/report.md`, `P11/reference.lean`, `P11/selected.lean`, 기존 result JSON을 읽었다. 기존 selected는 미사용 `P₀_coeffs/P₁_coeffs` 두 블록만 제거해 45,537→41,636 heartbeat, 1,906→1,656 tokens였다. 기존 기록은 현재 검증기의 fingerprint를 갖춘 새 세션 기준선이 아니므로 그대로 재사용하지 않는다.

첫 후보는 `remove-unused`, `kind=reproduction`으로 기존 selected를 그대로 재검증한다. 이를 새 발견으로 세지 않는다. 성공하면 검증된 부모를 확보한 뒤 별개 블록 하나만 개선한다. 실패하면 오류 종류를 분리하고 결과에 따라 다음 가설을 결정한다. 다음 두 후보를 미리 고정하지 않는다.

## 불확실성과 경계

- 직접 정리 적용은 coercion과 proof index 정합성 때문에 실패하거나 더 비쌀 수 있다.
- `ring` 호출 수를 줄여도 더 큰 정규화 목표로 인해 heartbeat가 증가할 수 있다.
- 성공 여부와 개선 여부를 분리한다. 공리 추가/명제 변경은 허용하지 않는다.
- 원본, selected, 기존 후보, 발표 HTML, legacy metrics를 수정하지 않는다.
- 실행은 최대 3개 후보, subprocess당 timeout 180초, patience 3. baseline은 후보 예산에 포함되지 않는다.
