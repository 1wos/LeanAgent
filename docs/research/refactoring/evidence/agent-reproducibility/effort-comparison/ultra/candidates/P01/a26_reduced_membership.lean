by
  dsimp only [Imperative.HasVarsPure.getVars]
  intro x
  induction post <;> simp only [substOld]
  all_goals repeat split
  all_goals
    simp only [Lambda.LExpr.LExpr.getVars, List.mem_append] at *
    grind only
