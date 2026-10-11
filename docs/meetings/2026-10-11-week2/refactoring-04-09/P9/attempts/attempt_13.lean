theorem bisimilarity_congr_choice :
    (p ~[lts (defs := defs)] q) → (choice p r) ~[lts (defs := defs)] (choice q r) := by
  intro h
  refine ⟨@ChoiceBisim _ _ defs, ChoiceBisim.choice h, ?_⟩
  rintro _ _ (h | h) μ
  · constructor <;> intro s t <;> cases t
    · exact (h.follow_fst ‹_›).imp fun _ => And.imp Tr.choiceL ChoiceBisim.bisim
    · exact ⟨s, Tr.choiceR ‹_›, ChoiceBisim.bisim (HomBisimilarity.refl _)⟩
    · exact (h.follow_snd ‹_›).imp fun _ => And.imp Tr.choiceL ChoiceBisim.bisim
    · exact ⟨s, Tr.choiceR ‹_›, ChoiceBisim.bisim (HomBisimilarity.refl _)⟩
  · grind [IsBisimulation, ChoiceBisim]
