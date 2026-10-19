theorem bisimilarity_congr_choice :
    (p ~[lts (defs := defs)] q) → (choice p r) ~[lts (defs := defs)] (choice q r) := by
  intro h
  exists @ChoiceBisim _ _ defs, .choice h
  intro s1 s2 hr μ
  cases hr <;> grind [IsBisimulation, ChoiceBisim]
