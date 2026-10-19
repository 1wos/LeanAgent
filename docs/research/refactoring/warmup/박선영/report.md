# Warm-up 8·11 원본 실측과 리팩터링 후보

**Week 2 기본 실험 · Week 3 agent 실험 안내.** [발표자료](presentation.html)에서 사용한 원본·후보 실행 결과와 후속 agent 실험의 읽는 순서를 정리합니다. Week 2 원본은 2026-10-15, 후보는 2026-10-16에 측정했고, Week 3 agent 실험은 2026-10-17에 수행했습니다. 아래 Week 2 본문과 기존 발표·선택 후보는 그대로 유지합니다.

## Week 3 — agent 실험 결과 읽는 법

### 먼저 볼 자료

**최신 결과는 [P11 구조 변경 A/C 분리 확인 보고서](evidence/agent/p11-20261017-ac-check4/report.md)를 참고합니다.** 이 대표 문서의 아래 수치 표는 Week 2 결과이며, 최신 agent 결과로 자동 갱신한 표가 아닙니다.

| 순서 | 자료 | 읽을 내용 |
| --- | --- | --- |
| 1 | [확인 실험 보고서](evidence/agent/p11-20261017-ac-check4/report.md) | 중간 `calc`의 두 `ring` 단계 통합(C)이 마지막 계수 계산 재구성(A) 없이도 효과가 있는지, 네 조건을 분리한 결과 |
| 2 | [확인 실험 README](evidence/agent/p11-20261017-ac-check4/README.md) | 조건별 후보·가설·diff와 evidence/metrics의 원시 결과·로그·회고를 찾는 목차 |
| 3 | [이전 순차 탐색 보고서](evidence/agent/p11-20261017-adaptive3/report.md) | B→B+A→B+A+C로 다음 전략을 선택한 과정과 후속 확인 실험이 필요했던 이유 |

### 결과를 해석하는 기준

- **B**는 Week 2의 미사용 계수 정의 제거 후보, **A**는 마지막 계수 계산 재구성, **C**는 중간 `calc`의 연속 두 `ring` 단계 통합입니다.
- 이전 순차 탐색에는 B+C 조건이 없었습니다. Week 3 확인 실험은 새 원본 baseline과 B·B+A·B+C·B+A+C를 측정하고, 뒤의 세 후보 모두 **B를 비교 부모로 고정**해 C의 효과를 분리했습니다.
- 확인 결과, **이 P11/v4.31.0 환경에서 C는 A 없이도 786 heartbeat를 줄였습니다.** A가 있을 때의 추가 감소량도 786으로 같았습니다. 감소율은 각 비교의 출발 값이 달라 각각 1.8878%, 2.0090%입니다. 측정 사실과 원인 추정·일반화 한계는 최신 보고서에서 구분합니다.
- **후보 번호는 세션 안에서만 유효합니다.** 이전 `adaptive3`의 a003은 B+A+C이고, 최신 `ac-check4`의 a003은 B+C, a004가 B+A+C입니다. 세션 이름과 조건을 함께 확인합니다.
- **검증 통과, 부모 대비 개선, 세션 best 갱신은 서로 다릅니다.** 최신 B+C는 검증에 통과하고 B보다 개선됐지만, 당시 best인 B+A보다 비용이 높아 원장에는 `improved=false`로 기록됩니다. 이를 증명 실패나 C의 효과 없음으로 읽으면 안 됩니다.
- **기존 결과의 재현을 새 최적화 발견으로 세지 않습니다.** 최신 네 조건 중 B·B+A·B+A+C는 기존 후보 재현이고, B+C는 사전 지정한 효과 분리 확인 조건입니다.
- 이전 탐색은 마지막 평가 후 skill 파일 변경 감지로 a003의 review 저장이 중단됐습니다. 최신 확인 실험은 **네 후보 평가·review·회고까지 모두 완료**했습니다. 이전 기록은 수정하지 않고 보존했습니다.
- 세션의 **best는 최종 채택이 아닙니다.** 최신 best는 a004(B+A+C)이지만 기존 `selected.lean`, 발표 HTML 및 Week 2 집계는 변경하지 않았습니다. 다른 정리·다른 버전·공식 서버 성능으로 일반화하지 않습니다.

원시 수치는 보고서가 연결하는 `evidence/metrics/agent/<session>/`의 `session.json`, `result.json`, `check.log`, `heartbeat.log`에서 확인합니다. 증명·가설·diff는 각 `evidence/agent/<session>/`에 있고, 측정 파일을 대표 문서나 증명 세션 폴더에 복제하지 않습니다.

경로 정리로 원시 JSON·로그·snapshot의 내용은 바꾸지 않았습니다. 내부의 과거 출력 경로, 저장 해시 및 코드·환경 fingerprint는 원래 실행 당시의 기록이며 현재 트리 전체의 동일성을 보장하지 않습니다. 이 보고서의 기존 검증·불변성 주장은 해당 측정 시점의 사실입니다. 기존 세션을 자동 재개하거나 원장을 수정해 무결성 검사를 우회하지 않으며, 후속 실행은 별도 승인·현재 환경 확인 후 새 세션에서 수행합니다. 로컬 skill·helper는 이번 공유에서 제외하고 경로 정리에서도 변경하지 않습니다.

## Week 2 — 결론과 검증 범위

원본과 두 후보 모두 기존에 준비된 **Lean v4.31.0 고정 커밋 환경에서 컴파일·공리 검사·별도 heartbeat 측정까지 통과**했습니다. benchmark의 전체 명제는 그대로 유지했고 금지 패턴 검사도 통과했습니다. 검증된 두 후보를 각 문제의 `selected.lean`으로 보존했습니다.

처음에는 외부 코드 실행 권한 계층에서 차단됐지만 사용자 승인 후 실행했습니다. 8번 첫 실행은 Lean 종료 코드 0이었으나 공리 없는 출력에 대한 검증기 판정 버그로 실패 기록이 남았습니다. 파서를 수정하고 새 실행으로 통과·측정까지 확인했습니다. 과거 차단·오판 기록은 삭제하지 않았습니다.

| 문제 | 원본 → 후보 토큰 | 토큰 변화 | 원본 → 후보 heartbeat | heartbeat 변화 | 후보 검증 |
| --- | ---: | --- | ---: | --- | --- |
| 8 | 407 → 412 | 1.23% 증가 | 1,382 → 1,320 | 4.49% 감소 | v4.31.0 통과 |
| 11 | 1,906 → 1,656 | 13.12% 감소 | 45,537 → 41,636 | 8.57% 감소 | v4.31.0 통과 |

- 토큰: 공유 tokenizer로 계산했으며 원본 15개 모두 benchmark의 `proof_length`와 일치했습니다. LLM 토큰 수나 API 비용이 아닙니다.
- 8번 명시적 조립은 토큰이 5개 증가하고 heartbeat가 62 줄었습니다. 두 지표가 모두 좋아진 것은 아니며, 연산량 감소와 공리 제거를 확인한 **절충안**으로 선택했습니다. heartbeat는 실시간 속도나 대회 종합 점수가 아닙니다.
- 11번 후보는 토큰 250개·heartbeat 3,901이 줄었고 같은 환경에서 정확성 검증도 통과해 선택했습니다.
- 후보 지정 버전 검사: **8번 1/4, 11번 1/3; 실제 검사한 후보 버전은 각각 1개**입니다. 나머지 버전은 실패가 아니라 미실행입니다.
- 공식 서버 채점·독립 리뷰·전체 버전 호환성은 확인하지 않았습니다. API 비용은 계측하지 않았으므로 `null`입니다.

## 원본 실행 환경과 근거

| 문제 | 정리 / 원본 파일 | 저장소·고정 커밋 | 버전 |
| --- | --- | --- | --- |
| 8 | `Cslib.SKI.parallelReduction_diamond` / `Cslib/Languages/CombinatoryLogic/Confluence.lean` | [leanprover/cslib](https://github.com/leanprover/cslib) · `8ea71c8df91acd63285515a04da952b23b78d266` | v4.31.0 |
| 11 | `Binius.BinaryBasefold.fold_advances_evaluation_poly` / `ArkLib/ProofSystem/Binius/BinaryBasefold/Prelude.lean` | [Verified-zkEVM/ArkLib](https://github.com/Verified-zkEVM/ArkLib) · `c1712f6c496d0aef04f09bae42aec13811b3273f` | v4.31.0 |

측정 시각은 각 JSON의 UTC `measured_at`에 있습니다. 원본·후보·전체 소스 SHA-256, 실행 명령, 종료 코드, 경과 시간, 공리, heartbeat를 함께 저장합니다.

- 8번: [결과 JSON](evidence/metrics/P8/runs/20261015T053841280710Z-reference/result.json) · [Lean 검증 로그](evidence/metrics/P8/runs/20261015T053841280710Z-reference/check.log) · [heartbeat 로그](evidence/metrics/P8/runs/20261015T053841280710Z-reference/heartbeat.log).
- 11번: [결과 JSON](evidence/metrics/P11/runs/20261015T053854284087Z-reference/result.json) · [Lean 검증 로그](evidence/metrics/P11/runs/20261015T053854284087Z-reference/check.log) · [heartbeat 로그](evidence/metrics/P11/runs/20261015T053854284087Z-reference/heartbeat.log).
- 8번 선택 후보: [결과 JSON](evidence/metrics/P8/runs/20261016T003747320609Z-attempt_01_recheck/result.json) · [Lean 검증 로그](evidence/metrics/P8/runs/20261016T003747320609Z-attempt_01_recheck/check.log) · [heartbeat 로그](evidence/metrics/P8/runs/20261016T003747320609Z-attempt_01_recheck/heartbeat.log).
- 11번 선택 후보: [결과 JSON](evidence/metrics/P11/runs/20261016T003619698812Z-attempt_01/result.json) · [Lean 검증 로그](evidence/metrics/P11/runs/20261016T003619698812Z-attempt_01/check.log) · [heartbeat 로그](evidence/metrics/P11/runs/20261016T003619698812Z-attempt_01/heartbeat.log).
- [전체 집계](evidence/metrics/metrics.json) · [권한 차단 해소·검증기 수정 이력](evidence/metrics/environment-status.json).

원본 두 정리와 11번 후보의 공리는 `Classical.choice`, `Quot.sound`, `propext`입니다. **8번 후보는 공리 의존성이 없습니다**(`axioms: []`). 모든 통과 증명에 `sorryAx`가 없으며 원본 대비 새 공리도 없습니다. 이전 smoke test를 이번 실측으로 재사용한 것이 아닙니다.

지정된 나머지 버전은 다음과 같으며 미준비·미검증 상태입니다. 기존 v4.31.0 환경 실행 허용 범위에 추가 다운로드는 포함되지 않아 설치하지 않았습니다.

- 8번: v4.30.0, v4.32.0, v4.33.0-rc2.
- 11번: v4.29.0, v4.30.0.
- 버전별 고정 커밋 전체는 보존한 [benchmark](evidence/benchmark.jsonl)의 `version_info`를 기준으로 합니다.

## 작성한 후보와 채택 판단

### 8번: 자동 탐색을 명시적 생성자로 대체

[원본](evidence/P8/reference.lean)의 `par/red_S` 분기 한 곳만 바꿨습니다. 작은 축약 증거 `h.1`, `h.2.1`, `hb'`를 직접 조합하려는 가설입니다.

```lean
-- 원본
apply ParallelReduction.par <;>
  apply ParallelReduction.par <;>
  grind

-- attempt_01
exact .par (.par h.1 hb') (.par h.2.1 hb')
```

[시도 원본](evidence/P8/attempts/attempt_01.lean) · [검증된 선택 후보](evidence/P8/selected.lean). 원본의 재귀·다른 경우 분기·명제는 유지했습니다. 길이는 늘었지만 v4.31.0 검증과 heartbeat 감소·공리 제거를 확인해 비교 후보로 채택했습니다. 다른 환경의 속도나 전체 버전 통과를 주장하지 않습니다.

### 11번: 미사용 지역 계수 정의만 제거

[원본](evidence/P11/reference.lean)의 `P₀_coeffs`와 `P₁_coeffs`는 각각 정의 위치에만 한 번 등장합니다. 이 두 `set` 블록과 그 소개 주석만 제거했습니다.

```lean
-- 삭제: 이후 참조되지 않는 지역 정의
set P₀_coeffs := ...
set P₁_coeffs := ...

-- 유지: 뒤의 증명에 실제로 쓰이는 다항식
set P₀ := evenRefinement ...
set P₁ := oddRefinement ...
```

[시도 원본](evidence/P11/attempts/attempt_01.lean) · [검증된 선택 후보](evidence/P11/selected.lean). qMap 평가, fiber 두 점의 차이, 다항식 분해, 마지막 `calc`는 그대로입니다. 삭제가 해당 블록에 한정되는지 회귀 테스트로 대조했고, v4.31.0 컴파일 통과와 두 지표 감소를 확인해 채택했습니다.

가설과 후보 경로는 [candidates.json](evidence/candidates.json)에 있고, 집계 시 파일에서 현재 토큰과 해시를 다시 계산합니다. 이 파일은 채택 선언이나 실행 성공 기록이 아닙니다.

## 검증·측정 방법

1. benchmark snapshot의 15개 원본 토큰 수를 공유 tokenizer로 대조합니다. [출처·해시](evidence/benchmark-provenance.json)는 기존 2026-10-10 획득 snapshot을 복사한 기록이며, 이번에 서버에서 새로 받은 데이터는 아닙니다.
2. 원본과 후보의 전체 statement prefix가 정확히 같고 `:= by`로 이어지는지 확인합니다. 금지 패턴과 추가 top-level 선언을 검사합니다.
3. 외부 checkout의 origin, HEAD, `lean-toolchain`, tracked 변경 유무를 확인합니다. 문제의 지정 커밋이 아니면 중단합니다.
4. benchmark 원본 선언이 upstream 전체 파일에 정확히 한 번 존재하는지 검사한 뒤, 임시 파일에서 그 선언만 교체합니다. 대상 정리의 `.olean`을 import해서 후보 검증을 대신하지 않습니다.
5. `lake env lean <temporary>/Check.lean`으로 전체 문맥을 다시 elaborate하고 `#print axioms`를 확인합니다. 종료 코드·오류 출력과 공리가 허용 집합의 부분집합인지 검사합니다. 공리 없는 출력은 빈 목록으로 처리하고, 호환성 비교 시 원본 대비 새 공리가 없는지 확인합니다. 공리 제거를 실패로 취급하지 않습니다.
6. 별도 임시 파일에 `Mathlib.Util.CountHeartbeats`와 `set_option Elab.async false in` / `#count_heartbeats in`을 넣어 대상 선언만 측정합니다. 앞의 doc comment 및 `omit ... in`을 고려합니다.
7. timeout은 기본 180초입니다. 실패·timeout·파싱 실패는 수치를 `null`로 남깁니다. 비교율은 같은 버전의 원본과 선택 후보가 모두 통과한 경우에만 계산합니다.
8. 실행별 JSON·원시 로그는 개인 `evidence/metrics/`에 저장합니다. `summarize --update-html`은 저장된 실행 결과를 집계하고 HTML marker 사이의 표만 갱신합니다. HTML은 런타임 JSON fetch 없이 파일로 열 수 있습니다.

정적 금지 패턴 검사는 검토된 로컬 증명 후보용 보조 검사이며, 임의의 악성 Lean 코드를 안전하게 실행시키는 sandbox가 아닙니다. 외부 Lean/Lake 코드를 실제로 실행하는 데에는 별도 실행 권한이 필요합니다.

## 재현 명령

저장소 루트에서 실행합니다. Python 집계·테스트는 외부 Lean checkout을 실행하지 않습니다.

```sh
python3 -I -m unittest discover -s docs/research/refactoring/warmup/박선영/evidence/tests -v
python3 -I docs/research/refactoring/warmup/박선영/evidence/run_experiments.py summarize --update-html
```

다음 Lean 검증 명령은 **외부 저장소 실행 권한이 있는 경우에만** 실행합니다. `CSLIB_REPO`, `ARKLIB_REPO`는 이미 의존성이 준비된 해당 고정 커밋 checkout으로 설정합니다. 이 스크립트는 환경 설치 명령이 아니며 기존 checkout 소스·브랜치를 수정하지 않습니다.

```sh
EVIDENCE=docs/research/refactoring/warmup/박선영/evidence
python3 -I "$EVIDENCE/run_experiments.py" verify --problem 8 --repo "$CSLIB_REPO" \
  --candidate "$EVIDENCE/P8/reference.lean" --label reference --hypothesis '원본 기준선'
python3 -I "$EVIDENCE/run_experiments.py" verify --problem 11 --repo "$ARKLIB_REPO" \
  --candidate "$EVIDENCE/P11/reference.lean" --label reference --hypothesis '원본 기준선'
python3 -I "$EVIDENCE/run_experiments.py" verify --problem 8 --repo "$CSLIB_REPO" \
  --candidate "$EVIDENCE/P8/attempts/attempt_01.lean" --label attempt_01 \
  --hypothesis 'grind를 명시적 생성자 증명으로 교체'
python3 -I "$EVIDENCE/run_experiments.py" verify --problem 11 --repo "$ARKLIB_REPO" \
  --candidate "$EVIDENCE/P11/attempts/attempt_01.lean" --label attempt_01 \
  --hypothesis '미사용 지역 계수 정의 제거'
```

후보가 실제로 통과하고 비교 결과를 검토한 뒤에만 그 내용을 문제 폴더의 `selected.lean`으로 보존하고 다시 집계합니다. 현재 두 선택 파일은 각 `attempt_01.lean`과 동일하며, 해시가 같은 최신 실행을 표에 사용합니다. 원시 실행과 과거 실패·검증기 오판 기록은 `runs/`와 집계의 `attempts`에 모두 남습니다.

## 테스트·문서 검증과 남은 작업

실험에 사용한 `/lean-refactor` skill과 세션 helper는 이번 공유에서 제외하며, 추후 정리해 별도로 공개할 예정입니다.

2026-10-18 경로 정리 후 Python 회귀 테스트 29개(기존 25개 + 경로 처리 4개), 문서 검사 124개, 브라우저 검사 209개를 통과했습니다. 새 검사 결과·화면 캡처는 Git에서 제외한 `evidence/metrics/local-checks/`에 생성합니다. 아래 링크의 과거 검사 JSON·로그와 이동한 측정 기록은 덮어쓰지 않았으며, 측정 JSON·로그 58개의 SHA-256이 이동 전과 같음을 확인했습니다. Lean은 추가 실행하지 않았습니다.

- 초기 Python 회귀 테스트 **25개 통과**: 원문 유일 교체, 명제 불변, 금지 패턴, 공리 없는 출력·축소된 공리 집합·중복 출력·`sorryAx`, 종료 코드, timeout bytes 처리, heartbeat 누락/중복/오류, null/감소율, 전체 버전 표시, HTML escaping·링크·marker 갱신, 저장된 해시·공리 및 후보 변경 범위.
- 처음 테스트 실행에서는 임시 발표 경로를 바꾼 테스트의 기대 링크 경로가 잘못되어 1개 실패했습니다. 같은 경로 문맥에서 기대 HTML을 만들도록 테스트를 수정한 뒤 24개 모두 통과했습니다. Lean 후보 실패 기록이 아닙니다.
- 로컬 Chromium에서 이전/다음·방향키·Home/End·전체 보기·print media의 전체 슬라이드 표시, 1280px/400px의 light/dark 및 명시적 light override, 표의 7개 버전 행, 로컬 링크를 확인했습니다. 페이지 가로 넘침과 콘솔 오류는 없었습니다. [브라우저 기록](evidence/metrics/document-checks.json). 화면 캡처는 로컬 생성물로 Git 공유에서 제외합니다. 실제 프린터 출력·다른 브라우저·공식 서버 렌더링은 확인하지 않았습니다.
- 이동 전 상대 링크·앵커·해시·HTML/metrics 일치·Git 점검은 [저장소 검증 기록](evidence/metrics/repository-checks.json), 회귀 테스트 출력은 [unit-tests.log](evidence/metrics/unit-tests.log)에 보관합니다. `python3 -I docs/research/refactoring/warmup/박선영/evidence/tests/check_documents.py`로 이 점검을 재실행할 수 있습니다. 브라우저 점검은 이미 설치된 Playwright/Chromium이 있는 환경에서 `node docs/research/refactoring/warmup/박선영/evidence/tests/check_presentation.cjs`로 실행하며 자동 다운로드하지 않습니다.
- [8번 최초 후보 실행](evidence/metrics/P8/runs/20261016T002536550231Z-attempt_01/result.json)은 Lean 종료 코드 0인데 `status: failed`입니다. 당시 파서가 `does not depend on any axioms`를 인식하지 못하고 전체 허용 공리와의 동등성을 요구했기 때문입니다. 원시 기록을 고치지 않고, 검증기를 수정한 뒤 별도 recheck 실행으로 통과·heartbeat 측정을 확인했습니다.
- 남은 핵심 작업: 나머지 지정 버전 검증과 8번 토큰 증가 완화 실험. 현재 로컬 결과를 공식 대회 점수나 전체 버전 호환성으로 확대해 주장하지 않습니다.
