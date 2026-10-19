import Mathlib.RingTheory.Int.Basic
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Tactic.Ring
import Mathlib.RingTheory.Coprime.Lemmas
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Data.Nat.Prime.Basic
import Mathlib.Data.Int.GCD
import Mathlib.Util.CountHeartbeats
import Aesop

set_option maxHeartbeats 100000000
set_option Elab.async false

#count_heartbeats in
theorem putnam_1995_a3
(relation : (Fin 9 → ℤ) → (Fin 9 → ℤ) → Prop)
(digits_to_num : (Fin 9 → ℤ) → ℤ)
(hdigits_to_num : digits_to_num = fun dig => ∑ i : Fin 9, (dig i) * 10^i.1)
(hrelation : ∀ d e : (Fin 9 → ℤ), relation d e ↔ (∀ i : Fin 9, d i < 10 ∧ d i ≥ 0 ∧ e i < 10 ∧ e i ≥ 0) ∧ (∀ i : Fin 9, 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then e j else d j))))
: ∀ d e f : (Fin 9 → ℤ), ((relation d e) ∧ (relation e f)) → (∀ i : Fin 9, 7 ∣ d i - f i) := by
  intro d e f h
  obtain ⟨-, h₃⟩ := (hrelation d e).mp h.1
  obtain ⟨-, h₄⟩ := (hrelation e f).mp h.2

  have key : ∀ (x y : Fin 9 → ℤ) (i : Fin 9), digits_to_num (fun j => if j = i then y j else x j) = digits_to_num x + (y i - x i) * 10 ^ (i : ℕ) := fun x y i => by
    subst hdigits_to_num
    beta_reduce
    rw [show (y i - x i) * 10 ^ i.1 = ∑ j, if j = i then (y j - x j) * 10 ^ j.1 else 0 by simp, ← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun j _ => by split_ifs with h <;> [(subst h; ring); simp]
  have h₅ : ∀ (i : Fin 9), 7 ∣ (e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d := fun i => by
    have := h₃ i
    rwa [key, add_comm] at this

  have h₆ : ∀ (i : Fin 9), 7 ∣ (f i - e i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num e := fun i => by
    have := h₄ i
    rwa [key, add_comm] at this

  have h₇ : 7 ∣ digits_to_num e + digits_to_num d := by
    have hS := Finset.dvd_sum (s := .univ) fun i _ => h₅ i
    subst hdigits_to_num
    simp only [Finset.sum_add_distrib, sub_mul, Finset.sum_sub_distrib, Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul] at hS ⊢
    convert dvd_sub hS (dvd_mul_right 7 (∑ i : Fin 9, d i * 10 ^ (i : ℕ))) using 1
    push_cast
    ring

  have h₈ : ∀ (i : Fin 9), 7 ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := fun i => by
    convert dvd_sub (dvd_add (h₅ i) (h₆ i)) h₇ using 1
    ring

  have h₉ : ∀ (i : Fin 9), 7 ∣ d i - f i := by
    intro i
    have h₁₀ : 7 ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := h₈ i
    have h₁₁ : 7 ∣ (f i - d i) := by

      have h₁₂ : (7 : ℤ) ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := h₁₀

      have h₁₃ : (7 : ℕ).Prime := by decide
      have h₁₄ : ¬(7 : ℤ) ∣ (10 : ℤ) ^ (i : ℕ) := by

        intro h
        have h₁₅ : (7 : ℕ) ∣ (10 : ℕ) ^ (i : ℕ) := by
          norm_cast at h ⊢
          <;> simpa [Int.coe_nat_dvd_left] using h
        have h₁₆ : (7 : ℕ) ∣ 10 := by

          exact Nat.Prime.dvd_of_dvd_pow h₁₃ h₁₅
        norm_num at h₁₆
        <;> contradiction

      have h₁₅ : (7 : ℤ) ∣ (f i - d i) := by

        have h₁₆ : (7 : ℤ) ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := h₁₂
        have h₁₇ : ¬(7 : ℤ) ∣ (10 : ℤ) ^ (i : ℕ) := h₁₄

        have h₁₈ : (7 : ℤ) ∣ (f i - d i) := by

          have h₁₉ : (7 : ℤ) ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := h₁₂
          have h₂₀ : (7 : ℕ).Prime := by decide
          have h₂₁ : (7 : ℤ) ∣ (f i - d i) ∨ (7 : ℤ) ∣ (10 : ℤ) ^ (i : ℕ) := by

            have h₂₂ : (7 : ℤ) ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := h₁₂
            have h₂₃ : (7 : ℤ) ∣ (f i - d i) ∨ (7 : ℤ) ∣ (10 : ℤ) ^ (i : ℕ) := by

              apply (Int.prime_iff_natAbs_prime.mpr (by decide)).dvd_mul.mp
              exact h₂₂
            exact h₂₃
          cases h₂₁ with
          | inl h₂₁ =>
            exact h₂₁
          | inr h₂₁ =>
            exfalso
            exact h₁₄ h₂₁
        exact h₁₈
      exact h₁₅

    have h₁₂ : 7 ∣ d i - f i := by
      have h₁₃ : 7 ∣ (f i - d i) := h₁₁
      have h₁₄ : 7 ∣ -(f i - d i) := by
        exact dvd_neg.mpr h₁₃
      have h₁₅ : -(f i - d i) = d i - f i := by ring
      rw [h₁₅] at h₁₄
      exact h₁₄
    exact h₁₂

  exact h₉

#print axioms putnam_1995_a3
