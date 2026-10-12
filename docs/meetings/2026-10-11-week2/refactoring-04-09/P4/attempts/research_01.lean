lemma fundamental_theorem_of_variational_calculus' {f : Y → V}
    (μ : Measure Y) [IsFiniteMeasureOnCompacts μ] [μ.IsOpenPosMeasure]
    [OpensMeasurableSpace Y]
    (hf : Continuous f) (hg : ∀ g, IsTestFunction g → ∫ x, ⟪f x, g x⟫_ℝ ∂μ = 0) :
    f = 0 := by
  funext x
  have hle : borel Y ≤ _ := OpensMeasurableSpace.borel_le (α := Y)
  have hc : Continuous fun y => ⟪f y, f x⟫_ℝ := by fun_prop
  have h0 : (fun y => ⟪f y, f x⟫_ℝ) =ᵐ[μ] 0 := by
    refine ae_eq_of_ae_eq_trim (hm := hle) ?_
    letI : MeasurableSpace Y := borel Y
    haveI : BorelSpace Y := ⟨rfl⟩
    haveI : IsLocallyFiniteMeasure (μ.trim hle) := ⟨fun y => by
      obtain ⟨s, hy, ho, hs⟩ := μ.exists_isOpen_measure_lt_top y
      exact ⟨s, ho.mem_nhds hy, by rwa [trim_measurableSet_eq hle ho.measurableSet]⟩⟩
    refine ae_eq_zero_of_integral_contDiff_smul_eq_zero hc.locallyIntegrable fun g hgs hgc => ?_
    refine (integral_trim hle (hgs.continuous.smul hc).stronglyMeasurable).symm.trans ?_
    simpa [inner_smul_right'] using hg _ (IsTestFunction.smul_right ⟨hgs, hgc⟩ contDiff_const)
  exact inner_self_eq_zero'.1 (congrFun ((hc.ae_eq_iff_eq μ continuous_zero).1 h0) x)
