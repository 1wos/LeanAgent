# 측정 산출물

박선영 Warm-up 8·11의 측정 JSON·원시 로그는 `docs/`와 분리해 이 루트 폴더에 보관합니다. 기존 다른 발표자의 측정 자료는 이동하지 않습니다. 배치 규칙은 [docs/STRUCTURE.md](../docs/STRUCTURE.md)에 있습니다.

## Warm-up 8·11

- [발표자 안내](../docs/research/refactoring/warmup/박선영/README.md) · [상세 보고서](../docs/research/refactoring/warmup/박선영/report.md).
- [집계 JSON](warmup/박선영/metrics.json): 선택 후보와 버전별 원본/후보 비교, 초안 정적 토큰, 모든 실행 이력. 현재 두 선택 후보 모두 v4.31.0에서 검증·측정했습니다.
- [환경·권한·검증기 수정 이력](warmup/박선영/environment-status.json): 과거 실행 차단과 승인 후 해소, 공리 없는 출력을 오판했던 검증기 수정·성공 재실행을 기록합니다. 최초 8번 후보 실행은 Lean 종료 코드 0이지만 당시 검증기 판정이 failed였으며 원시 기록은 유지합니다.
- [브라우저 검증](warmup/박선영/document-checks.json) · [저장소·문서 검증](warmup/박선영/repository-checks.json) · [Python 테스트 출력](warmup/박선영/unit-tests.log).
- `warmup/박선영/P8/runs/<실행ID>/`, `P11/runs/<실행ID>/`: 실행별 `result.json`, `check.log`, 유효한 증명의 별도 `heartbeat.log`.
- 원본·초안·benchmark·재현 코드·테스트는 [개인 evidence 폴더](../docs/research/refactoring/warmup/박선영/evidence/)에 있습니다. 측정 산출물만 이곳에 둡니다.

실행별 `candidate` 필드는 검사 입력 파일을 뜻하므로 원본 기준선 실행도 `reference.lean`을 가리킵니다. `label=reference`와 해시로 원본 기준선을 구분합니다. 초안 토큰은 정적 계산이며 컴파일 통과를 의미하지 않습니다. 미검증 후보의 개선율과 누락된 heartbeat/API 비용은 `null`입니다. 공식 서버 점수가 아니며, heartbeat는 같은 버전끼리만 비교합니다.

## Skill 실험 세션

`/lean-refactor`의 측정·상태·정책 snapshot·회고는 `warmup/박선영/agent/<session-id>/`에 격리합니다. 증명·가설·분석은 개인 `evidence/agent/<session-id>/`에 둡니다. 이 세션은 기존 `P8/runs`, `P11/runs` 집계나 선택 증명·발표 HTML을 자동 갱신하지 않습니다. skill·세션 helper는 로컬 전용이며 추후 별도 공개 예정입니다. 이번 공유는 저장된 실험 근거와 [개별 후보 검증기](../docs/research/refactoring/warmup/박선영/evidence/run_experiments.py)를 포함하며, 세션 전체 자동 재실행 도구는 포함하지 않습니다. [MVP 검증 기록](warmup/박선영/agent-validation.json)은 단위 테스트 통과와 외부 Lean smoke 실행 차단을 구분합니다.

## 집계·HTML 재생성

저장소 루트에서 실행합니다. 다음 명령은 Lean·외부 checkout을 실행하지 않습니다.

```sh
python3 -I -m unittest discover -s docs/research/refactoring/warmup/박선영/evidence/tests -v
python3 -I docs/research/refactoring/warmup/박선영/evidence/run_experiments.py summarize --update-html
```

HTML은 집계 함수가 생성한 표를 포함하므로 로컬 파일로 열 수 있습니다. 숫자를 여러 문서에서 따로 고치지 말고, 새 실험 후 집계·표를 재생성하고 보고서의 설명을 맞춥니다. Lean 재실행은 외부 코드 실행 권한과 지정된 고정 커밋의 준비된 환경이 필요하며 [보고서의 명령](../docs/research/refactoring/warmup/박선영/report.md#재현-명령)을 따릅니다. 추가 다운로드·API 호출·후보 선택은 집계 명령이 수행하지 않습니다.
