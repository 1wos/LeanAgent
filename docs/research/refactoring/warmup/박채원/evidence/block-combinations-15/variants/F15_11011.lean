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
    have h₈ : digits_to_num e = digits_to_num d + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
      calc
        digits_to_num e = ∑ i : Fin 9, e i * (10 : ℤ) ^ (i : ℕ) := by simp [hdigits_to_num]
        _ = ∑ i : Fin 9, (d i + (e i - d i)) * (10 : ℤ) ^ (i : ℕ) := by
          apply Finset.sum_congr rfl
          intro i _
          ring
        _ = ∑ i : Fin 9, (d i * (10 : ℤ) ^ (i : ℕ) + (e i - d i) * (10 : ℤ) ^ (i : ℕ)) := by
          apply Finset.sum_congr rfl
          intro i _
          ring
        _ = (∑ i : Fin 9, d i * (10 : ℤ) ^ (i : ℕ)) + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
          rw [Finset.sum_add_distrib]
        _ = digits_to_num d + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
          simp [hdigits_to_num]
          <;>
          rfl
    have h₉ : ∀ i : Fin 9, 7 ∣ (e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d := h₅
    have h₁₀ : 7 ∣ ∑ i : Fin 9, ((e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d) := by
      apply Finset.dvd_sum
      intro i _
      exact h₉ i
    have h₁₁ : ∑ i : Fin 9, ((e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d) = ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) + 9 * digits_to_num d := by
      calc
        ∑ i : Fin 9, ((e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d) = ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) + ∑ i : Fin 9, digits_to_num d := by
          rw [Finset.sum_add_distrib]
        _ = ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) + 9 * digits_to_num d := by
          simp [Finset.sum_const, Finset.card_fin]
          <;> ring
          <;> norm_num
    have h₁₂ : 7 ∣ ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) + 9 * digits_to_num d := by
      rw [h₁₁] at h₁₀
      exact h₁₀
    have h₁₃ : 7 ∣ digits_to_num e + digits_to_num d := by
      have h₁₄ : digits_to_num e + digits_to_num d = 2 * digits_to_num d + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
        linarith
      rw [h₁₄]
      have h₁₅ : 7 ∣ 2 * digits_to_num d + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
        have h₁₆ : 7 ∣ ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) + 9 * digits_to_num d := h₁₂
        have h₁₇ : 7 ∣ 2 * digits_to_num d + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by

          have h₁₈ : (∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) + 9 * digits_to_num d) = (∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ)) + 9 * digits_to_num d := by ring
          rw [h₁₈] at h₁₆






          have h₁₉ : 7 ∣ (∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ)) + 2 * digits_to_num d := by



            have h₂₀ : 7 ∣ (∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ)) + 9 * digits_to_num d := h₁₆
            have h₂₁ : 7 ∣ 7 * digits_to_num d := by
              use digits_to_num d
              <;> ring
            have h₂₂ : 7 ∣ (∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ)) + 2 * digits_to_num d := by

              have h₂₃ : (∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ)) + 2 * digits_to_num d = ((∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ)) + 9 * digits_to_num d) - 7 * digits_to_num d := by ring
              rw [h₂₃]
              exact dvd_sub h₂₀ h₂₁
            exact h₂₂

          have h₂₀ : 7 ∣ 2 * digits_to_num d + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by

            have h₂₁ : 2 * digits_to_num d + ∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ) = (∑ i : Fin 9, (e i - d i) * (10 : ℤ) ^ (i : ℕ)) + 2 * digits_to_num d := by ring
            rw [h₂₁]
            exact h₁₉
          exact h₂₀
        exact h₁₇
      exact h₁₅
    exact h₁₃

  have h₈ : ∀ (i : Fin 9), 7 ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := fun i => by
    convert dvd_sub (dvd_add (h₅ i) (h₆ i)) h₇ using 1
    ring

  have h₉ : ∀ (i : Fin 9), 7 ∣ d i - f i := fun i =>
    dvd_sub_comm.mp ((IsCoprime.pow_right ⟨3, -2, by norm_num⟩).dvd_of_dvd_mul_right (h₈ i))

  exact h₉

#print axioms putnam_1995_a3
