by
  have join {a b c d : List Expression.Ident} (ha : a.Subset c) (hb : b.Subset d) :=
    List.Subset.app (fun _ h => List.mem_append_left d (ha h))
      (fun _ h => List.mem_append_right c (hb h))
  intro h
  induction h with
  | app _ _ hn ihfn ihe =>
    unfold extractOldExprVars
    split
    · exact fun _ hx => hx
    · next hf =>
        cases hn (by constructor)
        exfalso
        apply hf
        rfl
    · exact join ihfn ihe
  | _ => repeat first | assumption | exact List.nil_subset _ | apply join
