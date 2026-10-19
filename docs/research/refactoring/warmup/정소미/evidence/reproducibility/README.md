# 4·9번 반복 실행 자료

2026-10-18 · 정소미 · Week 3 실행관리·평가·재현

2주차 참조 증명과 최종 증명을 그대로 사용한다. 실행 조건은 [protocol.json](protocol.json)에 고정했다. 4번은 지정 환경 하나, 9번은 지정 환경 세 개에서 참조·최종 증명을 각각 3번 실행한다. 총 24회이며, 매회 전체 파일 컴파일과 heartbeat 계측용 컴파일을 별도로 수행한다.

- [공유 보고서](../../reproducibility.md)
- [실행 도구](run_replay.py)
- [대회 입력 대조 기록](benchmark_source.json): 4·9번의 원본 선언·명제가 대회 데이터와 같은지 확인한 기록
- [결과 표](results/summary.csv), [실행별 결과](results/results.json), [환경 기록](results/environment.json)
- [실패 처리 확인](results/controls.json), [Lean 출력](results/logs/)

CSV 출력 형식을 정리하기 전에도 같은 24회를 한 번 실행했다. 공유 결과는 수정 후 전체 조건을 다시 실행한 마지막 24회이며, 예비 실행을 반복 횟수에 합산하지 않았다.

## 필요한 환경

Python 3.9 이상, Git, elan/Lake와 아래 네 checkout이 필요하다. Python 외부 패키지는 쓰지 않는다. 입력 증명과 기존 검증기는 이 폴더의 상위 `evidence/`에서 읽는다.

| 환경 ID | 저장소 | 고정 커밋 | Lean | 빌드할 모듈 |
| --- | --- | --- | --- | --- |
| `p4-4.32` | [PhysLib](https://github.com/leanprover-community/physlib) | `c48433678e8fb6306ebcd48453300c8e16058a62` | `v4.32.0` | `Physlib.Mathematics.VariationalCalculus.Basic` |
| `p9-4.31` | [CSLib](https://github.com/leanprover/cslib) | `8ea71c8df91acd63285515a04da952b23b78d266` | `v4.31.0` | `Cslib.Languages.CCS.BehaviouralTheory` |
| `p9-4.32` | CSLib | `197a7be621263b84c67ca4f803f69205b36d06df` | `v4.32.0` | `Cslib.Languages.CCS.BehaviouralTheory` |
| `p9-4.33rc2` | CSLib | `3aa9d4416c185e0b9faeb72bbd65abe85b95dbcc` | `v4.33.0-rc2` | `Cslib.Languages.CCS.BehaviouralTheory` |

환경마다 저장소를 별도 디렉터리에 복제하고 위 커밋을 checkout한다. 각 checkout에서 의존성 캐시를 받고 해당 모듈을 빌드한다.

```sh
git checkout <위 표의 커밋>
lake exe cache get
lake build <위 표의 모듈>
```

`lean-toolchain`과 `lake-manifest.json`은 해당 커밋에 있는 파일을 사용한다. 이번 측정에서는 이미 의존성 캐시가 준비된 로컬 환경을 사용했다. 빈 컴퓨터에서의 설치 시간·설치 성공률은 측정하지 않았다.

## 실행

[repos.example.json](repos.example.json)을 복사해서 각 checkout의 절대 경로를 적는다. 아래 명령은 LeanAgent 저장소 루트에서 실행한다. 출력 폴더는 없거나 비어 있어야 한다.

```sh
python3 docs/research/refactoring/warmup/정소미/evidence/reproducibility/run_replay.py \
  --repos /path/to/repos.json \
  --output /tmp/leanagent-replay-new
```

실행 도구는 다음을 확인한다.

1. 프로젝트 커밋, 추적 파일의 변경 여부, Lean toolchain, 원본 파일·의존성 목록의 해시.
2. 의존성 저장소의 실제 커밋과 변경 여부, 입력 증명·명제의 해시, 참조 증명의 길이.
3. 명제 문자열 보존, 금지 패턴 부재, 전체 문맥 컴파일, 참조와 같은 공리 목록, heartbeat 계측 성공.

반복마다 참조 증명을 먼저, 최종 증명을 다음에 실행한다. 원본 checkout에 증명을 덮어쓰지 않고 임시 사본을 컴파일한다. 판정과 원시 출력은 `results.json`과 `logs/`에 남기고, 완료된 실행마다 `results.json`을 저장한다. 중단된 실행을 이어서 돌리는 기능은 없다. 다시 실행할 때 새 출력 폴더를 지정한다.

`check.seconds`는 `lake env lean` 프로세스의 전체 경과 시간이다. import와 프로세스 시작 비용을 포함하며, 논문의 import 제외 컴파일 시간과 다르다. proof length와 heartbeat는 서로 다른 열로 기록한다.

## 결과 표만 다시 만들기

Lean을 실행하지 않고 저장된 JSON으로 CSV와 요약 JSON을 다시 만든다.

```sh
python3 docs/research/refactoring/warmup/정소미/evidence/reproducibility/run_replay.py \
  --summarize docs/research/refactoring/warmup/정소미/evidence/reproducibility/results
```

`summary.csv`의 `stable`은 세 번 모두 검사를 통과했고 proof length와 heartbeat가 각각 같았다는 뜻이다. 일반적인 에이전트 성공률이나 통계적 유의성을 뜻하지 않는다.

## 실패 처리 확인

정상 증명 24회와 별도로 네 가지 입력을 확인한다. 수정된 명제와 `sorry`를 넣은 증명은 Lean 실행 전에 거부한다. 존재하지 않는 이름을 사용한 증명은 실제 Lean 오류를 남긴다. `v4.32.0` 조건에 `v4.31.0` checkout을 넣으면 커밋 불일치로 실행을 막는다. 이 입력들은 실행 도구 확인용이며, 리팩터링 후보나 성능 비교 대상에 포함하지 않는다.

이번 실행에서는 PhysLib의 의존성 이름 `«doc-gen4»`가 디렉터리 이름 `doc-gen4`와 달라 환경 검사에서 한 번 멈췄다. 이름의 인용 부호를 처리한 뒤 전체 조건을 새 출력 폴더에서 실행했다. 시간 초과와 중간 중단 복구는 이번 확인 범위에 포함하지 않았다.
