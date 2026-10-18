by
  have join {a b c d : List Expression.Ident}
      (h : a.Subset c) (k : b.Subset d) : (a ++ b).Subset (c ++ d) :=
    List.Subset.app
      (fun _ hx => List.mem_append.mpr (Or.inl (h hx)))
      (fun _ hx => List.mem_append.mpr (Or.inr (k hx)))
  intros Hnorm
  induction post <;>
    simp [Imperative.HasVarsPure.getVars, extractOldExprVars,
          Lambda.LExpr.LExpr.getVars] at *
  case app fn e fn_ih e_ih =>
    unfold extractOldExprVars
    split
    . simp [Lambda.LExpr.LExpr.getVars]
      intros x Hin
      exact Hin
    . next Hfalse =>
      cases Hnorm with
      | app H1 H2 Hn =>
      exfalso
      specialize Hn ?_
      constructor
      cases Hn
      apply Hfalse
      rfl
    . cases Hnorm with
      | app H1 H2 Hn =>
      exact join (fn_ih H1) (e_ih H2)
  case abs ih =>
    cases Hnorm
    apply ih <;> assumption
  case quant trih eih =>
    cases Hnorm
    apply join
    . apply trih <;> assumption
    . apply eih <;> assumption
  case ite cih tih eih =>
    cases Hnorm
    apply join
    . apply cih <;> assumption
    apply join
    . apply tih <;> assumption
    . apply eih <;> assumption
  case eq ih1 ih2 =>
    cases Hnorm
    apply join
    . apply ih1 <;> assumption
    . apply ih2 <;> assumption
