by
  rintro -
  refine List.Sublist.subset ?_
  induction post
  case app ih1 ih2 =>
    unfold extractOldExprVars
    split
    · exact List.Sublist.refl _
    · exact List.nil_sublist _
    · exact ih1.append ih2
  all_goals repeat' first | exact List.nil_sublist _ | assumption | apply List.Sublist.append
