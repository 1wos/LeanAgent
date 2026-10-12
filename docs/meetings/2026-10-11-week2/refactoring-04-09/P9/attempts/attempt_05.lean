theorem bisimilarity_congr_choice :
    (p ~[lts (defs := defs)] q) → (choice p r) ~[lts (defs := defs)] (choice q r) := by
  intro h
  refine ⟨@ChoiceBisim _ _ defs, ChoiceBisim.choice h, ?_⟩
  rintro _ _ (h | h) μ
  · constructor <;> intro s t <;> cases t <;> rename_i t
    · obtain ⟨s', a, b⟩ := h.follow_fst t
      exact ⟨s', Tr.choiceL a, ChoiceBisim.bisim b⟩
    · exact ⟨s, Tr.choiceR t, ChoiceBisim.bisim (HomBisimilarity.refl _)⟩
    · obtain ⟨s', a, b⟩ := h.follow_snd t
      exact ⟨s', Tr.choiceL a, ChoiceBisim.bisim b⟩
    · exact ⟨s, Tr.choiceR t, ChoiceBisim.bisim (HomBisimilarity.refl _)⟩
  · constructor <;> intro s t
    · obtain ⟨s', a, b⟩ := h.follow_fst t
      exact ⟨s', a, ChoiceBisim.bisim b⟩
    · obtain ⟨s', a, b⟩ := h.follow_snd t
      exact ⟨s', a, ChoiceBisim.bisim b⟩
