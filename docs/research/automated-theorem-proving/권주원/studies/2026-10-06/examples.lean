/-
ATP study examples. No Mathlib required.
Run: lean +leanprover/lean4:v4.26.0 examples.lean
trace_state prints the actual goals for the first proof.
-/

namespace ATPStudy

theorem swapAnd (P Q : Prop) : P ∧ Q → Q ∧ P := by
  trace_state
  intro h
  trace_state
  constructor
  · trace_state
    exact h.2
  · trace_state
    exact h.1

-- Reuse an existing theorem instead of constructing each step again.
theorem swapAndViaPremise (P Q : Prop) : P ∧ Q → Q ∧ P := by
  exact swapAnd P Q

-- Choosing a witness for an existential goal.
theorem existsSelf (n : Nat) : ∃ m : Nat, m = n := by
  exact ⟨n, rfl⟩

end ATPStudy
