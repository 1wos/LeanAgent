by
  have combine {a b c d : List Expression.Ident}
      (ha : a.Subset (b ++ [h1])) (hc : c.Subset (d ++ [h1])) :
      (a ++ c).Subset ((b ++ d) ++ [h1]) := by
    simp only [List.Subset, List.mem_append] at *
    grind only
  induction post <;>
    dsimp only [substOld]
  case const | op | bvar | fvar => exact List.subset_append_left _ _
  case abs ih => exact ih
  case quant ih1 ih2 | eq ih1 ih2 => exact combine ih1 ih2
  case ite cih tih eih => exact combine (combine cih tih) eih
  case app ih1 ih2 =>
    split
    · split
      · exact List.subset_append_right _ _
      · exact List.subset_append_left _ _
    · exact combine ih1 ih2
