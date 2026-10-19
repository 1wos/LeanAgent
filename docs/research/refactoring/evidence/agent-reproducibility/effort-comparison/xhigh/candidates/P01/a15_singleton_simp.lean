by
  simp only [Imperative.HasVarsPure.getVars, List.Subset,
    List.mem_append, List.mem_singleton]
  intro x
  induction post <;> simp only [substOld]
  case' app => split <;> try split
  all_goals
    simp only [Lambda.LExpr.LExpr.getVars, List.mem_append,
      List.mem_singleton, List.not_mem_nil]
    grind only []
