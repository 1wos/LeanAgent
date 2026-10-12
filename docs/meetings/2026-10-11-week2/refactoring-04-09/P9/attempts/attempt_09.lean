theorem bisimilarity_congr_choice :
    (p ~[lts (defs := defs)] q) → (choice p r) ~[lts (defs := defs)] (choice q r) := by
  intro h
  refine ⟨ChoiceBisim, ChoiceBisim.choice h, ?_⟩
  rintro _ _ (h | h) μ <;> refine (Bisimilarity.isBisimulation _ _ h μ).imp ?_ ?_ <;> intro f s t <;>
    first
    | exact (f _ t).imp fun _ => And.imp_right ChoiceBisim.bisim
    | cases t <;> rename_i t <;> first
      | exact (f _ t).imp fun _ => And.imp Tr.choiceL ChoiceBisim.bisim
      | exact ⟨s, Tr.choiceR t, ChoiceBisim.bisim (HomBisimilarity.refl _)⟩
