theorem bisimilarity_congr_choice :
    (p ~[lts (defs := defs)] q) → (choice p r) ~[lts (defs := defs)] (choice q r) := by
  intro h
  exists @ChoiceBisim _ _ defs, .choice h
  intro s1 s2 hr μ
  cases hr
  case choice p q r h =>
    constructor
    · intro s' ht
      cases ht
      case choiceL ht =>
        obtain ⟨q', ht, hb⟩ := h.follow_fst ht
        exact ⟨q', .choiceL ht, .bisim hb⟩
      case choiceR ht =>
        refine ⟨s', .choiceR ht, .bisim ?_⟩
        apply HomBisimilarity.refl
    · intro s' ht
      cases ht
      case choiceL ht =>
        obtain ⟨p', ht, hb⟩ := h.follow_snd ht
        exact ⟨p', .choiceL ht, .bisim hb⟩
      case choiceR ht =>
        refine ⟨s', .choiceR ht, .bisim ?_⟩
        apply HomBisimilarity.refl
  case bisim h => grind [IsBisimulation, ChoiceBisim]
