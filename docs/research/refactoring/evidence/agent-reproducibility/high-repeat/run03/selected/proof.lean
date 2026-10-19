by
  have app {a b c d : List Expression.Ident} (ha : a.Subset c) (hb : b.Subset d) :
      (a ++ b).Subset (c ++ d) := by
    intro x hx
    simp only [List.mem_append] at hx ⊢
    exact hx.elim (fun h => Or.inl (ha h)) (fun h => Or.inr (hb h))
  intro h
  induction h <;>
    try (solve | exact List.nil_subset _ | assumption | exact app ‹_› ‹_› |
      exact app (app ‹_› ‹_›) ‹_›)
  rename_i hn ihfn ihe
  unfold extractOldExprVars
  split
  · exact fun _ hx => hx
  · next hbad =>
      cases hn (by constructor)
      exfalso
      apply hbad
      rfl
  · exact app ihfn ihe
