by
  have join {a b c d : List Expression.Ident}
      (ha : a.Subset c) (hb : b.Subset d) :
      (a ++ b).Subset (c ++ d) := by
    intro x h
    exact List.mem_append.mpr ((List.mem_append.mp h).imp ha hb)
  intro Hnorm
  induction post <;>
    simp only [Imperative.HasVarsPure.getVars, extractOldExprVars,
      Lambda.LExpr.LExpr.getVars] at * <;> try simp_all
  case app fn e fn_ih e_ih =>
    unfold extractOldExprVars
    split
    · simp [Lambda.LExpr.LExpr.getVars]
      exact fun _ h => h
    · next Hfalse =>
      cases Hnorm with
      | app H1 H2 Hn =>
        exfalso
        specialize Hn (by constructor)
        cases Hn
        apply Hfalse
        rfl
    · cases Hnorm with
      | app H1 H2 Hn => exact join (fn_ih H1) (e_ih H2)
  case abs ih =>
    cases Hnorm
    apply ih <;> assumption
  case quant trih eih =>
    cases Hnorm
    exact join (trih ‹_›) (eih ‹_›)
  case ite cih tih eih =>
    cases Hnorm
    exact join (cih ‹_›) (join (tih ‹_›) (eih ‹_›))
  case eq ih1 ih2 =>
    cases Hnorm
    exact join (ih1 ‹_›) (ih2 ‹_›)
