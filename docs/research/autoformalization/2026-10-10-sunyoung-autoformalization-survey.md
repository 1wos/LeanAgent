# Autoformalization 논문 조사 개요

- 작성: 박선영 · 2026-10-10 (LeanAgent Week 2 조사 자료)
- 발표자료: [HTML 슬라이드](2026-10-10-sunyoung-autoformalization-survey/viewer.html) · [발표 구성안](2026-10-10-sunyoung-autoformalization-survey/slide-outline.md)
- 범위: [papers.md](../papers.md)에서 `Autoformalization` 태그가 붙은 8편
- 추가 조사: papers.md 목록 밖의 최신 논문 10편 — 6장
  - 03 Process-Driven Autoformalization in Lean 4 · 04 An Evaluation Benchmark for Autoformalization in Lean4 · 05 TheoremLlama · 08 Herald · 19 ProofBridge · 22 miniF2F-Lean Revisited · 23 NL2Lean · 33 LLM-Generated Conjectures to Lean (SOS)
- 근거 표시: 03·04·08·19·22·23번은 arXiv abstract(23번은 논문 PDF)를 직접 확인해 요약했다. 05·33번은 abstract 확인에 실패해 papers.md 설명만 사용했으며 해당 항목에 표시했다. 03번 세부 구성은 공식 GitHub README로 보강했다. 6장의 10편은 2026-10-10에 arXiv API("autoformalization" + "Lean")로 검색해 abstract를 직접 확인했다.

## 1. 개요

Autoformalization은 자연어로 쓰인 수학 명제와 증명을 Lean 4 같은 형식 언어로 바꾸는 작업이다. LLM이 생성한 증명을 기계적으로 검증하려면 문제 자체가 정확한 formal statement여야 하므로, 이 분야는 검증 기반 에이전트 파이프라인에서 "문제 이해 → Lean 코드 생성" 앞단을 담당한다. 조사한 8편은 크게 세 흐름으로 묶인다.

- 번역: NL–Lean 병렬 데이터를 만들고 statement 번역 모델을 학습 (Herald, TheoremLlama)
- 검증 피드백: Lean 컴파일러·타입 체커 피드백을 학습 신호와 수정 루프에 사용 (PDA, NL2Lean, ProofBridge)
- 프로세스/평가: 무엇을 "올바른 번역"으로 볼지 정의하고 벤치마크 정합성을 점검 (Evaluation Benchmark, miniF2F-Lean Revisited, SOS 논문)

조사 대상별 근거 확인 상태:

| 번호 | 논문 | abstract 확인 | 요약 근거 |
| --- | --- | --- | --- |
| 03 | Process-Driven Autoformalization in Lean 4 | 확인 | arXiv abstract + 공식 GitHub README |
| 04 | An Evaluation Benchmark for Autoformalization in Lean4 | 확인 | arXiv abstract |
| 05 | TheoremLlama | 미확인 | papers.md 설명 + Herald 비교표 수치 |
| 08 | Herald | 확인 | arXiv abstract |
| 19 | ProofBridge | 확인 | arXiv abstract |
| 22 | miniF2F-Lean Revisited | 확인 | arXiv abstract |
| 23 | NL2Lean | 확인 | ACL Anthology 논문 PDF (abstract·실험 절) |
| 33 | LLM-Generated Conjectures to Lean (SOS) | 미확인 | papers.md 설명 + 논문 제목 |

## 2. 핵심 논문 요약

### 2.1 Herald — 자연어 주석 Lean 4 데이터셋 (08번)

- 문제: Lean용 LLM을 학습시키려면 자연어 증명과 형식 증명이 정렬된 병렬 데이터가 필요한데, 이런 데이터가 부족하다.
- 방법: 자연어→Lean 방향 데이터를 모으기 어려우므로 Mathlib4를 자연어로 번역하는 파이프라인으로 방향을 뒤집었고, tactic 기반 + informal 기반 이중 증강과 Lean 4 분석기 Lean-jixia로 데이터를 구성했다.
- 결과: 이 데이터로 학습한 Herald Translator는 miniF2F-test statement 형식화에서 Pass@128 93.2%(비교: InternLM2-Math-Plus-7B 74.0%, TheoremLlama 50.1%), 자체 대학원 수준 교과서 데이터셋에서 22.5%를 기록했다.
- 의의: 대규모 NL–Lean 4 병렬 데이터와 번역 모델을 공개해 이후 번역·학습 연구의 기반을 제공했고, section 단위 번역으로 Stack project의 한 섹션을 번역한 실제 적용 사례도 보였다.

### 2.2 Process-Driven Autoformalization in Lean 4 — PDA·FormL4·PSV (03번)

- 문제: 기존 autoformalization 연구는 온라인 코퍼스가 풍부한 형식 언어에 머물러, 빠르게 발전하는 Lean 4를 따라가지 못한다.
- 방법 (데이터): Mathlib4 정리를 Gemini-1.5-Pro로 자연어화하고 수작업 검수를 거쳐 Lean 4 전용 벤치마크 FormL4(Formalization for Lean 4)를 구축했다. train 14,250 · basic 970 · random 950 · Arithmo 기반 out-of-domain real 967문항으로 이루어진다.
- 방법 (학습): autoformalizer의 출력에 Lean 4 컴파일러의 정밀한 피드백을 붙여 과정(process) 단위 라벨을 만들고, 이 라벨로 Process-Supervised Verifier(PSV)를 학습시킨 뒤 verifier의 판정을 이용해 autoformalizer를 다시 fine-tune하는 순환을 돌렸다.
- 결과: 컴파일 성공분만 골라 학습하는 RFT보다 PSV 검증을 결합할 때 적은 필터링 데이터로 더 높은 형식화 정확도를 냈다(GitHub README 기준 basic 셋 40.92 → 46.28). 참고로 기존 LLM은 이 벤치마크에서 매우 낮은 점수를 기록했다(GPT-4-Turbo real 셋 Greedy 10.2%).
- 의의: 컴파일러 피드백을 "성공/실패 신호"가 아니라 "과정 감독 신호"로 활용하는 길을 열었고, Lean 4 전용 벤치마크 결핍을 채웠다.

### 2.3 NL2Lean — 다면 보상 강화학습 (23번, 프레임워크명 ReLean)

- 문제: 기존 LLM은 instruction tuning에 의존해 세밀한 구조·의미 정렬이 부족하고, 구문·논리적으로 타당한 Lean 4 statement를 잘 만들지 못한다.
- 방법: LLaMA3-8B를 NL–Lean 4 데이터로 fine-tune한 기본 번역기 위에서, ① 의미 정렬 ② term(하위항) 정렬 ③ 전체 구조 정렬(token edit distance) ④ 컴파일 체크(REPL 기반 이진 보상) 네 차원의 보상 모델을 preference 학습으로 만들고, 정규화·가중 합산한 점수로 PPO를 돌린다. 여기에 세 차원 난이도 기준의 쉬운 것→어려운 것 커리큘럼을 결합했다.
- 결과: "컴파일되면서 의미도 맞는" statement 비율 기준으로 Lean Workbook 26.6%·ProofNet 19.2%를 달성해 baseline과 Herald(Lean Workbook 22.4%)를 넘었고, 컴파일 보상 단독으로는 의미 충실도가 확보되지 않음을 ablation으로 보였다.
- 의의: 컴파일 가능성과 의미 충실도를 함께 끌어올리는 다차원 보상 설계의 대표 사례다. 다만 평가가 사람 annotation에 의존한다는 한계를 논문 스스로 밝혔다.

### 2.4 ProofBridge — 증명 전체 번역과 의미적 일치 (19번)

- 문제: 기존 방법은 statement만 번역하거나 formal statement에서 증명을 합성하는 데 그쳐, 정리+증명 전체를 옮기는 데는 사람 개입이 필요했다(AlphaProof가 문제 statement를 수동 번역한 사례를 근거로 제시).
- 방법: NL–FL 정리+증명 쌍을 공유 의미 공간에 정렬하는 joint embedding으로 번역에 도움 되는 formal 예시를 검색하고, retrieval-augmented fine-tuning과 반복 proof repair를 결합했다. Lean의 타입 체커 피드백과 의미 등가 피드백을 수정 루프에 사용했다.
- 평가: 타입 체크를 통과하는 TC(type correctness)와, 양방향 equivalence를 증명해 의미가 같음을 보이는 SC(semantic correctness)를 분리해 측정했다. 평가용으로 miniF2F-Test-PF를 자체 구축했다.
- 결과: Kimina-Prover-RL-1.7B 대비 SC +31.14%p·TC +1.64%p(pass@32), joint embedding의 Recall@1은 all-MiniLM-L6-v2 대비 최대 3.28배.
- 의의: statement를 넘어 증명 전체의 자동 번역·수정 프레임을 제시했고, 검색 기반 예시 제공이 의미 충실도를 크게 끌어올림을 보였다.

### 2.5 나머지 4편

**04 · An Evaluation Benchmark for Autoformalization in Lean4**

- 문제: Lean 4의 등장으로 LLM 형식화 능력을 엄밀하게 잴 필요가 생겼다.
- 방법: GPT-3.5·GPT-4·Gemini Pro를 대상으로 Lean 4 형식화 능력을 평가하는 벤치마크를 적용했다.
- 의의: 당시 최신 LLM도 복잡한 수학 영역에서는 형식화 능력이 부족함을 보여 자동 평가의 필요성을 제기했다.

**22 · miniF2F-Lean Revisited**

- 문제: miniF2F의 formal·informal statement가 서로 맞지 않아 벤치마크 자체의 신뢰성에 문제가 있다.
- 방법: "문제 읽기 → Lean 형식화 → 증명" 전체 파이프라인 관점에서 불일치를 추적하고, 오류·불일치·단순화를 모두 고친 miniF2F-v2를 공개했다.
- 의의: 개별 단계 최고 성적(형식화 97%·증명 69%)과 달리 전체 파이프라인은 약 36%에 그침을 보여 statement 정합성이 병목임을 드러냈고, v2에서는 70%까지 올라갔다.

**05 · TheoremLlama** — abstract 미확인, papers.md 설명 기반

- papers.md 요약: 자연어–Lean 증명 데이터, 모델 학습과 반복 증명 작성.
- 보조 근거: Herald 논문 비교표에서 miniF2F-test 형식화 50.1%(Pass@128)로 수록돼 있다. 문제·방법 세부는 원문 확인 필요.

**33 · From LLM-Generated Conjectures to Lean Formalizations (SOS)** — abstract 미확인, papers.md 설명 기반

- papers.md 요약: LLM의 SOS(Sum-of-Squares) 후보 생성 → 기호 계산 → Lean 인증.
- 제목상 "LLM 추측 생성 → 형식적 인증" 흐름을 다루는 것으로 보이며, 세부는 원문 확인 필요.

## 3. 연구 흐름

시간 순으로 보면 04·03(2024-06) → 08 Herald(2024-10) → 19 ProofBridge(2025-10) → 23 NL2Lean(EMNLP 2025, 11월) · 22 miniF2F-Lean Revisited(2025-11) 순서다. 컴파일 피드백 활용이 2024년에 시작돼 2025년에 보상 설계와 증명 전체 번역으로 확장된 흐름이다.

### 3.1 번역 — 병렬 데이터와 statement 번역기

- 병렬 데이터 확보가 출발점이다. Herald는 Mathlib→자연어 역방향 번역으로, PDA는 LLM informalization + 수작업 검수로 NL 쪽 데이터를 "만들어내는" 전략을 썼다.
- 데이터가 확보되자 전용 번역기가 이어졌다. fine-tune 기반(Herald Translator)에서 다면 보상 강화학습(ReLean)으로 학습 신호가 정교해졌다.
- 번역 대상도 statement(Herald, NL2Lean)에서 정리+증명 전체(ProofBridge)로 확대되는 중이다.

### 3.2 검증 피드백 — 컴파일러를 학습·수정 신호로

- 초기에는 컴파일 성공 여부로 학습 데이터를 거르는 수준이었다(PDA의 RFT 비교 대상).
- PDA는 컴파일러 피드백의 내용을 과정 라벨로 만들어 verifier를 학습시켰고, NL2Lean은 컴파일 체크를 네 보상 중 하나로 다른 정렬 보상과 결합했다.
- ProofBridge는 타입 체커와 의미 등가 피드백으로 반복 repair를 돌렸다.
- 공통점은 "검증기의 피드백을 다음 시도에 되먹이는" 구조로, LeanAgent가 목표로 하는 검증 루프와 같은 방향이다.

### 3.3 프로세스/평가 — 올바른 번역의 기준

- 컴파일·타입 체크 통과만으로는 부족하다. 의미가 달라도 컴파일되는 statement가 존재한다(NL2Lean이 컴파일률과 정확도를 분리해 보고, ProofBridge가 TC/SC를 분리).
- 의미 일치(SC) 측정은 아직 무거운 편이다. 양방향 equivalence 증명(ProofBridge)이나 사람 annotation(NL2Lean — 비용 한계 인정)에 의존한다.
- 벤치마크 자체의 정합성도 평가 대상이 됐다. miniF2F의 formal–informal 불일치가 파이프라인 성능 저하의 주요 원인으로 지적됐다(miniF2F-Lean Revisited).
- 평가 단위는 statement 번역 → 증명 번역 → 전체 파이프라인 순으로 넓어지고 있다.

## 4. 평가 벤치마크

| 벤치마크·데이터셋 | 등장 논문 | 내용 |
| --- | --- | --- |
| miniF2F(-test) | (기존 벤치마크, 22번에서 분석) | 수학 올림피아드 문제의 formal/informal statement 모음. statement 번역 평가에 널리 쓰임(Herald Pass@128 93.2%) |
| miniF2F-v2 | miniF2F-Lean Revisited | formal·informal 오류·불일치·단순화를 수정한 판. 전체 파이프라인 40% → 70% |
| miniF2F-Test-PF | ProofBridge | 증명까지 포함한 번역 평가를 위해 저자들이 구축한 데이터셋 |
| FormL4 | PDA | Mathlib4 기반 train/basic/random + Arithmo 기반 real(out-of-domain) |
| Lean Workbook · ProofNet | NL2Lean 평가셋 | statement 번역 평가에 사용. ProofNet은 학부 수준 수학 형식화 벤치마크(NL2Lean 참고문헌 기준) |
| 대학원 교과서 데이터셋 | Herald (내부) | miniF2F보다 어려운 실제 교과서 수준 문장으로 22.5% 기록 |

지표 정리:

- 컴파일률(compile rate): 생성 statement가 컴파일되는 비율 (NL2Lean)
- 정확도: 컴파일되면서 의미까지 맞는 비율 (NL2Lean — 사람 판정)
- pass@k: k개 샘플 중 하나라도 성공할 확률 (Herald Pass@128, ProofBridge pass@32)
- TC / SC: 타입 체크 통과 / 양방향 equivalence 증명으로 확인한 의미 일치 (ProofBridge)
- 파이프라인 성공률: 형식화부터 증명까지 통과한 비율 (miniF2F-Lean Revisited)

주의점: miniF2F는 statement 정합성 문제가 지적된 벤치마크다. 결과를 비교할 때는 버전(v1/v2)과 판정 기준(컴파일만 볼지 의미까지 볼지)을 반드시 함께 명시해야 한다.

## 5. 우리 프로젝트 적용점

- 문제 이해 단계의 번역 품질이 전체 성공률의 상한을 정한다. miniF2F-Lean Revisited처럼 자연어 문장과 Lean statement가 같은 뜻인지 먼저 점검하는 체크 단계를 harness에 두면, prover 실패와 statement 오류를 구분해 기록할 수 있다.
- 컴파일 통과(TC)와 의미 일치(SC)를 별도 필드로 기록한다. "컴파일은 되지만 문제가 다른" 실패 유형을 추적해야 수정 전략이 정확해진다(ProofBridge, NL2Lean의 지표 분리 참고).
- 컴파일러 피드백을 구조화해 다음 시도 선택에 쓴다. PDA의 과정 라벨과 ProofBridge의 반복 repair처럼 오류 메시지를 유형별로 정리하면 LeanAgent의 "오류 분석 → 수정" 루프 설계의 직접적인 근거가 된다.
- NL–formal 병렬 예시를 프롬프트에 넣는 방식을 실험할 만하다. ProofBridge가 검색 기반 예시 제공으로 SC를 크게 올렸고, Herald 같은 공개 병렬 데이터에서 유사 문제 예시를 찾아 제공하는 few-shot 구성을 비교 대상으로 삼을 수 있다.
- 평가는 자동 기록 중심으로 설계한다. NL2Lean이 사람 annotation 의존의 비용 한계를 인정하므로, 우리 harness는 컴파일 결과·pass@k·실행 시간·비용 같은 자동 수집 지표를 축으로 하고 사람 판정은 소표본으로만 쓴다.
- 벤치마크를 쓸 때는 버전과 판정 기준을 명시한다. miniF2F 계열은 v1의 statement 불일치 이슈가 있으므로, 실험 보고에 v1/v2와 성공 판정 기준을 함께 적는다.

## 6. 추가 조사 — papers.md 목록 밖의 최신 논문 (2026-04~10)

papers.md의 8편이 2024~2025년 중심인 데 비해, 2026년 논문은 ①의미 일치(충실성) 평가 ②검색·컴파일러 피드백을 결합한 파이프라인과 데이터 구축 ③연구 수준 문서를 대상으로 한 장기 형식화 에이전트의 세 축으로 발전하고 있다. 2026-10-10 기준 arXiv 최신 45편에서 papers.md와 중복되지 않는 10편을 골랐고, 전부 abstract를 직접 확인했다.

### 6.1 의미 일치(충실성) 평가 — "컴파일된다"와 "같은 정리다"를 분리

- **Beyond Compilation** (2606.31002, 2026-06) — GPT-5.2·Gemini-2.5-Pro 합의 + Lean 컴파일을 충실성 판정 기준으로 제안. 대학원 수준 227문제·8개 시스템에서 컴파일률-충실성 격차가 1.3~29.5%p로 시스템별로 크게 벌어지고, 도구 에이전트가 Lean 피드백으로 얻은 컴파일 개선의 절반가량이 의미 기준에서 탈락함을 보였다.
- **SHADOWBENCH · SA-Pass** (2608.29270, 2026-08) — 의도한 명제를 특정하는 보조 명제(shadow)들의 함축을 순·역방향으로 검사하는 SA-Pass 지표. 대학원~연구 수준 178문제 Lean 4 벤치마크, 전문가 판정과 98.8% 일치. 초기 버전이 ICML 2026 AI4Math Challenge Track 4에 사용됐다.
- **The Faithfulness Gap · BPF** (2606.16541, 2026-06) — 순·역방향 귀결 이웃을 '지문'으로 쓰는 Bidirectional Provability Fingerprinting으로 의미 표류(drift)를 검출(89.6%, typecheck은 41.2%). NL/Lean 4 쌍 2,183개의 DriftBench를 공개했다.
- **Evaluating the Robustness of Proof Autoformalization** (2606.14867, 2026-06) — 전역(패러프레이즈)·국소(값·기호·증명 단계 변경) 교란 아래 증명 형식화의 견고성을 처음 측정. 최신 7개 모델 모두 전역 교란에 민감하고 국소 교란을 반영하지 못하는 경우가 많다.
- **Characterizing Paraphrase-Induced Failures** (2604.23135, 2026-04) — 결정론적 패러프레이즈 규칙을 적용해 의미가 같은 입력이 서로 다른 형식화를 유도하는 구조를 분석. 민감성의 주원인이 코드 생성 계층임을 보이고 실패 유형 분류(taxonomy)를 제시했다.

### 6.2 검색·피드백 결합 파이프라인과 데이터

- **MathForm** (2608.14221, 2026-08) — 생성 전 Mathlib 검색 계획, 생성 후 컴파일 진단 + 의미 일관성 피드백의 반복 수정으로 검증된 학습 데이터를 구축하는 프레임워크. FormalVerse(약 367K 검증 예시)로 8B 모델을 학습해 6개 벤치마크 평균 Pass@8 구문 88.06%·의미 72.37%로 32B 전용 모델들을 넘었다.
- **DSR** (2604.19000, 2026-04) — 문장을 논리 성분으로 분해해 연산자 트리로 구조화하고, 오류를 하위 트리 단위로 국소화·수정하는 신경-기호 파이프라인. 학부·대학원 수준 156문제의 PRIME 벤치마크를 함께 공개했다.

### 6.3 연구 수준 장기 형식화 에이전트

- **Theo · Beyond the Library** (2606.31134, 2026-06) — 범용 코딩 LLM 기반 멀티에이전트로 연구 논문을 형식화. Mathlib 밖 개념은 타입 정의를 동적으로 확장하고 보조 정리로 검증한 뒤 본 정리를 형식화한다. STOC 논문 5편·OpenAI 원고 2편의 주 정리를 형식화해 전문가 검증을 받았고 2편은 커널 외 axiom 없이 완성됐다.
- **LeanMarathon** (2606.05400, 2026-06) — 형식 증명 뼈대이자 자연어 증명 그래프인 진화형 blueprint를 공유 기록으로 쓰는 4에이전트 하니스. Erdős 문제 4건을 다룬 논문 2편에서 표적 정리 7개를 sorry 없이 완증(정리·보조정리 258개).
- **Pistis** (2608.15432, 2026-08) — 자연어 증명의 논증 구조를 따르는 '충실한 증명'의 필요조건 5개를 정의하고 OrderDecompose 탐색으로 『원론』 1~3권을 형식화. 반증 탐색으로 원문 증명의 간극까지 발견해, 형식화를 증명 검토 도구로 쓰는 방향을 보였다.

### 추가 시사점

- SA-Pass·BPF류의 보조 명제 기반 전방/후방 검사는 5장 1번 불릿(statement 정합성 체크 단계)의 구체적 구현 후보다.
- Beyond Compilation의 결과는 컴파일 성공률만 보고하면 충실성을 과대평가한다는 뜻이다. 실험 기록에서 컴파일률과 의미 판정을 분리 보고하는 원칙(5장 2번)을 유지한다.
- Theo·LeanMarathon·Pistis는 W12 research use case(논문의 핵심 정리·증명 검토)의 직접적 선행 사례다. blueprint 중심 진행 관리와 반증 탐색 아이디어를 설계 참고자료로 남긴다.

이 10편은 papers.md 등록 후보다. 남성우님과 합의해 목록에 추가할지 정한다.

## 7. 참고 링크

논문 (papers.md 번호와 동일):

- 03 Process-Driven Autoformalization in Lean 4 — <https://arxiv.org/abs/2406.01940v2> · 코드 <https://github.com/rookie-joe/PDA>
- 04 An Evaluation Benchmark for Autoformalization in Lean4 — <https://arxiv.org/abs/2406.06555>
- 05 TheoremLlama — <https://arxiv.org/abs/2407.03203v2>
- 08 Herald — <https://arxiv.org/abs/2410.10878v2>
- 19 ProofBridge — <https://arxiv.org/abs/2510.15681>
- 22 miniF2F-Lean Revisited — <https://arxiv.org/abs/2511.03108> · miniF2F-v2 데이터 <https://github.com/roozbeh-yz/miniF2F_v2>
- 23 NL2Lean — <https://aclanthology.org/2025.emnlp-main.1586v2.pdf>
- 33 LLM-Generated Conjectures to Lean (SOS) — <https://arxiv.org/abs/2605.15445>

추가 조사 (6장, papers.md 목록 외 · 전부 2026-10-10 abstract 확인):

- Beyond Compilation — <https://arxiv.org/abs/2606.31002>
- SHADOWBENCH (SA-Pass) — <https://arxiv.org/abs/2608.29270>
- The Faithfulness Gap (BPF·DriftBench) — <https://arxiv.org/abs/2606.16541>
- Evaluating the Robustness of Proof Autoformalization — <https://arxiv.org/abs/2606.14867>
- Characterizing Paraphrase-Induced Failures — <https://arxiv.org/abs/2604.23135>
- MathForm — <https://arxiv.org/abs/2608.14221>
- DSR (Decompose, Structure, and Repair) — <https://arxiv.org/abs/2604.19000>
- Theo (Beyond the Library) — <https://arxiv.org/abs/2606.31134>
- LeanMarathon — <https://arxiv.org/abs/2606.05400>
- Pistis (Faithful Formalization of Elements Proofs) — <https://arxiv.org/abs/2608.15432>

프로젝트 내 문서:

- [전체 논문 목록](../papers.md) · [연구 자료 안내](../README.md) · [Autoformalization 폴더 README](README.md) · [Week 2 안내](../../meetings/2026-10-11-week2/README.md)

비고: 이 폴더는 박선영·남성우 공동 담당이며, 조사 흐름 요약(3장)은 남성우 담당 논문과 비교해 보면 좋다. 05·33번 abstract와 miniF2F 원판의 문항 수 등 미확인 세부는 추후 원문 확인이 필요하다.
