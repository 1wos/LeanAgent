# LeanAgent Week 2

2026년 10월 11일 일요일 20:00–22:00.

대회 웜업 문제 15개의 연구와 분야별 논문 조사를 진행하고, 담당한 내용을 공유합니다.

## ATP 지식 공유 발표

### 담당자 : 손지연

- [HTML 발표자료](../../research/automated-theorem-proving/lean_atp_presentation.html): ATP 태그 논문 28편을 환경·검색·학습·수리·최적화·평가 관점으로 정리한 본문 18장과 부록 6장입니다.
- HTML 파일을 내려받아 브라우저에서 열면 동작합니다. 슬라이드·발표자 노트가 한 파일에 포함되어 있으며, 원문 링크를 열 때 인터넷 연결이 필요합니다.
- `←`·`→`로 이동하고, `O`로 목차, `N`으로 노트, `P`로 발표자 창, `F`로 전체화면을 엽니다. `T`는 타이머이며, Home / End로 처음 / 마지막 장에 이동합니다.
- 인쇄 기능으로 전체 슬라이드를 출력할 수 있습니다. 3번 데모는 설명용 시각화이며 실제 Lean 실행 결과가 아닙니다.

### 담당자 : 권주원

- [HTML 발표자료](../../research/automated-theorem-proving/atp.html): LeanDojo, Premise Selection for a Lean Hammer, InternLM2.5-StepProver, Lean Refactor의 핵심 방법을 다루는 20장 슬라이드. 약 20분 분량입니다. ATP 연구 폴더에서 계속 수정합니다.
- 파일 하나로 구성해 브라우저에서 바로 열 수 있습니다. 외부 라이브러리·폰트·네트워크 요청 없이 동작하며, 출처 링크를 열 때만 인터넷 연결이 필요합니다.
- 좌우 방향키·하단 버튼으로 이동하고, `T`로 목차, `N`으로 발표자 노트, `F`로 전체화면을 엽니다. Home / End는 처음 / 마지막 장으로 이동합니다.
- PDF / 인쇄 버튼은 모든 슬라이드를 출력합니다. 화면 공유 전 발표자 노트를 닫습니다.
- 증명 상태와 탐색 우선순위의 클릭 예시는 설명용입니다. 브라우저에서 Lean이나 논문의 모델을 실행하지 않습니다.

## 웜업 문제 담당

| 담당자 | 웜업 문제 번호 | 문제 수 |
| --- | --- | --- |
| 권주원 | 3, 6, 13 | 3개 |
| 손지연 | 7, 12 | 2개 |
| 박채원 | 14, 15 | 2개 |
| 박선영 | 8, 11 | 2개 |
| 남성우 | 1, 2 | 2개 |
| 정소미 | 4, 9 | 2개 |
| 박성호 | 5, 10 | 2개 |

총 15문제를 중복 없이 배정했습니다. 웜업 문제 연구 자료와 진행 기록은 이 폴더에 모읍니다.

### 담당 문제 연구 기록

- [손지연 · P7·P12 증명 리팩터링 상세 보고서](refactoring-07-12/proof_refactoring_report.md): 명제의 의미와 Lean 문법, 증명 흐름, 리팩터링 전략, 원본·수정 코드 비교, 실패 원인과 해결 과정 및 검증 결과를 정리합니다.
- [손지연 · P7·P12 HTML 발표자료](refactoring-07-12/proof_refactoring_presentation.html): 개념·수식 해설, P7의 단계별 계산 예제, P12의 차원별 행 분할 데모, 전후 코드와 검증 결과를 브라우저에서 확인합니다. 파일을 내려받아 열 수 있으며, 목차 이동·큰 글씨·인쇄 기능을 제공합니다. 데모는 설명용이며 실제 Lean을 실행하지 않습니다.
- 리팩터링 규모: P7 정리 전체는 **83줄 → 49줄**, `grind` 출현은 **19회 → 8회**입니다. P12 주 정리는 **177줄 → 17줄**이며, 새 보조정리를 포함한 비교 범위 전체는 **76줄**입니다.
- [손지연 · 실행·검증 설명](refactoring-07-12/proof_refactoring_report.md#verification-and-axiom-check): 최종 검증 결과와 공리 확인, P12의 실패·해결 과정을 본문에 요약합니다. 별도 소스·스크립트·로그·JSON은 로컬 작업 자료입니다. 검증 결과는 2026-10-10 완료된 로컬 실행 기록 기준이며, 이번 자료 정리에서는 Lean을 재실행하지 않았습니다. 네 증명 모두 검증을 통과했고 대상 정리의 `sorryAx` 의존성은 없습니다. 단회 파일 검사 시간은 참고치이며 실행 속도 개선으로 일반화하지 않습니다.
- [권주원 · 3·6·13번 HTML 학습 자료](refactoring-03-06-13.html): 문제별 페이지에서 변수 확인, 작은 예시, Lean 코드와 리팩터링 전략을 공부하고, 마지막 페이지에서 대회 지표와 세 문제의 공통 인사이트를 확인합니다.

## 논문 분야 담당

| 분야 | 담당자 | 자료 공유 폴더 |
| --- | --- | --- |
| Lean&Mathlib | 박채원 | [lean-mathlib](../../research/lean-mathlib/README.md) |
| Autoformalization | 박선영 · 남성우 | [autoformalization](../../research/autoformalization/README.md) |
| Automated Theorem Proving (ATP) | 권주원 · 손지연 | [automated-theorem-proving](../../research/automated-theorem-proving/README.md) |
| Verifier-guided Agent | 정소미 · 박성호 | [verifier-guided-agent](../../research/verifier-guided-agent/README.md) |

논문 조사 자료는 각 분야의 공유 폴더에 모읍니다.

- [관련 논문 목록 · 37편](../../research/papers.md)
- [연구 자료 안내](../../research/README.md)
