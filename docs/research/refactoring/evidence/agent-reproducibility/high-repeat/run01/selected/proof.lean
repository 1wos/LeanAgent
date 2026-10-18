by
  have appendSub {a b c d : List Expression.Ident}
      (ha : a.Subset b) (hc : c.Subset d) : (a ++ c).Subset (b ++ d) :=
    List.Subset.app
      (fun _ hx => List.mem_append.mpr (.inl (ha hx)))
      (fun _ hx => List.mem_append.mpr (.inr (hc hx)))
  intro h
  induction h with
  | const | op | bvar | fvar =>
    intro x hx
    cases hx
  | abs h ih => exact ih
  | quant h1 h2 ih1 ih2 => exact appendSub ih1 ih2
  | ite h1 h2 h3 ih1 ih2 ih3 => exact appendSub (appendSub ih1 ih2) ih3
  | eq h1 h2 ih1 ih2 => exact appendSub ih1 ih2
  | app h1 h2 hOld ih1 ih2 =>
    unfold extractOldExprVars
    split
    · exact fun _ hx => hx
    · next hfalse =>
        exfalso
        have hf := hOld IsOldPred.oldPred
        cases hf
        apply hfalse
        rfl
    · exact appendSub ih1 ih2
