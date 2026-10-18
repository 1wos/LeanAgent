by
  have join {a b c d : List Expression.Ident}
      (h : a.Subset c) (h' : b.Subset d) :
      (a ++ b).Subset (c ++ d) := by
    apply List.Subset.app
    · intro x hx
      simp [h hx]
    · intro x hx
      simp [h' hx]
  intros Hnorm
  induction post <;>
    simp [Imperative.HasVarsPure.getVars, extractOldExprVars,
          Lambda.LExpr.LExpr.getVars] at * <;>
    try simp_all
  case app fn e fn_ih e_ih =>
    unfold extractOldExprVars
    split
    · simp [Lambda.LExpr.LExpr.getVars]
      intros x Hin
      exact Hin
    · next Hfalse =>
      cases Hnorm with
      | app H1 H2 Hn =>
        exfalso
        specialize Hn ?_
        constructor
        cases Hn
        apply Hfalse
        rfl
    · cases Hnorm with
      | app H1 H2 Hn => exact join (fn_ih H1) (e_ih H2)
  case abs ih =>
    cases Hnorm
    apply ih <;> assumption
  case quant trih eih =>
    cases Hnorm with
    | quant H1 H2 => exact join (trih H1) (eih H2)
  case ite cih tih eih =>
    cases Hnorm with
    | ite H1 H2 H3 => exact join (cih H1) (join (tih H2) (eih H3))
  case eq ih1 ih2 =>
    cases Hnorm with
    | eq H1 H2 => exact join (ih1 H1) (ih2 H2)
