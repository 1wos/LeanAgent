theorem bisimilarity_congr_choice :
    (p ~[lts (defs := defs)] q) → (choice p r) ~[lts (defs := defs)] (choice q r) := by
  intro h
  refine ⟨ChoiceBisim, ChoiceBisim.choice h, ?_⟩
  rintro _ _ (h | h) μ
  · constructor <;> intro s t <;> cases t <;> rename_i t <;>
      try exact ⟨s, Tr.choiceR t, ChoiceBisim.bisim (HomBisimilarity.refl _)⟩
    · exact (h.follow_fst t).imp fun _ => And.imp Tr.choiceL ChoiceBisim.bisim
    · exact (h.follow_snd t).imp fun _ => And.imp Tr.choiceL ChoiceBisim.bisim
  · exact ⟨fun _ t => (h.follow_fst t).imp fun _ => And.imp_right ChoiceBisim.bisim,
      fun _ t => (h.follow_snd t).imp fun _ => And.imp_right ChoiceBisim.bisim⟩
