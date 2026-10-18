# 4·9번 반복 실행과 평가 기록

정소미 · 2026-10-18 · Week 3 실행관리·평가·재현

지난주에는 4·9번 증명을 줄이는 과정을 기록했다. 이번에는 그 증명을 다시 비교할 때 필요한 실행 조건과 결과 기록을 정리했다. 같은 증명을 여러 번 돌려도 수치가 같은지, 버전을 바꾸면 무엇이 달라지는지 확인하고, 이 과정을 한 번에 실행하는 도구를 만들었다.

대상은 **4·9번 두 문제**다. 참조 증명과 지난주 최종 증명을 네 지정 환경에서 각각 3번 실행했다. 정상 입력의 최종 실행 24회가 모두 검사를 통과했고, 같은 조건의 증명 길이와 heartbeat는 세 번 내내 같았다. 1–15번 전체 Lean 실험은 수행하지 않았다.

4·9번은 명제·참조·최종 증명과 실행 환경이 이미 준비되어 있어, 실행 도구를 먼저 확인할 대상으로 골랐다. 이번 결과는 팀 전체 평가로 넓히기 전의 소규모 확인이다. 보고서는 3주차 안내가 참조한 [2주차 후속 실험 정리 제안](../../../../meetings/2026-10-11-week2/README.md#후속-실험-정리-제안)의 네 항목에 맞췄다.

## 1. 환경과 기준

증명은 [4번 참조](evidence/P4/reference.lean)·[최종](evidence/P4/final.lean), [9번 참조](evidence/P9/reference.lean)·[최종](evidence/P9/final.lean)을 그대로 사용했다. 참조 선언과 명제는 [대회 데이터의 고정 revision](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/blob/8fdaaaa25b993ae8d894e9bb756c3ae222b58507/benchmark_data_warmup.jsonl)과 다시 대조했다. 참조 proof length도 4번 851, 9번 251로 대회 기록과 일치했다.

| 문제 | Lean | 프로젝트 커밋 | 비교 조건 |
| --- | --- | --- | --- |
| 4 | `v4.32.0` | PhysLib `c484336` | 참조·최종 각 3회 |
| 9 | `v4.31.0` | CSLib `8ea71c8` | 참조·최종 각 3회 |
| 9 | `v4.32.0` | CSLib `197a7be` | 참조·최종 각 3회 |
| 9 | `v4.33.0-rc2` | CSLib `3aa9d44` | 참조·최종 각 3회 |

실행 전에 프로젝트와 의존성의 실제 커밋, 추적 파일의 변경 여부, toolchain, 원본 파일·후보·명제의 해시를 확인했다. 전체 커밋과 옵션은 [실행 조건](evidence/reproducibility/protocol.json), 실제 환경 확인 결과는 [환경 기록](evidence/reproducibility/results/environment.json)에 있다. macOS arm64, Python 3.14.8에서 이미 준비된 의존성 캐시를 사용했다.

이번 재실행에 사용한 LLM은 없다. 입력 증명은 2주차에 공개한 고정 파일이며, 새 후보 생성·검색·수리를 요청하지 않았다. 검증에는 표의 Lean 버전을 사용했다.

### 논문에서 가져온 방법과 적용 범위

현재 적용한 것은 두 논문의 평가·기록 방법이다. 논문별 연결은 아래와 같다. proof length는 구문 단위로 센 증명 길이이고, heartbeat는 Lean이 증명 처리에 쓴 작업량이다.

| 논문·위치 | 참고한 방법 | 이번 구현·실행 | 확인한 결과와 적용 범위 |
| --- | --- | --- | --- |
| [Lean Refactor](https://www.alphaxiv.org/pdf/2605.20244), §4.2·부록 J·L. 공통 [논문 목록](../../../papers.md)의 34번 | 길이와 컴파일 비용을 각각 측정한다. 연구용 프로젝트의 선언에는 `Elab.async false`와 `#count_heartbeats`를 적용한다. | 2주차의 길이 계산기와 heartbeat 검증기를 재사용하고, 네 환경의 참조·최종 증명을 각 3회 실행했다. | 8개 조건 모두 길이와 heartbeat가 반복마다 같았다. 지표와 계측 방법을 적용했으며, 논문의 전략 검색·재정렬 효과는 실험하지 않았다. |
| Lean Refactor, §4.3 | 같은 증명을 여러 toolchain에서 수정 없이 다시 컴파일해 호환성을 확인한다. | 9번의 고정된 증명 두 개를 지정된 Lean·CSLib 환경 세 개에서 검사했다. | 모두 통과했다. 최종 heartbeat 516·516·510은 지난주 결과의 재확인이다. 논문의 데이터셋·버전과 다르며, 버전 정보를 이용한 전략 필터링은 구현하지 않았다. |
| Arvan·Pina·Parde, [Reproducibility in Computational Linguistics: Is Source Code Enough?](https://aclanthology.org/2022.emnlp-main.150.pdf#page=2), EMNLP 2022, §3 | 소스 코드와 함께 입력·실행 환경·원시 결과·실험 및 표 생성 스크립트를 제공한다. | [실행 조건](evidence/reproducibility/protocol.json), [환경 기록](evidence/reproducibility/results/environment.json), [실행·집계 도구](evidence/reproducibility/run_replay.py), 로그와 재실행 안내를 함께 두었다. | 저장된 결과에서 표를 다시 생성해 일치함을 확인했다. 사전 준비한 로컬 환경에서만 실행했으며, 논문이 설명하는 독립 실행 패키지·컨테이너나 다른 사람의 재현 검증까지 갖춘 것은 아니다. |

3회 반복, 파일 해시 대조, 환경 불일치 차단, 실패 입력 4종은 이번 실행 도구를 확인하기 위해 정한 구현·검사 방법이다. 두 논문이 그대로 제시한 실험 설정이나 알고리즘으로 소개하지 않는다. Lean Refactor의 경시 수학 실험은 import를 제외한 컴파일 시간을 5회 측정한다. 이번의 3회 반복과 전체 프로세스 시간은 그 설정을 재현한 것이 아니다.

논문별 방법의 성능을 비교하거나, 이 기록 방식을 쓰기 전후의 재현 성공률을 비교한 실험은 아직 없다. 현재 근거는 위 방법을 적용한 실행·기록 절차가 4·9번에서 작동한다는 확인이다. Lean Refactor의 에이전트 구조와 2주차 적용 기록은 [별도 논문 문서](../../../verifier-guided-agent/정소미/report.md)에 있다.

## 2. 비교 조건

바꾼 조건은 참조·최종 증명과 9번의 지정 환경이다. 각 환경 안에서는 입력 파일, 전체 문맥, 검증기, 옵션을 고정했다. 한 조건을 세 번 반복했고, 새로운 모델이나 프롬프트의 효과를 비교하지 않았다.

각 반복에서는 참조 증명을 먼저, 최종 증명을 다음에 실행했다. 원본 파일의 해당 선언을 교체한 임시 사본을 만들고 뒤따르는 선언까지 컴파일했다. heartbeat는 `Elab.async false`와 `#count_heartbeats`를 적용한 별도 사본에서 측정했다. 명제가 그대로이고, 금지 패턴이 없고, 컴파일·공리·heartbeat 검사가 모두 통과한 실행만 유효한 결과로 집계했다. 공리 목록은 모든 정상 실행에서 `[propext, Classical.choice, Quot.sound]`였다.

## 3. 결과와 비용

표의 길이와 heartbeat는 각 조건에서 3회 모두 같았다. 마지막 열은 참조 3회와 최종 3회의 검증 통과 횟수다.

| 문제·Lean | proof length 참조 → 최종 | heartbeat 참조 → 최종 | 검증 통과 |
| --- | ---: | ---: | ---: |
| 4 · `v4.32.0` | 851 → 123 | 11,947 → 1,411 | 6/6 |
| 9 · `v4.31.0` | 251 → 79 | 3,859 → 516 | 6/6 |
| 9 · `v4.32.0` | 251 → 79 | 3,856 → 516 | 6/6 |
| 9 · `v4.33.0-rc2` | 251 → 79 | 3,858 → 510 | 6/6 |

[조건별 CSV](evidence/reproducibility/results/summary.csv) · [24회 개별 결과](evidence/reproducibility/results/results.json) · [Lean 출력](evidence/reproducibility/results/logs/)

이 증명 길이 감소와 아래의 버전별 heartbeat 차이는 [지난주 보고서](report.md#5-참조-증명-대비-현재-후보)에 이미 기록한 결과다. 이번에 추가한 것은 환경·입력 확인, 반복 실행, 실패 분류와 결과 집계를 묶은 실행 도구와 새로 실행한 24회의 기록이다. 같은 컴퓨터·같은 조건에서 반복성이 유지되는 것을 확인했다.

전체 실행 시간은 달랐다. 예를 들어 4번 최종 증명의 컴파일 프로세스는 3.90–7.13초가 걸렸지만 heartbeat는 매번 1,411이었다. 이 시간에는 프로세스 시작과 import 비용이 포함된다. 논문에서 측정한 import 제외 컴파일 시간과 정의가 달라, 여기서는 실행 상황을 기록하는 용도로만 남겼다.

9번은 같은 증명 파일인데도 버전에 따라 최종 heartbeat가 516에서 510으로 달라졌다. 참조 증명의 값도 함께 달라졌다. 결과를 비교할 때는 같은 환경의 참조값을 함께 보아야 한다. 이번에는 Lean·CSLib·의존성이 함께 바뀌므로, 차이의 원인을 Lean 버전 하나로 좁힐 수는 없다.

### 실행량과 비용

| 항목 | 이번 최종 실행의 기록 |
| --- | --- |
| 새 후보 생성·검색·수리를 위한 LLM 호출 | 0회 |
| 재실행 프로그램의 LLM API 비용 | US$0 |
| 정상 입력의 Lean 컴파일 | 48회: 전체 문맥 검사 24회 + heartbeat 계측 24회 |
| 실패 확인용 Lean 컴파일 | 1회. 나머지 세 입력은 실행 전에 차단 |
| 전체 회차 경과 시간 | 278.36초. 환경 확인·정상 실행·실패 확인을 포함 |
| 기존 증명을 만드는 데 든 비용 | [2주차 기록](report.md)에 따르면 문제별 API 비용을 집계하지 않음 |

US$0는 고정된 증명을 다시 검사하는 프로그램의 추가 LLM API 비용이다. 기존 증명 생성과 이번 도구·문서 작성에 든 전체 비용을 뜻하지 않는다. 따라서 이 결과만으로 전체 리팩터링 과정의 문제당 US$3 예산 충족을 판단할 수는 없다.

## 4. 실패 원인

실행 도구가 실패를 성공으로 집계하지 않는지 확인하려고 정상 실행과 별도로 네 입력을 넣었다.

| 넣은 입력 | 실제 결과 | Lean 실행 |
| --- | --- | --- |
| 9번 명제의 `choice q r`를 `choice p r`로 변경 | 명제 불일치로 거부 | 실행 전 차단 |
| 증명을 `by sorry`로 교체 | 금지 패턴으로 거부 | 실행 전 차단 |
| 존재하지 않는 이름 `noSuchLemmaForReplayControl` 사용 | `Unknown identifier` 오류를 저장하고 성공 집계에서 제외 | 실행함 |
| `v4.32.0` 조건에 `v4.31.0` checkout 전달 | 프로젝트 커밋 불일치로 거부 | 실행 전 차단 |

[실패 확인 결과](evidence/reproducibility/results/controls.json)와 컴파일 오류의 [원시 출력](evidence/reproducibility/results/logs/control-compiler-error.log)을 남겼다. 이 네 건은 도구 확인용으로 만든 입력이다. 에이전트가 생성한 실패 사례나 실패율로 해석하지 않는다.

환경 검사 구현 중에는 PhysLib 의존성 이름 `«doc-gen4»`와 실제 디렉터리 `doc-gen4`의 표기가 달라 한 번 멈췄다. 이름의 인용 부호를 처리한 뒤 새 출력 폴더에서 전체 실험을 시작했다. 실행 도구를 만들 때는 이런 환경 준비 단계의 실패도 증명 실패와 구분해야 했다.

## 다시 실행하려면

[환경 준비와 실행 안내](evidence/reproducibility/README.md)에 네 checkout의 커밋과 준비 명령을 적었다. checkout 경로를 `repos.json`에 채운 뒤 저장소 루트에서 실행한다.

```sh
python3 docs/research/refactoring/warmup/정소미/evidence/reproducibility/run_replay.py \
  --repos /path/to/repos.json \
  --output /tmp/leanagent-replay-new
```

Lean 실행 없이 저장된 결과로 표만 다시 만들 수도 있다.

```sh
python3 docs/research/refactoring/warmup/정소미/evidence/reproducibility/run_replay.py \
  --summarize docs/research/refactoring/warmup/정소미/evidence/reproducibility/results
```

## 이번 결과의 범위와 다음 논의

이번에는 두 문제의 이미 알려진 증명을 같은 컴퓨터에서 반복했다. 24회는 두 문제의 여러 조건을 반복한 횟수이며, 서로 다른 24개 문제에서 성능을 검증한 결과가 아니다. 실행·기록 절차를 확인한 소규모 실험으로 해석한다. 새 후보를 생성하거나 에이전트의 탐색 성능을 비교하지 않았고, 공식 Arena 제출도 하지 않았다. 다른 컴퓨터에서의 재현, 빈 환경부터의 설치, 시간 초과 처리와 중단 후 복구는 아직 확인하지 않았다.

모임에서는 다른 담당자의 결과에도 **문제·후보 해시·환경·검증 판정·길이·heartbeat·원시 로그 위치**를 함께 남기는 형식을 제안하고 싶다. 이 기록이 있으면 같은 조건의 결과를 모아 비교하고, 실패한 실행을 다시 확인하기가 쉬워진다. 1–15번으로 넓히려면 나머지 문제의 지정 환경과 검증 조건을 추가하고 실제로 실행해야 한다. 현재 실행 도구와 결과는 4·9번에 맞춰져 있다.
