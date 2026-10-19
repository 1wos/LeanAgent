by
  simp only [Imperative.HasVarsPure.getVars, List.Subset]
  intro hn x
  induction hn
  case' app =>
    unfold extractOldExprVars
    split
    simp [Lambda.LExpr.LExpr.getVars]
    rename_i hf
    have hv := ‹IsOldPred _ → IsFvar _› IsOldPred.oldPred
    cases hv
    apply False.elim
    apply hf
    rfl
  all_goals
    simp only [extractOldExprVars, Lambda.LExpr.LExpr.getVars, List.mem_append,
      List.mem_singleton, List.not_mem_nil]
    grind only []
