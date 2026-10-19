# 15번 블록 조합 32개

`putnam_1995_a3` 참조 증명을 블록 다섯 개로 나누고, 블록마다 참조 증명 그대로 또는 짧은 증명을 골라 만든 32개 Lean 파일입니다. 공식 점수 중 길이 축에서 블록별 기여를 나누기 위해 만들었습니다. 결과는 [발표자료](../../presentation.html) 12–14장에 있습니다.

## 블록

| 블록 | 참조 증명 `P15_ref.lean`의 줄 | 짧은 증명 |
| --- | --- | --- |
| E | `h_main`, `h₁`–`h₄` 16–25, 끝 288–291 | `intro`, `obtain` 두 줄, 끝 `exact h₉` |
| A | `h₅` 27–74, `h₆` 76–123 | 보조정리 `key` + `h₅`, `h₆` 각 2줄 |
| B | `h₇` 125–198 | 7줄 |
| C | `h₈` 200–231 | 3줄 |
| D | `h₉` 233–286 | 2줄 |

- 블록 경계는 참조 증명의 `have` 들여쓰기 경계이고, [block_tokens.py](../local-v4.26/tools/block_tokens.py)의 줄 범위와 같습니다.
- 짧은 증명은 블록의 `have` 명제 줄을 그대로 두고 그 아래 증명만 다시 쓴 것입니다. 그래서 어떤 조합도 컴파일됩니다.
- E, D와 A의 `key`는 [P15_mine.lean](../local-v4.26/P15_mine.lean)에서 가져왔고, A의 `h₅`·`h₆` 각 2줄과 B, C는 참조 증명의 명제에 맞춰 새로 썼습니다.
- 파일 이름 `F15_EABCD`의 각 자리는 그 블록의 선택입니다. 1은 짧은 증명, 0은 참조 증명입니다.

## 결과

[results.csv](results.csv)에 32개 파일의 proof token, 길이 감소율, 컴파일 여부, 공리를 적었습니다.

- 토큰은 공식 `proof_length` 재구현 [proof_tokens.py](../local-v4.26/tools/proof_tokens.py)로 셌습니다. `F15_00000`은 4,085로 공식 값과 같습니다.
- 32개 모두 토큰 = 4,085 − 바꾼 블록들의 감소 합입니다. 블록별 감소는 A 1,391, B 1,082, D 483, C 467, E 219이고, 다섯 블록을 모두 바꾸면 443토큰, 길이 감소율 89.16%입니다.
- 길이 감소율은 (4,085 − 토큰) ÷ 4,085입니다.

## 컴파일 환경

- Lean v4.26.0, Mathlib v4.26.0, `lake env lean <파일>`.
- 대회 헤더의 전체 `import Mathlib`이 아니라 파일 맨 위의 Mathlib 모듈만 import했습니다. 32개 모두 같은 import입니다.
- 32개 모두 에러 없이 컴파일되었고, `#print axioms` 결과는 `propext`, `Classical.choice`, `Quot.sound`입니다.
- heartbeat는 공식 채점 환경과 같은 값인지 확인할 수 없어 기록하지 않았습니다.

## 다시 만들기

```bash
cd docs/research/refactoring/warmup/박채원/evidence/block-combinations-15
python make_variants.py --tokens          # variants/ 32개 파일과 토큰
python make_variants.py --full --tokens   # 전체 import Mathlib 헤더로 만들기
```
