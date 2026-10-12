lemma fundamental_theorem_of_variational_calculus' {f : Y → V}
    (μ : Measure Y) [IsFiniteMeasureOnCompacts μ] [μ.IsOpenPosMeasure]
    [OpensMeasurableSpace Y]
    (hf : Continuous f) (hg : ∀ g, IsTestFunction g → ∫ x, ⟪f x, g x⟫_ℝ ∂μ = 0) :
    f = 0 := by
  funext x
  have hle := ‹OpensMeasurableSpace Y›.borel_le
  have hc : Continuous fun y => ⟪f y, f x⟫_ℝ := by fun_prop
  refine inner_self_eq_zero'.1 (congrFun ((hc.ae_eq_iff_eq μ continuous_zero).1
    (ae_eq_of_ae_eq_trim (hm := hle) ?_)) x)
  letI := borel Y
  haveI : BorelSpace Y := ⟨rfl⟩
  haveI : IsLocallyFiniteMeasure (μ.trim hle) := ⟨fun y =>
    let ⟨s, hy, ho, hs⟩ := μ.exists_isOpen_measure_lt_top y
    ⟨s, ho.mem_nhds hy, trim_measurableSet_eq hle ho.measurableSet ▸ hs⟩⟩
  exact ae_eq_zero_of_integral_contDiff_smul_eq_zero hc.locallyIntegrable fun g hgs hgc =>
    (integral_trim hle (hgs.continuous.smul hc).stronglyMeasurable).symm.trans
      (by simpa [inner_smul_right'] using hg _ (.smul_right ⟨hgs, hgc⟩ contDiff_const))
