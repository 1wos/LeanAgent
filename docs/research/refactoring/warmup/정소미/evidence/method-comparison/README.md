# 평가 기준에 따른 후보 선택과 실패 집계

정소미 · 2026-10-18 · Week 3 실행관리·평가·재현

같은 후보에 평가 기준을 다르게 적용했을 때 선택과 보고값이 어떻게 달라지는지 확인한다. 2주차에 만든 4번 후보 15개와 9번 후보 13개를 전부 사용한다. 참조 증명 두 개도 새로 실행한다. 후보 생성은 다시 하지 않는다.

## 사전에 고정한 것

[protocol.json](protocol.json)에 실행 전 시각, 입력 파일·환경의 해시, 후보 목록, 실행 순서의 난수 시드, 평가 방법과 비교 대상을 기록했다. 4·9번은 이전 시도에서 결과를 보며 만든 후보들이므로 독립적인 모델 표본이 아니다. 과거 결과를 이미 알고 있는 후향 분석이며, 새로 등록한 전향 실험으로 소개하지 않는다.

- 4·9번: Lean v4.32.0의 지정 프로젝트·의존성 커밋, 각 입력 1회. 전체 문맥 검사와 heartbeat 측정을 각각 실행한다.
- 모든 과거 후보를 포함한다. 실패한 시도, 기각한 시도, 토큰이 늘어난 시도를 제거하지 않는다. `final.lean`은 이미 시도 목록에 같은 증명이 있어 중복 추가하지 않는다.
- 실행 순서는 시드 20261018로 섞었다. 경과 시간은 운영 기록이며 이 실험의 후보 선택 지표가 아니다.

공유한 실행에서는 17건을 완료한 뒤 나머지를 3개 작업으로 병렬 실행했다. 완료된 결과는 유지하고, 중단 시 저장되지 않은 입력만 다시 실행했다. 재개 시각·작업 수·사용 스크립트 해시는 환경 기록의 `continuation`에 남겼다. 순차 실행 명령은 아래와 같으며, 이번 재개에 사용한 코드는 [finish_pool.py](finish_pool.py)에 있다. 병렬 실행의 경과 시간으로 후보별 속도를 비교하지 않는다.

## 논문과 계산 방법

### 1. ProofOptimizer: min@k / red@k

[ProofOptimizer §2](https://www.alphaxiv.org/pdf/2510.15700)는 검증 실패나 원본보다 긴 후보를 원본 길이로 취급한다. 유효 비용을 `min(참조 길이, 후보 길이)`로 두고, k개 중 최솟값을 min@k, `1 − min@k / 참조 길이`를 red@k로 계산한다. §5.2.1은 같은 최적화 틀의 비용을 heartbeat로 바꾼다.

여기서는 k=1, 2, 4, 8과 전체 후보 수에서 가능한 모든 부분집합을 열거해 평균을 계산한다. 이것은 고정된 후보 목록에서 균등하게 k개를 뽑았을 때의 정확한 평균이다. 논문이 모델에서 새로 생성한 표본에 대해 계산한 기대 성능과 구분한다. k는 추가 LLM 호출 수나 달러 예산을 뜻하지 않는다.

### 2. ImProver: 실패를 포함한 개선량

[ImProver §4](https://www.alphaxiv.org/pdf/2410.04753)는 올바른 출력을 만들지 못하면 개선량을 0으로 두어 오류를 평가에 반영한다. 이 원칙을 후보 단위로 적용해 `성공 후보의 상대 개선량 합 / 전체 시도 수`를 계산한다. 유효하지만 원본보다 긴 후보의 음수 개선량은 유지한다. 성공률과 개선된 시도의 비율도 함께 기록한다.

비교용으로 성공한 후보만 분모에 둔 평균을 계산한다. 이 비교값은 우리가 정한 진단값이며 논문의 `nonempty improvement`와 동일하다고 주장하지 않는다. 원문은 정리 단위 평가이고 길이 지표가 tactic 호출 수다. 여기서는 과거 후보 단위·구문 토큰 수로 바꿨으므로 모델 정확도나 원문 수치를 재현한 실험이 아니다.

### 3. Lean Refactor: 여러 지표와 선택 기준

[Lean Refactor §4.2·부록 L](https://www.alphaxiv.org/pdf/2605.20244)의 길이·heartbeat 측정을 사용한다. 후보 선택은 길이 최소, heartbeat 최소, 두 정규화 비용의 같은 비중 평균을 비교한다. 마지막 가중합과 가중치 민감도 분석은 이 실험의 비교 규칙이며, 논문의 전략 검색·재정렬 알고리즘을 구현한 것이 아니다.

`C(w) = w × 길이/참조 길이 + (1−w) × heartbeat/참조 heartbeat`를 최소화한다. 가중치는 0부터 1까지 비교한다. 후보별 비용 직선이 만나는 지점을 모두 구해 최선 후보가 같은 구간을 합친다. 경계에서 동률이면 길이, heartbeat, 후보 이름 순으로 선택한다. 한 지표도 개선하지 못하면서 다른 지표가 더 나쁜 후보를 제외한 Pareto 목록도 저장한다. 이는 후보 선택의 보조 분석이며 특정 논문의 고유 기법으로 귀속하지 않는다.

### 4. 재현 자료 구성

[Arvan·Pina·Parde, EMNLP 2022, §3](https://aclanthology.org/2022.emnlp-main.150.pdf#page=2)를 참고해 입력·환경·실행 기록과 표 생성 스크립트를 함께 제공한다. 이 부분은 산출물 구성 원칙이며 다른 평가 알고리즘과의 성능 비교 대상은 아니다. 다른 컴퓨터나 빈 환경에서의 재현은 확인하지 않았다.

## 다시 실행하기

기존 [환경 준비 안내](../reproducibility/README.md)에 따라 PhysLib·CSLib v4.32.0을 준비한다. 저장소 루트에서 실행한다. `repos.json`은 기존 [경로 예시](../reproducibility/repos.example.json)의 형식이며 `p4-4.32`, `p9-4.32` 두 항목이 필요하다. 출력 디렉터리는 새로 지정한다.

```sh
python3 docs/research/refactoring/warmup/정소미/evidence/method-comparison/compare_methods.py \
  pool --repos /path/to/repos.json --output /tmp/method-pool
python3 docs/research/refactoring/warmup/정소미/evidence/method-comparison/compare_methods.py \
  analyze --pool /tmp/method-pool --output /tmp/method-tables
```

## 공유 기록

- [후보 28개와 참조 2개의 실행 결과](results/pool/results.json), [환경](results/pool/environment.json), [원시 출력](results/pool/logs/).
- [실패 포함 집계](results/analysis/failure_accounting.csv), [선택 결과](results/analysis/selection.csv), [후보 수별 결과](results/analysis/budget_curve.csv).
- [가중치별 선택 구간](results/analysis/weight_intervals.csv), [Pareto 후보](results/analysis/pareto_frontier.csv).

표 생성만 다시 확인하려면 마지막 명령의 입력을 이 폴더의 `results/pool`로 바꾸고 새 출력 폴더를 지정한다. Lean 실행은 필요 없다.

대상 범위와 문서를 정리하면서 14건의 결과가 저장된 시점에 예비 실행을 중단하고, 새 출력 폴더에서 전부 다시 실행했다. 공유 결과에는 최종 실행만 포함한다. 중단 전 기록은 최종 결과의 표본 수나 경과 시간에 합산하지 않았다.
