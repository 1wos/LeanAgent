by
  dsimp only [Imperative.HasVarsPure.getVars]
  intro h
  clear h
  intro x
  induction post <;>
    simp only [extractOldExprVars, Lambda.LExpr.LExpr.getVars,
      List.mem_append, List.not_mem_nil] at *
  case app ihfn ihe =>
    unfold extractOldExprVars
    split
    · exact Or.inr
    · exact nofun
    · simp only [List.mem_append]
      exact Or.imp ihfn ihe
  all_goals grind only
