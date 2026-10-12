lemma fundamental_theorem_of_variational_calculus' {f : Y → V}
    (μ : Measure Y) [IsFiniteMeasureOnCompacts μ] [μ.IsOpenPosMeasure]
    [OpensMeasurableSpace Y]
    (hf : Continuous f) (hg : ∀ g, IsTestFunction g → ∫ x, ⟪f x, g x⟫_ℝ ∂μ = 0) :
    f = 0 := by
    rw [funext_iff]; by_contra h₀
    obtain ⟨x₀, hx0⟩ := not_forall.1 h₀
    simp at hx0
    have hinner_cont : Continuous (fun x => ⟪f x, f x₀⟫_ℝ) :=
      Continuous.inner' (f : Y → V) (fun _ => f x₀) hf continuous_const
    obtain ⟨δ₂, hδ₂_pos, inner_pos_V⟩ :=
      Metric.isOpen_iff.1 (isOpen_lt continuous_const hinner_cont) x₀
        (real_inner_self_nonneg'.lt_of_ne' (mt inner_self_eq_zero'.1 hx0))
    let φ : ContDiffBump x₀ := ⟨δ₂ / 2, δ₂, half_pos hδ₂_pos, half_lt_self hδ₂_pos⟩
    have key_integral := hg _ (IsTestFunction.smul_right (g := fun _ => f x₀)
      ⟨φ.contDiff, φ.hasCompactSupport⟩ contDiff_const)
    simp only [inner_smul_right'] at key_integral
    refine ((φ.continuous.mul hinner_cont).integral_pos_of_hasCompactSupport_nonneg_nonzero
      φ.hasCompactSupport.mul_right (fun x => ?_) (mul_ne_zero
        (φ.support_eq.superset (Metric.mem_ball_self hδ₂_pos))
        (inner_pos_V (Metric.mem_ball_self hδ₂_pos)).ne')).ne' key_integral
    by_cases h : φ x = 0
    simp [h]
    exact mul_nonneg φ.nonneg (inner_pos_V (φ.support_eq.subset h)).le
