lemma fundamental_theorem_of_variational_calculus' {f : Y → V}
    (μ : Measure Y) [IsFiniteMeasureOnCompacts μ] [μ.IsOpenPosMeasure]
    [OpensMeasurableSpace Y]
    (hf : Continuous f) (hg : ∀ g, IsTestFunction g → ∫ x, ⟪f x, g x⟫_ℝ ∂μ = 0) :
    f = 0 := by
    ext x₀
    by_contra hx0
    have h0 := real_inner_self_nonneg'.lt_of_ne' (mt inner_self_eq_zero'.1 hx0)
    have hinner_cont := hf.inner' (𝕜 := ℝ) _ (fun _ => f x₀) continuous_const
    obtain ⟨φ, hs, hcs, hcd, hr, h1⟩ := exists_contDiff_tsupport_subset
      ((isOpen_lt continuous_const hinner_cont).mem_nhds h0)
    have key_integral := hg _ (IsTestFunction.smul_right (g := fun _ => f x₀)
      ⟨hcd, hcs⟩ contDiff_const)
    simp only [inner_smul_right'] at key_integral
    refine ((hcd.continuous.mul hinner_cont).integral_pos_of_hasCompactSupport_nonneg_nonzero
      hcs.mul_right (fun x => ?_) (mul_ne_zero
        (h1 ▸ one_ne_zero) h0.ne')).ne' key_integral
    by_cases h : x ∈ tsupport φ
    exact mul_nonneg (hr ⟨x, rfl⟩).1 (hs h).le
    simp [image_eq_zero_of_notMem_tsupport h]
