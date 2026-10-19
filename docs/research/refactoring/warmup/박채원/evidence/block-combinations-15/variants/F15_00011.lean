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
  have h_main : ∀ (d e f : (Fin 9 → ℤ)), ((relation d e) ∧ (relation e f)) → (∀ i : Fin 9, 7 ∣ d i - f i) := by
    intro d e f h
    have h₁ : relation d e := h.1
    have h₂ : relation e f := h.2
    have h₃ : ∀ (i : Fin 9), 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then e j else d j)) := by
      have h₄ : (∀ i : Fin 9, 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then e j else d j))) := (hrelation d e).mp h₁ |>.2
      exact h₄
    have h₄ : ∀ (i : Fin 9), 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then f j else e j)) := by
      have h₅ : (∀ i : Fin 9, 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then f j else e j))) := (hrelation e f).mp h₂ |>.2
      exact h₅

    have h₅ : ∀ (i : Fin 9), 7 ∣ (e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d := by
      intro i
      have h₆ : 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then e j else d j)) := h₃ i
      have h₇ : (digits_to_num (fun j : Fin 9 => if j = i then e j else d j)) = digits_to_num d + (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
        calc
          (digits_to_num (fun j : Fin 9 => if j = i then e j else d j)) = ∑ j : Fin 9, (if j = i then e j else d j) * (10 : ℤ) ^ (j : ℕ) := by
            simp [hdigits_to_num]
            <;>
            rfl
          _ = ∑ j : Fin 9, (if j = i then e j else d j) * (10 : ℤ) ^ (j : ℕ) := rfl
          _ = (∑ j : Fin 9, d j * (10 : ℤ) ^ (j : ℕ)) + (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
            calc
              (∑ j : Fin 9, (if j = i then e j else d j) * (10 : ℤ) ^ (j : ℕ)) = ∑ j : Fin 9, (d j * (10 : ℤ) ^ (j : ℕ) + (if j = i then (e j - d j) else 0) * (10 : ℤ) ^ (j : ℕ)) := by
                apply Finset.sum_congr rfl
                intro j _
                by_cases h : j = i
                · simp [h]
                  <;> ring
                · simp [h]
                  <;> ring
              _ = (∑ j : Fin 9, d j * (10 : ℤ) ^ (j : ℕ)) + ∑ j : Fin 9, (if j = i then (e j - d j) else 0) * (10 : ℤ) ^ (j : ℕ) := by
                rw [Finset.sum_add_distrib]
              _ = (∑ j : Fin 9, d j * (10 : ℤ) ^ (j : ℕ)) + (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
                have h₈ : ∑ j : Fin 9, (if j = i then (e j - d j) else 0) * (10 : ℤ) ^ (j : ℕ) = (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
                  calc
                    _ = ∑ j : Fin 9, (if j = i then (e j - d j) else 0) * (10 : ℤ) ^ (j : ℕ) := rfl
                    _ = (if i = i then (e i - d i) else 0) * (10 : ℤ) ^ (i : ℕ) := by

                      simp [Finset.sum_ite_eq', Finset.mem_univ, i.is_lt]
                    _ = (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by simp
                rw [h₈]
                <;> simp [hdigits_to_num]
                <;>
                rfl
          _ = digits_to_num d + (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
            simp [hdigits_to_num]
            <;>
            rfl
      have h₈ : 7 ∣ digits_to_num d + (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by
        rw [h₇] at h₆
        exact h₆

      have h₉ : 7 ∣ (e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d := by

        have h₁₀ : (e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d = digits_to_num d + (e i - d i) * (10 : ℤ) ^ (i : ℕ) := by ring
        rw [h₁₀]
        exact h₈
      exact h₉

    have h₆ : ∀ (i : Fin 9), 7 ∣ (f i - e i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num e := by
      intro i
      have h₇ : 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then f j else e j)) := h₄ i
      have h₈ : (digits_to_num (fun j : Fin 9 => if j = i then f j else e j)) = digits_to_num e + (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by
        calc
          (digits_to_num (fun j : Fin 9 => if j = i then f j else e j)) = ∑ j : Fin 9, (if j = i then f j else e j) * (10 : ℤ) ^ (j : ℕ) := by
            simp [hdigits_to_num]
            <;>
            rfl
          _ = ∑ j : Fin 9, (if j = i then f j else e j) * (10 : ℤ) ^ (j : ℕ) := rfl
          _ = (∑ j : Fin 9, e j * (10 : ℤ) ^ (j : ℕ)) + (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by
            calc
              (∑ j : Fin 9, (if j = i then f j else e j) * (10 : ℤ) ^ (j : ℕ)) = ∑ j : Fin 9, (e j * (10 : ℤ) ^ (j : ℕ) + (if j = i then (f j - e j) else 0) * (10 : ℤ) ^ (j : ℕ)) := by
                apply Finset.sum_congr rfl
                intro j _
                by_cases h : j = i
                · simp [h]
                  <;> ring
                · simp [h]
                  <;> ring
              _ = (∑ j : Fin 9, e j * (10 : ℤ) ^ (j : ℕ)) + ∑ j : Fin 9, (if j = i then (f j - e j) else 0) * (10 : ℤ) ^ (j : ℕ) := by
                rw [Finset.sum_add_distrib]
              _ = (∑ j : Fin 9, e j * (10 : ℤ) ^ (j : ℕ)) + (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by
                have h₉ : ∑ j : Fin 9, (if j = i then (f j - e j) else 0) * (10 : ℤ) ^ (j : ℕ) = (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by
                  calc
                    _ = ∑ j : Fin 9, (if j = i then (f j - e j) else 0) * (10 : ℤ) ^ (j : ℕ) := rfl
                    _ = (if i = i then (f i - e i) else 0) * (10 : ℤ) ^ (i : ℕ) := by

                      simp [Finset.sum_ite_eq', Finset.mem_univ, i.is_lt]
                    _ = (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by simp
                rw [h₉]
                <;> simp [hdigits_to_num]
                <;>
                rfl
          _ = digits_to_num e + (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by
            simp [hdigits_to_num]
            <;>
            rfl
      have h₉ : 7 ∣ digits_to_num e + (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by
        rw [h₈] at h₇
        exact h₇

      have h₁₀ : 7 ∣ (f i - e i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num e := by

        have h₁₁ : (f i - e i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num e = digits_to_num e + (f i - e i) * (10 : ℤ) ^ (i : ℕ) := by ring
        rw [h₁₁]
        exact h₉
      exact h₁₀

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

    intro i
    have h₁₀ : 7 ∣ d i - f i := h₉ i
    exact h₁₀
  exact h_main

#print axioms putnam_1995_a3
