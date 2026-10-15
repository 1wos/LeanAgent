# 담당 4·9번: 참조 증명 실행과 리팩터링 기록

작성: 정소미 · 초안 v0.1 · 검증일: 2026-10-11 (Asia/Seoul) · 공유: 2026-10-11(일)

웜업 4번과 9번의 참조 증명을 지정된 환경에서 실행하고, 명제를 유지한 채 증명을 줄이는 수정을 시도했다. 이 문서는 그 기록이다. 참조 증명 두 개는 모두 컴파일을 통과했다. 로컬에서 잰 증명 토큰은 두 문제 모두 공식 기준값과 같았고, heartbeat는 4번과 9번(`v4.33.0-rc2`)에서 공식 기준값과 같았다.

현재 후보의 증명 토큰은 4번이 **851 → 123**, 9번이 **251 → 79**이고, heartbeat는 4번이 **11,947 → 1,411**, 9번이 **3,858 → 510**이다. 9번 후보는 지정된 세 환경에서 모두 통과했다. 이 수치는 로컬 측정값이며 대회의 공식 점수가 아니다.

2주차 모임의 공유 자료이며, 후보와 측정 방법에 대한 검토를 기대한다. 발표 자료는 [presentation.html](presentation.html)에 있다.

## 1. 배경과 용어

- **대회**: [Lean Refactor Arena](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena). 이미 검증된 Lean 4 증명을 받아서, 명제는 그대로 두고 증명만 더 짧고 싸게 고치는 대회다.
- **웜업**: 본선 전에 공개된 연습 문제 15개다. 문제 데이터는 대회 사이트 저장소의 [`benchmark_data_warmup.jsonl`](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/blob/main/benchmark_data_warmup.jsonl)에 있다. 문제 번호는 이 파일의 줄 순서(첫 줄이 1번)이고, 스터디에서 4번과 9번을 배정받았다.
- **채점**: 문제 점수는 증명 토큰 감소율, heartbeat 감소율, 지정 환경 통과율 세 값의 평균이다. 컴파일에 실패하거나 명제를 바꾸면 그 문제는 0점이다.
- **공식 기준값**: 참조 증명의 토큰 수는 JSONL의 `proof_length`에, heartbeat는 같은 저장소의 [`benchmark_heartbeats.jsonl`](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/blob/main/benchmark_heartbeats.jsonl)에 있다.

| 용어 | 뜻 |
| --- | --- |
| 참조 증명 | 대회가 문제마다 제공하는 원래 증명. JSONL의 `src` 필드다. |
| 증명 토큰 | `:=` 뒤의 증명 본문을 대회 규칙으로 나눈 조각의 수. LLM의 토큰과 다르다. 주석과 빈 줄은 세지 않는다. |
| heartbeat | Lean이 선언 하나를 처리하면서 쓴 작업량의 계수. 실행 시간이 아니며 같은 환경에서는 같은 값이 나온다. |
| 지정 환경 | JSONL의 `version_info`에 나열된 Lean 버전과 저장소 커밋. 문제마다 다르다. |
| 공식 평가 워커 | 대회 사이트가 제출물을 컴파일하고 채점하는 프로그램. 코드는 공개되어 있지 않다. |
| 교정 | 컴파일에 실패한 수정을 Lean 오류 메시지를 보고 고치는 재시도. |
| 쌍모사 | 두 프로세스가 서로의 행동을 한 단계씩 따라 할 수 있고, 따라 한 뒤의 상태도 다시 같은 관계에 있다는 관계. CCS는 프로세스의 행동을 다루는 계산 체계이고, `lts`는 "상태, 행동, 다음 상태"로 이루어진 전이 시스템이다. |
| 증인 | 존재 명제를 증명할 때 제시하는 구체적인 대상. 9번에서는 관계 `ChoiceBisim`이다. |
| 잎 경우 | 경우 분석의 맨 끝에서 실제로 닫아야 하는 목표. |
| 혹 함수 | 한 점의 주변에서만 양수이고 그 밖에서는 0인 매끄러운 함수. |
| `WithLp 2 V`, `toL2` | `V`에 L² 노름을 붙인 공간과, `V`에서 그 공간으로 가는 사상. |
| `μ.trim` | 측도 `μ`를 더 작은 σ-대수로 제한한 측도. |

## 2. 두 문제의 개요

| 문제 | 정리 | 출처 · 위치 | 증명하려는 사실 | 핵심 수정 |
| --- | --- | --- | --- | --- |
| 4 | `fundamental_theorem_of_variational_calculus'` | [PhysLib](https://github.com/leanprover-community/physlib) · `Physlib/Mathematics/VariationalCalculus/Basic.lean` 99–224행 | 연속함수 `f`와 모든 시험함수의 내적을 적분한 값이 항상 0이면 `f`는 영함수다. | 증명 전체를 Mathlib에 있는 변분법 기본 보조정리의 적용으로 바꾼다. |
| 9 | `Cslib.CCS.bisimilarity_congr_choice` | [CSLib](https://github.com/leanprover/cslib) · `Cslib/Languages/CCS/BehaviouralTheory.lean` 311–372행 | `p`와 `q`가 쌍모사 동치이면, 같은 `r`과의 선택 `choice p r`과 `choice q r`도 쌍모사 동치다. | 두 방향에 대해 거울처럼 반복되는 블록을 항 하나로 합친다. |

이 문서에서 "원본 파일 N행"은 저장소 파일의 줄 번호이고, "선언의 N행째"는 정리 선언의 첫 줄을 1로 센 줄 번호다.

## 3. 검증 환경과 측정 방법

| 문제 | Lean | 저장소 커밋 | Mathlib 커밋 |
| --- | --- | --- | --- |
| 4 | `v4.32.0` | physlib `c48433678e8fb6306ebcd48453300c8e16058a62` | `81a5d257c8e410db227a6665ed08f64fea08e997` |
| 9 | `v4.33.0-rc2` | cslib `3aa9d4416c185e0b9faeb72bbd65abe85b95dbcc` | `51e6992efd06126df61a496bebf8f49482a4e129` |
| 9 | `v4.32.0` | cslib `197a7be621263b84c67ca4f803f69205b36d06df` | `81a5d257c8e410db227a6665ed08f64fea08e997` |
| 9 | `v4.31.0` | cslib `8ea71c8df91acd63285515a04da952b23b78d266` | `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` |

4번의 지정 환경은 하나이고, 9번의 지정 환경은 세 개다. Lean과 Mathlib의 버전은 각 저장소 커밋의 `lean-toolchain`과 `lake-manifest.json`이 정한다. 9번 정리의 위치(311–372행)와 내용은 세 커밋에서 같다.

측정은 [검증 스크립트](evidence/verify_candidate.py) 하나로 수행했다. 스크립트는 저장소 사본을 수정하지 않고, 원본 파일의 해당 줄을 후보 선언으로 교체한 사본을 만들어 `lake env lean`으로 컴파일한다. 뒤따르는 선언까지 함께 컴파일하므로, 후보가 같은 파일의 다른 정리를 깨뜨리면 실패로 판정한다.

| 항목 | 확인 방법 |
| --- | --- |
| 명제 보존 | 후보가 `statement.lean`의 내용으로 시작하고 바로 `:=`가 이어지는지 검사한다. `statement.lean`은 JSONL의 `statement` 필드를 그대로 저장한 파일이다. |
| 금지 패턴 | 대회 사이트 소스(`app.py`의 `_FORBIDDEN_PATTERNS`)에 있는 업로드 검사용 정규식 목록을 그대로 적용한다. `sorry`, `native_decide`, `#eval`, 최상위 보조 선언 등이 들어 있다. |
| 컴파일과 공리 | 종료 코드가 0이고 오류 메시지가 없어야 한다. 파일 끝에 붙인 `#print axioms`의 출력에 `sorryAx`가 없어야 한다. 스크립트는 공리 목록을 결과 파일에 기록하며, 참조 증명의 목록과 같은지는 결과 파일을 보고 확인했다. |
| 증명 토큰 | [토큰 계산기](evidence/proof_tokens.py)를 사용한다. 대회 주최 측의 논문인 Lean Refactor(arXiv:2605.20244v2) 부록 J의 `proof_length`를 다시 구현했고, 연산자 목록을 저자의 공개 저장소(`delta-lab-ai/lean-refactor`의 `lean_refactor/utils.py`)와 대조했다. 웜업 15문제의 공식 `proof_length`를 모두 재현한다. |
| heartbeat | 선언 앞에 `set_option Elab.async false in`과 `#count_heartbeats in`을 붙인 별도 사본을 컴파일한다. 종료 코드가 0일 때만 값을 기록한다. 제출용 후보에는 이 명령을 넣지 않는다. |

9번의 heartbeat는 지정 환경 중 최신인 `v4.33.0-rc2`의 값을 기준으로 삼았다. 공식 기준값 3,858이 이 환경의 측정값과 같기 때문이다. 공식 평가 워커가 이 환경에서 측정한다는 것은 확인된 사실이 아니라 추정이다.

## 4. 기준값: 참조 증명의 실행 결과

| 문제 | 환경 | 컴파일 | 증명 토큰: 로컬 / 공식 | heartbeat: 로컬 / 공식 | 공리 |
| --- | --- | --- | ---: | ---: | --- |
| 4 | `v4.32.0` | 통과 | 851 / 851 | 11,947 / 11,947 | `[propext, Classical.choice, Quot.sound]` |
| 9 | `v4.33.0-rc2` | 통과 | 251 / 251 | 3,858 / 3,858 | `[propext, Classical.choice, Quot.sound]` |
| 9 | `v4.32.0` | 통과 | 251 / 251 | 3,856 / 3,858 | `[propext, Classical.choice, Quot.sound]` |
| 9 | `v4.31.0` | 통과 | 251 / 251 | 3,859 / 3,858 | `[propext, Classical.choice, Quot.sound]` |

결과 파일은 [4번](evidence/P4/runs/reference.result.json)과 [9번의 환경별 폴더](evidence/P9/compat/)에 있다.

## 5. 참조 증명 대비 현재 후보

| 문제 | 기준 환경 | 증명 토큰: 참조 → 현재 | 감소율 | heartbeat: 참조 → 현재 | 감소율 | 지정 환경 통과 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 4 | `v4.32.0` | 851 → **123** | **85.55%** | 11,947 → **1,411** | **88.19%** | **1/1 · 100%** |
| 9 | `v4.33.0-rc2` | 251 → **79** | **68.53%** | 3,858 → **510** | **86.78%** | **3/3 · 100%** |

세 값(토큰 감소율, heartbeat 감소율, 지정 환경 통과율)의 평균인 문제 점수로 계산하면 4번은 91.25, 9번은 85.10이다. 로컬 측정값으로 계산한 값이다.

9번 후보의 환경별 결과는 다음과 같다.

| 환경 | 컴파일 | heartbeat: 참조 → 후보 | 결과 파일 |
| --- | --- | ---: | --- |
| `v4.33.0-rc2` | 통과 | 3,858 → 510 | [결과](evidence/P9/compat/v4.33.0-rc2/final.result.json) |
| `v4.32.0` | 통과 | 3,856 → 516 | [결과](evidence/P9/compat/v4.32.0/final.result.json) |
| `v4.31.0` | 통과 | 3,859 → 516 | [결과](evidence/P9/compat/v4.31.0/final.result.json) |

후보 파일은 [4번 `final.lean`](evidence/P4/final.lean)과 [9번 `final.lean`](evidence/P9/final.lean)이다. 두 후보의 공리 목록은 참조 증명과 같다.

## 6. 9번 `Cslib.CCS.bisimilarity_congr_choice`

### 9번: 참조 증명을 읽은 내용

명제는 합동성 정리다. CCS 프로세스 `p`와 `q`가 쌍모사 동치(`p ~[lts] q`)이면, 같은 프로세스 `r`과의 선택 `choice p r`과 `choice q r`도 쌍모사 동치다. 원본 파일의 문서 주석은 이 연산을 `P + R`로 적지만 수의 덧셈이 아니다. 첫 행동을 하는 순간 두 프로세스 중 한쪽으로 정해지는 연산이다.

증명은 쌍모사의 증인으로 관계 `ChoiceBisim`을 제시한다. 이 관계는 원본 파일 306–308행에 정의되어 있고, `(choice p r, choice q r)` 쌍을 담는 `choice` 생성자와 이미 쌍모사 동치인 쌍을 담는 `bisim` 생성자로 이루어진다. 관계가 쌍모사임을 보이려면 두 방향을 확인해야 한다. 한 방향(`left`)은 앞쪽 상태의 행동을 뒤쪽 상태가 따라 하는 것이고, 다른 방향(`right`)은 그 반대다. 방향마다 세 경우가 있다.

- 선택의 첫째 프로세스 `p`에서 온 행동(`choiceL`): 가정의 쌍모사에서 `q`의 대응 행동을 얻는다.
- 선택의 둘째 프로세스 `r`에서 온 행동(`choiceR`): 반대쪽도 같은 `r`의 행동을 하고, 도착 상태가 같으므로 반사성으로 닫는다.
- 이미 쌍모사 동치인 쌍(`bisim`): 첫 행동 이후의 상태 쌍이 모두 이 경우에 해당한다.

선언 62줄 가운데 54줄(선언의 9–62행째)이 두 방향의 블록이며, 두 블록은 `follow_fst`와 `follow_snd`만 다르다. `simp`나 `grind` 같은 자동화 전술은 쓰지 않는다.

### 9번: 수정 시도와 결과

시도마다 수정의 범위를 작게 잡고 매번 검증했다. 실패하면 Lean 오류 메시지를 보고 교정했다. 채택 기준은 컴파일 통과와, 토큰 감소율과 heartbeat 감소율의 평균이 직전에 채택한 후보보다 커지는 것이다.

시도는 먼저 준비한 `v4.32.0` 환경에서 반복했고, 최종 후보만 세 환경에서 다시 쟀다. 그래서 아래 표의 수치는 `v4.32.0`의 값이고, 감소율의 분모도 이 환경의 참조 값(251토큰, heartbeat 3,856)이다. 결과 파일은 [`P9/runs`](evidence/P9/runs/)에, 후보 파일은 [`P9/attempts`](evidence/P9/attempts/)에 있다.

| 시도 | 바꾼 내용 | Lean 결과 | 증명 토큰 | heartbeat | 채택 여부 |
| --- | --- | --- | ---: | ---: | --- |
| 1 | 잎 경우 여섯 개의 `exists`·`constructor`·`apply` 묶음을 익명 생성자 한 줄로 바꿨다. | 통과 | 262 | 497 | 채택. 토큰은 11개 늘었지만 heartbeat가 3,856에서 497로 줄었다. |
| 2 | `obtain`으로 관계를 꺼내지 않고 `Bisimilarity.follow_fst`와 `follow_snd`를 가정에 직접 적용했다. | 통과 | 198 | 441 | 채택 |
| 3 | 증인 제시를 `refine` 한 줄로 합치고, 경우 분석을 `rintro s (t \| t)` 패턴으로 썼다. | 실패. ``Unknown identifier `t` `` ([로그](evidence/P9/runs/attempt_03.check.log)) | - | - | 교정으로 넘김 |
| 4 | 시도 3의 교정. `Tr`의 생성자가 8개여서 패턴이 맞지 않았다. `intro s t; cases t`와 `next t =>`로 바꿨다. | 통과 | 169 | 380 | 채택 |
| 5 | 두 방향 블록의 `intro`와 `cases`를 `<;>`로 한 번만 쓰게 했다. | 통과 | 157 | 383 | 채택 |
| 6 | `obtain` 뒤 `exact` 두 줄을 `Exists.imp`와 `And.imp` 항 한 줄로 바꿨다. | 통과 | 124 | 353 | 채택 |
| 7 | 증인의 명시 인자 `@ChoiceBisim _ _ defs`를 `ChoiceBisim`으로 줄였다. | 통과 | 120 | 353 | 채택 |
| 8 | 두 방향에 똑같이 나오는 `choiceR` 잎을 `<;> try`로 합쳤다. | 통과 | 107 | 422 | 채택 |
| 9 | `Bisimilarity.isBisimulation`이 주는 논리곱에 `.imp`를 적용하여 두 방향을 항 하나로 합쳤다. | 통과 | 89 | 500 | 채택 |
| 10 | `refine (...).imp ?_ ?_`를 `apply (...).imp`로 바꿨다. | 통과 | 87 | 502 | 채택 |
| 11 | 증인 제시를 `exists`로 바꿨다. | 통과 | 83 | 524 | 채택 |
| 12 | 바깥의 경우 분석을 `repeat' first` 하나로 합치고, `bisim` 경우와 `choiceL` 경우의 항을 하나로 통일했다. `rename_i`를 지웠다. | 통과 | 79 | 516 | 채택. 현재 후보다. |
| 13 | 비교용. `bisim` 경우를 `grind [IsBisimulation, ChoiceBisim]`로 닫았다. 시도 7의 후보와는 두 군데가 더 다르다. 증인의 명시 인자 `@ChoiceBisim _ _ defs`가 남아 있고, `rename_i t` 대신 `‹_›`를 쓴다. | 통과 | 103 | 1,242 | 기각. 시도 7보다 토큰은 17개 적고 heartbeat는 889 많다. |

시도 1에서 heartbeat가 크게 줄어든 원인은 분석하지 않았다. 참조 증명의 `exists`·`constructor`·`apply` 묶음을 항으로 바꾼 것만으로 줄었다는 관찰이다.

현재 후보는 다음과 같다. heartbeat는 `v4.32.0`에서 516, 기준 환경인 `v4.33.0-rc2`에서 510이다.

```lean
theorem bisimilarity_congr_choice :
    (p ~[lts (defs := defs)] q) → (choice p r) ~[lts (defs := defs)] (choice q r) := by
  intro h
  exists ChoiceBisim, ChoiceBisim.choice h
  rintro _ _ (h | h) μ <;> apply (Bisimilarity.isBisimulation _ _ h μ).imp <;> intro f s t <;>
    repeat' first
    | exact (f _ ‹_›).imp fun _ => And.imp (by first | exact id | exact Tr.choiceL) ChoiceBisim.bisim
    | exact ⟨s, Tr.choiceR ‹_›, ChoiceBisim.bisim (HomBisimilarity.refl _)⟩
    | cases t
```

### 9번: 남겨 둔 부분과 막힌 점

- 증인 관계 `ChoiceBisim`과 증명의 수학적 내용은 참조 증명과 같다. 바뀐 것은 같은 논증을 적는 방식이다.
- 현재 후보는 `repeat' first`와 `‹_›`에 의존해서 읽기 어렵다. 읽기 쉬운 형태를 우선한다면 [시도 7의 후보](evidence/P9/attempts/attempt_07.lean)가 대안이다. 불릿으로 경우를 나누며 120토큰이다. heartbeat는 `v4.31.0`에서 353, `v4.32.0`에서 353, `v4.33.0-rc2`에서 352이고 세 환경에서 모두 통과했다([`v4.31.0`](evidence/P9/compat/v4.31.0/attempt_07.result.json), [`v4.32.0`](evidence/P9/runs/attempt_07.result.json), [`v4.33.0-rc2`](evidence/P9/compat/v4.33.0-rc2/attempt_07.result.json)).
- heartbeat가 가장 낮은 후보는 시도 6과 시도 7(353)이고, 토큰이 가장 적은 후보는 시도 12(79)다. 두 감소율의 평균으로는 시도 12가 가장 높다.
- 증명 전체를 `grind` 한 번으로 닫는 형태는 통과하는 것을 찾지 못했다. 검증 스크립트를 거치지 않은 임시 파일에서 `grind failed`로 끝났고, 그 기록은 이 폴더에 넣지 않았다.
- 증명 자리에 `sorry`만 넣은 선언의 heartbeat는 `v4.33.0-rc2`에서 39였다([결과](evidence/P9/compat/v4.33.0-rc2/floor.result.json)). 현재 후보의 510과의 차이인 471이 앞으로 줄일 수 있는 최대폭이고, 문제 점수로는 약 4.1점이다.

## 7. 4번 `fundamental_theorem_of_variational_calculus'`

### 4번: 참조 증명을 읽은 내용

명제는 변분법의 기본 보조정리다. `Y`는 유한 차원 실내적공간이고, `V`는 PhysLib의 `InnerProductSpace'` 구조를 가진 실노름공간이다. `μ`는 콤팩트 집합에서 유한하며 비어 있지 않은 열린집합에서 양수인 측도이고, `f : Y → V`는 연속함수다. 모든 시험함수 `g`(매끄럽고 콤팩트 지지를 갖는 함수)에 대해 `∫ x, ⟪f x, g x⟫_ℝ ∂μ = 0`이면 `f = 0`이다. `Y`와 `V`에 대한 가정은 명제 본문이 아니라 원본 파일 82–85행의 `variable` 선언에 있다.

증명은 귀류법이며 네 단계로 진행한다.

1. `f x₀ ≠ 0`인 점 `x₀`를 잡는다.
2. `f`를 `toL2`로 `WithLp 2 V`에 옮겨 코시–슈바르츠 부등식을 쓰고, 연속성으로부터 공 `B(x₀, δ₂)` 안에서 `⟪f x, f x₀⟫ > 0`임을 보인다.
3. 혹 함수 `φ`로 시험함수 `g x = φ x • f x₀`를 만든다.
4. 피적분함수 `φ x * ⟪f x, f x₀⟫`가 모든 점에서 0 이상이고, 측도가 양수인 닫힌 공 위에서 양수이므로 적분이 양수가 되어 가정과 모순이다.

토큰이 많이 드는 부분은 세 곳이다. 선언의 13–45행째는 `WithLp 2 V`로 우회한다. 49–64행째는 혹 함수의 존재 명제를 세웠다가 여섯 성분으로 다시 꺼낸다. 81–120행째는 포함 관계와 측도 양수성을 `have` 8개로 나누어 적는다.

### 4번: 수정 시도와 결과

두 갈래로 시도했다. 첫째 갈래는 참조 증명에서 출발하여 한 단계씩 고쳤다. 둘째 갈래는 첫째 갈래와 별도로, Mathlib에 있는 변분법 기본 보조정리로 증명 전체를 바꿨다. 채택 기준은 9번과 같고, 감소율의 분모는 참조 값(851토큰, heartbeat 11,947)이다. 수치는 `v4.32.0`의 값이다. 결과 파일은 [`P4/runs`](evidence/P4/runs/)에, 후보 파일은 [`P4/attempts`](evidence/P4/attempts/)에 있다.

#### 첫째 갈래: 참조 증명에서 출발한 단계별 수정

| 시도 | 바꾼 내용 | Lean 결과 | 증명 토큰 | heartbeat | 채택 여부 |
| --- | --- | --- | ---: | ---: | --- |
| 1 | 혹 함수의 성분 중 이후에 쓰이지 않는 `φ x₀ > 0`을 지웠다. | 통과 | 838 | 11,867 | 채택 |
| 2 | `closedBall_subset_support`의 전술 블록을 `mul_ne_zero` 항 하나로 바꿨다. | 통과 | 812 | 11,551 | 채택 |
| 3 | `nlinarith`를 `linarith`와 힌트 두 개로 바꿨다. | 통과 | 806 | 8,512 | 채택. 토큰 6개와 heartbeat 3,039가 줄었다. |
| 4 | `WithLp 2 V` 우회를 없앴다. `x ↦ ⟪f x, f x₀⟫`가 연속이므로 양수인 점들이 열린집합이라는 사실(`isOpen_lt`)로 공을 구했다. | 통과 | 543 | 5,306 | 채택 |
| 5 | 혹 함수의 존재 명제를 없애고 `ContDiffBump` 구조를 직접 썼다. | 실패. `Application type mismatch` ([로그](evidence/P4/runs/attempt_05.check.log)) | - | - | 교정으로 넘김 |
| 6 | 시도 5의 교정. 반지름 부등식 `δ₂ / 4 < δ₂ / 2`가 필요한 자리에 `δ₂ / 2 < δ₂`를 넣었던 것을 고쳤다. | 통과 | 427 | 4,746 | 채택 |
| 7 | 지지집합 포함, 적분 가능성, 닫힌 공의 측도 양수성 단계를 `Continuous.integral_pos_of_hasCompactSupport_nonneg_nonzero` 하나로 바꿨다. | 통과 | 185 | 1,765 | 채택 |
| 8 | 도입부를 `ext x₀`와 `by_contra`로 바꾸고, `x₀`에서의 양수성을 한 번만 증명했다. | 통과 | 165 | 1,686 | 채택 |
| 9 | 반지름과 `ContDiffBump`를 없애고 `exists_contDiff_tsupport_subset`으로 혹 함수를 얻었다. | 통과 | 161 | 1,488 | 채택 |
| 10 | 연속성 보조 사실의 형 표기를 지우고 `(𝕜 := ℝ)`만 명시했다. | 통과 | 144 | 1,463 | 채택 |
| 11 | 비음성 증명의 경우 나누기 기준을 `x ∈ tsupport φ`로 바꿨다. | 통과 | 141 | 1,483 | 채택. 토큰 3개가 줄고 heartbeat 20이 늘었다. |
| 12 | `ne_of_eq_of_ne`를 `▸`로 바꿨다. | 통과 | 141 | 1,485 | 기각. 토큰은 같고 heartbeat만 늘었다. |

#### 둘째 갈래: Mathlib의 변분법 기본 보조정리로 전체 교체

Mathlib의 `ae_eq_zero_of_integral_contDiff_smul_eq_zero`는 변분법 기본 보조정리의 Mathlib 판이다. 내용은 이렇다. 국소 적분 가능한 함수가 있고, 그 함수와 모든 매끄러운 콤팩트 지지 실수 함수의 곱의 적분이 0이면 그 함수는 거의 어디서나 0이다. 이 정리는 4번 파일의 import 범위 안에 있다. 4번의 명제와는 결론("거의 어디서나 0")과 가정(`BorelSpace`)이 달라서, 아래 설명처럼 두 차이를 메우는 단계가 필요하다.

| 시도 | 바꾼 내용 | Lean 결과 | 증명 토큰 | heartbeat | 채택 여부 |
| --- | --- | --- | ---: | ---: | --- |
| R1 | `x`를 고정하고 실수 함수 `y ↦ ⟪f y, f x⟫`에 위 정리를 적용했다. `BorelSpace Y` 가정은 `μ.trim`으로 메웠다. | 통과 | 176 | 2,004 | 둘째 갈래의 출발점 |
| R2 | 중간 보조 사실을 `refine` 한 줄에 넣고, 인스턴스 증명을 항으로 바꿨다. | 통과 | 139 | 1,959 | 채택 |
| R3 | `IsLocallyFiniteMeasure` 대신 `IsFiniteMeasureOnCompacts`를 증명하고, `simpa`를 `simpa only [inner_smul_right', Pi.mul_apply]`로 바꿨다. | 통과 | 123 | 1,411 | 채택. 현재 후보다. |

두 감소율의 평균은 첫째 갈래의 최선인 시도 11이 85.51%, 둘째 갈래의 R3이 86.87%다. 그래서 R3을 현재 후보로 정했다.

```lean
lemma fundamental_theorem_of_variational_calculus' {f : Y → V}
    (μ : Measure Y) [IsFiniteMeasureOnCompacts μ] [μ.IsOpenPosMeasure]
    [OpensMeasurableSpace Y]
    (hf : Continuous f) (hg : ∀ g, IsTestFunction g → ∫ x, ⟪f x, g x⟫_ℝ ∂μ = 0) :
    f = 0 := by
  funext x
  have hle := ‹OpensMeasurableSpace Y›.borel_le
  have hc : Continuous fun y => ⟪f y, f x⟫_ℝ := by fun_prop
  refine inner_self_eq_zero'.1 (congrFun ((hc.ae_eq_iff_eq μ continuous_zero).1
    (ae_eq_of_ae_eq_trim (hm := hle) ?_)) x)
  letI := borel Y
  haveI : BorelSpace Y := ⟨rfl⟩
  haveI : IsFiniteMeasureOnCompacts (μ.trim hle) := ⟨fun K hK =>
    trim_measurableSet_eq hle hK.measurableSet ▸ hK.measure_lt_top⟩
  exact ae_eq_zero_of_integral_contDiff_smul_eq_zero hc.locallyIntegrable fun g hgs hgc =>
    (integral_trim hle (hgs.continuous.mul hc).stronglyMeasurable).symm.trans
      (by simpa only [inner_smul_right', Pi.mul_apply] using
        hg _ (.smul_right ⟨hgs, hgc⟩ contDiff_const))
```

이 증명은 다음 순서로 진행한다.

1. 점 `x`를 고정하고 실수 함수 `y ↦ ⟪f y, f x⟫`를 본다.
2. 가정을 시험함수 `g y • f x`에 적용하면, 모든 매끄러운 콤팩트 지지 실수 함수 `g`에 대해 `∫ g y * ⟪f y, f x⟫ = 0`이다.
3. Mathlib의 정리가 이 실수 함수가 거의 어디서나 0임을 준다. 연속함수이므로 모든 점에서 0이다(`Continuous.ae_eq_iff_eq`).
4. `y = x`를 넣으면 `⟪f x, f x⟫ = 0`이고, 따라서 `f x = 0`이다.

Mathlib의 정리는 `BorelSpace Y`를 요구하는데 명제에는 `OpensMeasurableSpace Y`만 있다. 그래서 측도를 Borel σ-대수로 제한한 `μ.trim`에 정리를 적용하고, `integral_trim`과 `ae_eq_of_ae_eq_trim`으로 원래 측도 `μ`에 대한 결과로 되돌린다.

### 4번: 남겨 둔 부분과 막힌 점

- 증명 자리에 `sorry`만 넣은 선언의 heartbeat는 537이었다([결과](evidence/P4/runs/floor.result.json)). 현재 후보의 1,411과의 차이인 874가 앞으로 줄일 수 있는 최대폭이고, 문제 점수로는 약 2.4점이다.
- `letI := borel Y` 뒤에는 `MeasurableSpace Y` 인스턴스가 문맥에 두 개 있다. 이 블록에 줄을 더 넣으면 의도와 다른 인스턴스가 선택될 수 있다.
- 첫째 갈래의 최선 후보([시도 11](evidence/P4/attempts/attempt_11.lean), 141토큰, heartbeat 1,483)는 참조 증명의 귀류법 줄거리를 유지한다. 참조 증명과 같은 논증을 남기고 싶다면 이 후보가 대안이다.
- `fun_prop`을 항으로 바꾸는 시도와 `(hm := hle)`를 생략하는 시도는 검증 스크립트를 거치지 않은 임시 파일에서 이득이 없거나 실패했다. 후보로 만들지 않았고, 그 기록은 이 폴더에 넣지 않았다.

## 8. 두 문제에서 얻은 점

- **구조를 바꾸는 수정이 줄 단위 수정보다 컸다.** 4번에서 줄 단위 수정인 시도 1–3은 851 → 806토큰에 그쳤다. 라이브러리 정리로 단계를 통째로 바꾼 시도 4와 시도 7은 각각 806 → 543, 427 → 185였고, 증명 전체를 Mathlib 정리로 바꾼 R3이 123토큰이다. 9번에서 토큰을 가장 많이 줄인 것은 시도 2(262 → 198)와 시도 6(157 → 124)이다. 시도 2는 관계를 꺼냈다가 되돌리는 왕복을 없앴고, 시도 6은 두 줄짜리 전술을 항 하나로 바꿨다.
- **길이와 heartbeat는 따로 움직인다.** 9번의 시도 1은 토큰이 251 → 262로 늘었는데 heartbeat는 3,856 → 497로 줄었다. 반대로 `grind`를 넣은 시도 13은 시도 7보다 토큰이 17개 적고 heartbeat가 889 많다. 4번의 시도 3은 `nlinarith`를 `linarith`로 바꿔 토큰 6개와 heartbeat 3,039를 줄였다.
- **토큰 계산 규칙이 수정 방향을 정한다.** 점으로 이은 이름은 길이와 무관하게 1토큰이고, 괄호·쉼표·꺾쇠는 각각 1토큰이며, 줄바꿈은 0토큰이다. 다만 `:=` 바로 뒤에서 줄을 바꾸면 1토큰이 늘어난다. 이름을 줄이는 것은 효과가 없고, 구두점이 줄어드는 구조 변경이 효과가 있다. 전체 규칙은 [토큰 계산기](evidence/proof_tokens.py)의 코드에 있다.
- **두 축의 교환 비율을 알면 미세 조정을 판단할 수 있다.** 두 감소율을 같은 비중으로 볼 때 토큰 1개는 4번에서 heartbeat 약 14, 9번에서 약 15와 같다. 9번의 시도 5, 8, 9, 10, 11은 heartbeat가 늘었지만 이 비율로 보면 이득이어서 채택했다.
- **측정기를 먼저 맞춰야 한다.** 논문 HTML의 코드 목록은 연산자 `⁻¹`을 `-1`로 표시한다. 그대로 옮긴 토큰 계산기는 15문제 중 12문제만 공식 값과 맞았다.

## 9. 해석 범위와 한계

- 모든 수치는 로컬 측정값이다. 토큰 계산기는 공식 값 15개를 재현했다. heartbeat는 4번과 9번(`v4.33.0-rc2`)의 참조 증명에서 공식 기준값과 같았고, 9번의 다른 두 환경에서는 3,856과 3,859였다. 후보에 대한 공식 값은 대회 사이트에 제출해야 확인할 수 있다. 제출은 하지 않았다.
- 최종 후보 두 개는 시도와 별도로 한 번 더 실행했고 같은 값이 나왔다. 나머지 시도는 한 번씩 실행한 값이다.
- 9번의 heartbeat 기준 환경을 `v4.33.0-rc2`로 본 것은 추정이다. 기준 환경이 `v4.32.0`이나 `v4.31.0`이라면 9번의 문제 점수는 85.10이 아니라 85.05다.
- 수정 시도 과정에서 문제별 API 비용을 집계하지 않았다. 대회의 예산 규칙(문제당 US$3, 버린 시도를 포함한 모든 호출 집계)을 충족하는 실행이 아니다.
- 4번 후보는 참조 증명과 증명 방식이 다르다. 대회 안내에서 증명 방식의 변경을 제한하는 규칙은 찾지 못했다. 명제는 그대로이고 보조 선언은 추가하지 않았다.
- 논문에 나오는 PhysLean은 4번의 출처인 PhysLib과 같은 저장소다. GitHub가 `HEPLean/PhysLean`을 `leanprover-community/physlib`으로 연결한다.

## 10. 재현 방법

필요한 것은 Lean 버전 관리자 `elan`과 Python 3(표준 라이브러리만 사용)이다. 2026-10-11에는 Python 3.14.7로 실행했다.

1. 2절의 저장소를 3절의 커밋으로 받는다. Lean과 Mathlib의 버전은 저장소가 정하므로 따로 맞추지 않는다.
2. 저장소 폴더에서 `lake exe cache get`을 실행한 뒤 대상 모듈을 빌드한다. 4번은 `lake build Physlib.Mathematics.VariationalCalculus.Basic`, 9번은 `lake build Cslib.Languages.CCS.BehaviouralTheory`다.
3. 이 문서 옆의 [`evidence`](evidence/) 폴더에서 아래 명령을 실행한다.

```sh
# 4번
python3 verify_candidate.py --repo <physlib 경로> \
  --file Physlib/Mathematics/VariationalCalculus/Basic.lean --start 99 --end 224 --hb-line 87 \
  --name "fundamental_theorem_of_variational_calculus'" \
  --statement P4/statement.lean --candidate P4/final.lean --workdir out/P4 --tag final

# 9번 (환경마다 --repo만 바꾼다)
python3 verify_candidate.py --repo <cslib 경로> \
  --file Cslib/Languages/CCS/BehaviouralTheory.lean --start 311 --end 372 --hb-line 310 \
  --name "Cslib.CCS.bisimilarity_congr_choice" \
  --statement P9/statement.lean --candidate P9/final.lean --workdir out/P9 --tag final
```

| 옵션 | 뜻 |
| --- | --- |
| `--start`, `--end` | 원본 파일에서 후보로 교체할 줄 범위. JSONL의 `start_line`과 `end_line`이다. |
| `--hb-line` | heartbeat 측정 명령을 끼워 넣을 줄. 선언 바로 위의 주석이 시작하는 줄을 준다. 4번은 주석이 87–98행이어서 87이고, 9번은 310행의 한 줄 주석이어서 310이다. |
| `--name` | `#print axioms`에 넘길 정리의 전체 이름. |
| `--workdir`, `--tag` | 생성한 사본, 로그, 결과 파일을 둘 폴더와 파일 이름의 앞부분. |
| `--lean-arg` | Lean에 넘길 옵션. 생략할 수 있다. |
| `--extra-import` | heartbeat 측정 사본에만 추가할 import. 생략할 수 있다. |

실행이 끝나면 `out/P4/final.result.json`이 생긴다. `compiled`가 `true`이고, `proof_tokens`가 123, `heartbeat.heartbeats`가 1,411이면 이 문서의 4번 결과와 같다. 9번은 `v4.33.0-rc2`에서 79와 510이다.

이 폴더의 결과 파일은 위 명령에 옵션을 더해 실행한 기록이다. 4번은 PhysLib의 `lakefile.toml`에 있는 빌드 옵션을 `--lean-arg=-Dwarn.sorry=false --lean-arg=-Dweak.says.verify=true`로 함께 넘겼다. 9번의 환경별 결과(`P9/compat`)는 `--extra-import Mathlib.Util.CountHeartbeats`를 붙여 실행했다. 두 경우 모두 옵션 없이 실행해도 같은 값이 나온다. 4번은 2026-10-11에 참조 증명(851토큰, heartbeat 11,947)과 최종 후보(123토큰, heartbeat 1,411)로 확인했고, 9번은 세 환경의 참조 증명과 최종 후보로 확인했다.

토큰 계산기의 자체 점검은 `python3 proof_tokens.py --check benchmark_data_warmup.jsonl`이며 `15/15`가 나와야 한다. 시도 표의 수치는 `python3 attempt_table.py P9/runs 251 3856`처럼 결과 파일에서 뽑는다.
