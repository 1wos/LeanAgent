# ATP 입문과 Warm-up 3·6·13 학습 노트

작성자: 권주원 · 시작일: 2026-10-06 · 상태: 학습 진행 중.

이 문서는 대화 중 이해한 개념, 논문 근거, 실제 검증을 구분해 누적한다. 세 문제의 새 풀이와 성능 측정은 아직 수행하지 않았다.

## 학습 순서와 결과물

1. Lean의 명제·증명·proof state·tactic을 작은 실행 예제로 이해한다.
2. ATP의 전제 선택·증명 생성·탐색·검증을 구분한다.
3. 3번의 가정과 목표, 기존 보조정리 재사용을 읽는다.
4. 13번의 유한 상태와 eventual periodicity를 이해한다.
5. 6번의 비가환 곱셈·부호·선형성·기저 환원 구조를 읽는다.
6. LeanDojo를 중심으로 논문을 분석하고, 문제별 개선 가설과 실험 조건을 정리한다.

공유 시에는 각 문제의 자연어 설명, 원본 증명의 구조, 개선 가설, 실행 환경, 검증 결과를 함께 제시한다. 이해한 설명과 미검증 후보를 완료된 실험으로 표시하지 않는다.

## 1. Lean으로 증명을 읽는 출발점

명제(statement)는 증명해야 할 주장이다. 증명(proof)은 그 주장의 근거이며, Lean에서는 해당 명제의 타입을 가진 항으로 표현된다. Tactic은 그 증명항을 만드는 작업을 돕는다.

Proof state는 현재 사용할 수 있는 가정과 남은 목표를 보여준다. `⊢` 오른쪽이 목표다. 여러 목표가 있으면 모두 해결해야 증명이 끝난다.

| 표기 | 읽는 방법 |
| --- | --- |
| `P : Prop` | P는 명제다 |
| `h : P` | h는 P의 증명이다 |
| `P ∧ Q` | P와 Q가 모두 참이다 |
| `P → Q` | P가 참이라는 가정에서 Q를 보인다 |
| `∀ n, ...` | 모든 n에 대해 성립한다 |
| `∃ n, ...` | 조건을 만족하는 n을 하나 제시한다 |

다음 예제는 OT의 논리 예제를 다시 사용한다.

```lean
theorem swapAnd (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h
  constructor
  · exact h.2
  · exact h.1
```

- `intro h`: `P ∧ Q`가 참이라고 가정하고 그 증명을 h라고 부른다.
- `constructor`: `Q ∧ P`를 증명하기 위해 Q와 P 두 목표로 나눈다.
- `h.1`은 P의 증명이고 `h.2`는 Q의 증명이다.
- `exact h.2`: 현재 목표 Q에 맞는 증명을 제출한다.
- `·`: 각 하위 목표의 증명을 구분한다.

첫 목표 Q에 `h.1`을 제출하면 타입이 맞지 않는다. 이것은 문자열의 이름 문제가 아니라 필요한 명제 Q와 제출한 증명의 명제 P가 다른 문제다.

같은 예제에서 이미 증명된 `swapAnd P Q`를 `exact`로 재사용할 수도 있다. 큰 라이브러리에서 현재 목표에 맞는 정리·정의를 골라오는 것이 premise selection(전제 선택)의 출발점이다.

실행 파일: [examples.lean](examples.lean). `trace_state`를 넣어 실제 proof state를 확인할 수 있다.

공식 설명: [Lean tactic reference](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/Tactic-Reference/). 이 문서의 최신 버전과 로컬 실행 버전은 다를 수 있으므로 예제 검증에는 명시한 버전을 사용한다.

## 2. ATP가 자동화하는 것

형식 명제가 주어졌을 때 기계가 증명을 찾는 작업이 Automated Theorem Proving이다. Lean 자체는 사람과 상호작용하는 proof assistant이며, 그 위에 자동 탐색 시스템을 연결할 수 있다.

```text
현재 증명 상태
  → 도움이 될 정리·정의 검색
  → 다음 tactic 후보 생성
  → Lean에서 실행
  → 새 상태 또는 오류 확인
  → 다음 후보 선택 / 이전 상태에서 다시 시도
  → 모든 목표 해결 후 완성된 증명 검증
```

| 구성 요소 | 답해야 할 질문 |
| --- | --- |
| 전제 선택 | 어떤 기존 정리·정의가 도움이 되는가? |
| 증명 생성 | 다음 tactic이나 전체 증명을 어떻게 만들 것인가? |
| 탐색 | 여러 후보와 증명 경로 중 무엇을 먼저 시도할 것인가? |
| 검증 | 만든 증명이 주어진 형식 명제에 맞는가? |

LLM 기반 prover와 외부 symbolic ATP를 연결하는 hammer는 서로 다른 구성이며 결합할 수도 있다. LeanHammer 논문은 전제 선택, 외부 증명기로의 변환, Lean 증명 복원을 하나의 파이프라인으로 설명한다. [Premise Selection for a Lean Hammer, v2](https://arxiv.org/html/2506.07477v2)

이번 대회에서는 기존 증명을 개선한다. 증명 성공률을 높이는 연구 아이디어가 길이·검증 비용·버전 호환성도 개선하는지는 별도로 측정해야 한다. Lean 검증은 형식 명제의 증명을 확인하며, 자연어 문제를 올바르게 형식화했는지는 별도 검토 대상이다.

## 3. 담당 Warm-up 문제

배정 근거: [Week 2](../../../../../meetings/2026-10-11-week2/README.md).
2026-10-06 공식 JSONL의 1부터 시작하는 순서에서 3·6·13번 ID, statement, version_info를 확인했다. 공식 Space의 확인 시점 HEAD는 `56aa7b8f738d1d6a0a24a55e03cdea1a84007b6c`다.
[공식 데이터](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/blob/56aa7b8f738d1d6a0a24a55e03cdea1a84007b6c/benchmark_data_warmup.jsonl).

| 번호 | 문제 ID | 주제 | 지정 Lean 버전 |
| --- | --- | --- | --- |
| 3 | `Core.InitsUpdatesComm` | 기존 변수 갱신과 새 변수 초기화의 순서 교환 | 4.26.0 / 4.27.0 / 4.29.1 |
| 6 | `FieldSpecification.WickAlgebra.ι_timeOrderF_superCommuteF_eq_time` | 시간 정렬과 supercommutator | 4.32.0 |
| 13 | `putnam_1964_a4` | 유계 정수 점화수열의 eventual periodicity | 4.25.0 / 4.26.0 / 4.27.0 |

### 3번: 상태 갱신의 순서를 바꾸기

`σ`, `σ'`, `σ''`는 변수와 값을 관리하는 상태다. `UpdateStates`는 기존 변수들의 값을 갱신하는 관계, `InitStates`는 새 변수들을 초기화하는 관계다.

```text
주어진 실행: σ --기존 변수 갱신--> σ' --새 변수 초기화--> σ''
보일 실행:   σ --새 변수 초기화--> σ₁ --기존 변수 갱신--> σ''
```

목표는 두 번째 실행의 중간 상태 σ₁을 제시하고 필요한 관계들을 증명하는 것이다. 모든 변수 쓰기가 교환되는 것은 아니다. 기존 변수와 새 변수에 대한 조건이 핵심이다.

첫 학습 과제: `UpdateStates ... → InitStates ... → ∃ σ₁, A ∧ B ∧ C`를 두 가정과 존재 증명, 세 하위 주장으로 나눠 읽기.

기존 로컬 노트에서는 목록에 대한 귀납 증명을 `updatedStatesComm` 등 보조정리 재사용으로 바꾼 사례를 보고한다. 이는 이번 세션에서 재실행한 결과가 아니다. 전제 선택이 증명 구조를 바꾸는 예제로 분석한다.

### 13번: 왜 네 항을 묶는가?

정수 수열 `u : ℕ → ℤ`가 위아래로 유계이고, 직전 네 항으로 다음 항을 결정하는 점화식과 분모의 비영 조건을 만족한다. 목표는 어떤 N 이후 양의 주기 c로 반복됨을 보이는 것이다.

```text
S(n) = (u(n), u(n+1), u(n+2), u(n+3))
유계 정수 → 가능한 S(n)이 유한
무한히 많은 n → 같은 상태 S(i) = S(j), i < j가 등장
같은 상태 + 다음 항을 결정하는 점화식 → 이후 상태도 계속 같음
따라서 N = i, c = j-i > 0인 eventual periodicity
```

유계라는 조건만으로 주기성이 나오지는 않는다. 같은 상태에서 다음 상태가 정해지는 성질이 필요하다. 한 항이 우연히 같다는 사실만으로는 직전 네 항을 사용하는 점화식의 다음 항이 같다고 할 수 없다.

첫 학습 과제: 단일 항 대신 네 항의 상태를 써야 하는 이유, 유계와 정수라는 두 조건의 역할, N 이전 구간이 반복될 필요는 없다는 점 설명하기.

### 6번: 곱셈의 순서와 부호를 보존하기

두 연산자의 시간 정렬 관계가 양방향으로 성립한다는 가정 아래, `a`와 `b` 사이의 supercommutator를 포함한 식에 시간 정렬과 `ι`를 적용한 결과를 비교한다. 전문적인 표기와 정의는 원본 파일에서 하나씩 확인한다.

원본의 큰 구조는 span induction으로 일반 대수 원소를 리스트 기저 원소로 환원하고, 정렬과 부호를 정리하고, `ι` 이후 중심성에 관한 정리로 필요한 곱 순서 이동을 정당화하는 것이다.

첫 학습 과제: `a * b = b * a`를 일반적으로 가정할 수 없는 이유와 supercommutator의 통계 부호가 필요한 이유 이해하기. 증명 최적화 전에 사용된 정의·보조정리를 정리한다.

## 4. 논문 읽기

### 주논문: LeanDojo / ReProver

[LeanDojo v2](https://arxiv.org/html/2306.15626v2)의 §3에서 Lean 증명 상태를, §4에서 데이터와 상호작용 환경을, §5에서 검색·tactic 생성을 읽는다. §6과 Appendix D에서 실험을 확인한다.

LeanDojo는 환경·데이터·도구이고 ReProver는 그 위에서 검색을 결합한 prover다. 현재 상태에 맞는 전제를 검색하고, 상태와 검색 결과로 tactic 후보를 만들며, best-first search로 증명 경로를 탐색한다.

논문 본문은 Lean 3를 기본으로 다루고 Lean 4 결과는 Appendix D에 있다. 두 버전의 결과 표를 혼동하지 않는다. `novel_premises` 분할은 학습 증명에서 사용되지 않은 전제가 필요한 시험 문제를 구성한다. 검색을 통한 일반화를 분석하는 장치다.

읽고 답할 질문:

1. 다음 tactic 생성에 검색된 전제가 왜 도움이 되는가?
2. 현재 위치에서 접근 가능한 전제만 검색하는 이유는 무엇인가?
3. 후보 생성과 best-first search의 역할은 어떻게 다른가?
4. retrieval 제거 실험은 어떤 주장을 뒷받침하는가?
5. 3번에서 프로젝트의 보조정리를 찾는 데 무엇을 적용할 수 있는가?

### 비교 논문

| 논문 | 확인할 핵심 | Warm-up과 연결할 질문 |
| --- | --- | --- |
| [Lean-auto v2](https://arxiv.org/abs/2505.14929v2) | Lean의 dependent type theory에서 외부 ATP의 논리로 옮기는 변환 | 어떤 하위 목표를 외부 solver에 보낼 수 있는가? |
| [Premise Selection for a Lean Hammer v2](https://arxiv.org/html/2506.07477v2) | LeanPremise와 LeanHammer, 로컬 정의·정리를 포함한 전제 선택 | 학습 데이터 밖의 프로젝트 정리를 어떻게 활용하는가? |

주논문의 구조를 이해한 뒤 비교 논문으로 확장한다. 논문 기여를 설명할 때 연구자의 결과, 우리 해석, 아직 검증하지 않은 적용 가설을 구분한다.

## 5. 실행 기록과 다음 학습

2026-10-06 OT의 `example.lean`과 새 학습 예제의 세 정리를 Lean 4.26.0으로 실행해 각각 종료 코드 0을 확인했다. Mathlib는 이 입문 예제에 필요하지 않다.

저장소 루트에서 실행한 명령:

```sh
source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent
lean +leanprover/lean4:v4.26.0 docs/research/automated-theorem-proving/권주원/studies/2026-10-06/examples.lean
```

`trace_state`의 실제 출력:

```text
P Q : Prop
⊢ P ∧ Q → Q ∧ P
P Q : Prop
h : P ∧ Q
⊢ Q ∧ P
case left
P Q : Prop
h : P ∧ Q
⊢ Q
case right
P Q : Prop
h : P ∧ Q
⊢ P
```

각 출력은 차례로 첫 상태, `intro h` 직후, 첫 번째 하위 목표, 첫 목표 해결 후 두 번째 하위 목표다. `swapAndViaPremise`와 `existsSelf`도 같은 실행에서 검증됐다.

세 Warm-up의 원본·후보는 이번 세션에서 아직 컴파일하지 않았다. 3번의 과거 성공 기록, 6·13번의 과거 환경 미완성 기록은 옆 저장소 `01_LEArN/examples/lean-refactor/problems/`의 노트에서 확인했다. 환경과 증명 상태는 재검증 전까지 현재 결과로 옮기지 않는다.

- [ ] `P ∧ Q → Q ∧ P`의 가정과 목표를 읽는다.
- [ ] `intro`, `constructor`, `exact` 전후의 상태를 설명한다.
- [ ] 3번의 명제를 읽고 σ₁이 필요한 이유를 설명한다.
- [ ] LeanDojo의 검색·생성·탐색을 구분한다.
- [ ] 13번의 유한 상태 논증을 자연어로 정리한다.
- [ ] 6번의 정의와 핵심 보조정리 의존성을 정리한다.
- [ ] 원본 재현 후 작은 후보를 검증하고 같은 환경에서 측정한다.
