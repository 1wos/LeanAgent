import MIL.Common
import Mathlib.Topology.MetricSpace.Basic

/-
# Mathematics in Lean 2.5 Proving Facts about Algebraic Structures — 풀이와 개념 정리

출처
- 원문: Jeremy Avigad, Patrick Massot, *Mathematics in Lean*, 2.5 Proving Facts about Algebraic Structures
  https://leanprover-community.github.io/mathematics_in_lean/C02_Basics.html#proving-facts-about-algebraic-structures
- 원본 코드: https://github.com/leanprover-community/mathematics_in_lean
  (`MIL/C02_Basics/S05_Proving_Facts_about_Algebraic_Structures.lean`, Apache License 2.0)
- 원본 연습문제의 `sorry` 자리에 답안 작성 및 개념 설명용 한국어 주석 추가함.
  문제·예제 문장과 영어 주석은 원본 그대로 유지함.
- 원본 저장소 Lean 버전: v4.30.0

## 핵심 개념
- 2.4에서 실수의 min/max 로 했던 증명을 **추상 구조**에서 다시 한다.
  같은 증명이 구조의 공리만 쓰기 때문에 더 넓은 대상에 그대로 적용된다.
- `PartialOrder` (부분순서) : ≤ 가 반사·추이·반대칭 (`le_refl`, `le_trans`, `le_antisymm`)
- `Lattice` (격자) : 두 원소마다 ⊓ (inf, 최대 하계)와 ⊔ (sup, 최소 상계)가 있다.
  실수의 min/max, 집합의 ∩/∪, 자연수의 gcd/lcm 이 모두 격자의 예.
  → 2.4 의 min 증명과 2.5 의 ⊓ 증명이 **똑같은 모양**인 이유.
- `DistribLattice` : 분배법칙까지 성립하는 격자
- 순서환 : 부등식과 사칙연산이 맞물리는 규칙 (`add_le_add_right`, `mul_nonneg`)
- `MetricSpace` (거리공간) : 거리 함수 `dist` 와 `dist_self`, `dist_comm`, `dist_triangle`
- 새 tactic: `trans y` (부등식 중간에 y 를 끼워 넣기, le_trans 와 같은 역할)
-/

section
variable {α : Type*} [PartialOrder α]
variable (x y z : α)

#check x ≤ y
#check (le_refl x : x ≤ x)
#check (le_trans : x ≤ y → y ≤ z → x ≤ z)
#check (le_antisymm : x ≤ y → y ≤ x → x = y)


#check x < y
#check (lt_irrefl x : ¬ (x < x))
#check (lt_trans : x < y → y < z → x < z)
#check (lt_of_le_of_lt : x ≤ y → y < z → x < z)
#check (lt_of_lt_of_le : x < y → y ≤ z → x < z)

example : x < y ↔ x ≤ y ∧ x ≠ y :=
  lt_iff_le_and_ne

end

section
variable {α : Type*} [Lattice α]
variable (x y z : α)

#check x ⊓ y
#check (inf_le_left : x ⊓ y ≤ x)
#check (inf_le_right : x ⊓ y ≤ y)
#check (le_inf : z ≤ x → z ≤ y → z ≤ x ⊓ y)
#check x ⊔ y
#check (le_sup_left : x ≤ x ⊔ y)
#check (le_sup_right : y ≤ x ⊔ y)
#check (sup_le : x ≤ z → y ≤ z → x ⊔ y ≤ z)

-- 2.4 의 min a b = min b a 와 같은 증명 (min → ⊓)
example : x ⊓ y = y ⊓ x := by
  apply le_antisymm
  repeat
    apply le_inf
    · apply inf_le_right
    apply inf_le_left

-- 2.4 의 min 결합법칙과 같은 구조. trans 로 중간 항을 끼운다.
example : x ⊓ y ⊓ z = x ⊓ (y ⊓ z) := by
  apply le_antisymm
  · apply le_inf
    · trans x ⊓ y
      apply inf_le_left
      apply inf_le_left
    apply le_inf
    · trans x ⊓ y
      apply inf_le_left
      apply inf_le_right
    apply inf_le_right
  apply le_inf
  · apply le_inf
    · apply inf_le_left
    trans y ⊓ z
    apply inf_le_right
    apply inf_le_left
  trans y ⊓ z
  apply inf_le_right
  apply inf_le_right

-- ⊔ 는 ⊓ 의 방향만 뒤집은 것 (le_inf ↔ sup_le)
example : x ⊔ y = y ⊔ x := by
  apply le_antisymm
  repeat
    apply sup_le
    · apply le_sup_right
    apply le_sup_left

example : x ⊔ y ⊔ z = x ⊔ (y ⊔ z) := by
  apply le_antisymm
  · apply sup_le
    · apply sup_le
      apply le_sup_left
      · trans y ⊔ z
        apply le_sup_left
        apply le_sup_right
    trans y ⊔ z
    apply le_sup_right
    apply le_sup_right
  apply sup_le
  · trans x ⊔ y
    apply le_sup_left
    apply le_sup_left
  apply sup_le
  · trans x ⊔ y
    apply le_sup_right
    apply le_sup_left
  apply le_sup_right

-- 흡수법칙: x ⊓ (x ⊔ y) = x
theorem absorb1 : x ⊓ (x ⊔ y) = x := by
  apply le_antisymm
  · apply inf_le_left
  apply le_inf
  · apply le_refl
  apply le_sup_left

theorem absorb2 : x ⊔ x ⊓ y = x := by
  apply le_antisymm
  · apply sup_le
    · apply le_refl
    apply inf_le_left
  apply le_sup_left

end

section
variable {α : Type*} [DistribLattice α]
variable (x y z : α)

#check (inf_sup_left x y z : x ⊓ (y ⊔ z) = x ⊓ y ⊔ x ⊓ z)
#check (inf_sup_right x y z : (x ⊔ y) ⊓ z = x ⊓ z ⊔ y ⊓ z)
#check (sup_inf_left x y z : x ⊔ y ⊓ z = (x ⊔ y) ⊓ (x ⊔ z))
#check (sup_inf_right x y z : x ⊓ y ⊔ z = (x ⊔ z) ⊓ (y ⊔ z))
end

section
variable {α : Type*} [Lattice α]
variable (a b c : α)

-- 한쪽 분배법칙이 성립하면 다른 쪽도 성립한다 (흡수법칙과 교환법칙으로 정리).
example (h : ∀ x y z : α, x ⊓ (y ⊔ z) = x ⊓ y ⊔ x ⊓ z) : a ⊔ b ⊓ c = (a ⊔ b) ⊓ (a ⊔ c) := by
  rw [h, @inf_comm _ _ (a ⊔ b), absorb1, @inf_comm _ _ (a ⊔ b), h, ← sup_assoc, @inf_comm _ _ c a,
    absorb2, inf_comm]

example (h : ∀ x y z : α, x ⊔ y ⊓ z = (x ⊔ y) ⊓ (x ⊔ z)) : a ⊓ (b ⊔ c) = a ⊓ b ⊔ a ⊓ c := by
  rw [h, @sup_comm _ _ (a ⊓ b), absorb2, @sup_comm _ _ (a ⊓ b), h, ← inf_assoc, @sup_comm _ _ c a,
    absorb1, sup_comm]

end

section
variable {R : Type*} [Ring R] [PartialOrder R] [IsStrictOrderedRing R]
variable (a b c : R)

#check (add_le_add_right : a ≤ b → ∀ c, c + a ≤ c + b)
#check (mul_pos : 0 < a → 0 < b → 0 < a * b)

#check (mul_nonneg : 0 ≤ a → 0 ≤ b → 0 ≤ a * b)

-- sub_nonneg : 0 ≤ a - b ↔ b ≤ a
example (h : a ≤ b) : 0 ≤ b - a := by
  exact sub_nonneg.mpr h

example (h: 0 ≤ b - a) : a ≤ b := by
  exact sub_nonneg.mp h

-- 0 ≤ (b - a) * c 를 만들고 펼치면 0 ≤ b * c - a * c → a * c ≤ b * c
example (h : a ≤ b) (h' : 0 ≤ c) : a * c ≤ b * c := by
  have h1 : 0 ≤ (b - a) * c := mul_nonneg (sub_nonneg.mpr h) h'
  rw [sub_mul] at h1
  exact sub_nonneg.mp h1

end

section
variable {X : Type*} [MetricSpace X]
variable (x y z : X)

#check (dist_self x : dist x x = 0)
#check (dist_comm x y : dist x y = dist y x)
#check (dist_triangle x y z : dist x z ≤ dist x y + dist y z)

-- 0 = dist x x ≤ dist x y + dist y x = 2 * dist x y
example (x y : X) : 0 ≤ dist x y := by
  have : 0 ≤ dist x y + dist y x := by
    rw [← dist_self x]
    apply dist_triangle
  linarith [dist_comm x y]

end
