# Lean Refactor Warmup

## Meta
- style: custom-light-technical
- language: ko
- audience: Lean을 처음 배우며 대회 준비 과정을 공유하는 스터디 참여자
- format: 자체 포함 HTML viewer, 16:9 중심·모바일 대응·키보드 이전/다음·인쇄
- scope: 대화에서 정한 접근과 확인된 실행 사실; 개선 성과를 주장하지 않음

## 디자인
흰 배경 #FFFFFF, 옅은 청회색 #F2F5F8, 본문 남청색 #182B40, 보조색 #53677B, 강조 청색 #1557B0. 제목·본문은 한국어 시스템 sans-serif, 코드는 monospace. 좌측 정렬, 큰 제목과 한 장 한 메시지, 코드/설명 2열 구성을 사용한다. 장식 차트와 가상 점수는 사용하지 않는다.

## 슬라이드
1. **Lean을 배우며 증명을 개선하기** — 8·11번 warmup으로 이해·가설·검증·기록의 루프를 만든다.
2. **대회에서 개선하는 것과 지켜야 하는 것** — 같은 명제의 정확성 유지; 길이 감소율·heartbeat 감소율·버전 호환성 평균; Track 1 API 예산 최대 $3/문제, 재시도·폐기 포함. 비용 자체는 가점 항목이 아니다.
3. **제로 베이스에서 시작한 학습** — 식, 적용(⬝), 축약, 증거; refl은 그대로 두기, red_I/K/S는 규칙 적용, par는 부분 축약 조합. cases/case는 증거 생성자별 경우 분석.
4. **8번: 두 축약 결과를 다시 만나게 하기** — Diamond: a⇒a₁, a⇒a₂이면 공통 b로 각각 병렬 축약. 각 분기는 공통 항·두 경로를 구성; par/par은 작은 부분항에서 재귀적으로 합류.
5. **8번 첫 후보: 탐색 대신 증거 조립** — S/par 혼합 분기의 apply/par/grind를 exact .par (.par h.1 hb') (.par h.2.1 hb')로 바꾸는 가설. 후보는 아직 검증·측정하지 않았으며 개선 결과가 아니다.
6. **11번: 긴 증명은 의미 단위로 읽기** — fold 함수 결과가 갱신된 계수의 다음 단계 다항식 평가와 같음. fiber의 두 점→qMap/차이 성질→짝수·홀수 분해→계수 갱신 일치. 반복 인덱스 산술·rewrite는 조사할 후보이며 병목으로 확정하지 않는다. 상세 구조 최적화는 앞으로 수행.
7. **두 문제에 적용할 구조 분석 체크리스트** — 핵심 구조·의존성·불필요 분기·기존 정리·반복 논리 확인. 귀납법 변경/보조정리 분리는 필수가 아니라 후보; 매번 후보 하나만 생성.
8. **skill은 판단 절차, harness는 실행 기록** — lean-refactor 하나 + 기존 Lean 검사·비용 원장 재사용. 가설/원본/후보/환경/로그/측정/비용/채택 이유를 연결. 실패와 timeout도 보존.
9. **현재 확인된 것과 아직 모르는 것** — 회귀 테스트20개 PASS, 8번 원본을 후보로 넣은 baseline/candidate 실제검증 PASS; 저장된 기록상 11번 원본 v4.31.0 PASS. 공식 길이/heartbeat·다른 버전·최적화 효과는 미측정/미검증. 독립 코드리뷰 미확인; 비용 사전강제/자동 API호출 미구현.
10. **다음 실험과 대회 준비** — 기준 지표 확보→8번 단일 후보 실행→공식 측정/지정버전 비교→11번 구조 분석 확장→반복 가능 절차 자동화. 호출 수보다 예산 내 유효 후보에 집중; 학습 대화 비용 산정 경계는 공식 규칙 추가확인.

## 근거
- STRUCTURAL_REFACTOR_PLAN.md
- solution/README.md 및 solution/08·11 README/reference.lean/verification.json
- harness/README.md, harness/experiment.py, harness/budget.py
- 이번 세션 unittest 출력(20개 성공), 8번 원본 후보 실험 출력(baseline/candidate passed)
- 공식 안내: https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena
