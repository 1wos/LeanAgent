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
    let φ : ContDiffBump x₀ := ⟨δ₂ / 4, δ₂ / 2, by positivity, by linarith⟩
    let g : Y → V := fun x => φ x • f x₀
    have hg_test : IsTestFunction g :=
      IsTestFunction.smul_right ⟨φ.contDiff, φ.hasCompactSupport⟩ contDiff_const
    have key_integral := hg g hg_test
    simp only [g, inner_smul_right'] at key_integral
    have support_subset : Function.support φ ⊆ Metric.ball x₀ δ₂ :=
      φ.support_eq.subset.trans (Metric.ball_subset_ball (half_le_self hδ₂_pos.le))
    have supp_subset2 : Function.support (fun x => φ x * ⟪f x, f x₀⟫_ℝ) ⊆ Function.support φ := by
      intro x hprod hφ0
      simp [hφ0] at hprod
    have integrable_prod :
      Integrable (fun x => φ x * ⟪f x, f x₀⟫_ℝ) μ :=
      (Continuous.mul φ.continuous hinner_cont).integrable_of_hasCompactSupport
        (φ.hasCompactSupport.mono supp_subset2)
    have h_nonneg : ∀ x, 0 ≤ φ x * ⟪f x, f x₀⟫_ℝ := by
      intro x
      by_cases hx : x ∈ Function.support φ
      · exact mul_nonneg φ.nonneg (inner_pos_V (support_subset hx)).le
      · simp [Function.notMem_support.mp hx]
    have hμ_ball : 0 < μ (Metric.ball x₀ (δ₂/4)) :=
      Metric.isOpen_ball.measure_pos μ (Metric.nonempty_ball.mpr (by linarith))
    have hμ : 0 < μ (Metric.closedBall x₀ (δ₂/4)) :=
      lt_of_lt_of_le hμ_ball (measure_mono Metric.ball_subset_closedBall)
    have closedBall_subset_support :
        Metric.closedBall x₀ (δ₂/4)
          ⊆ Function.support (fun x => φ x * ⟪f x, f x₀⟫_ℝ) :=
        fun x hx => mul_ne_zero
          (φ.pos_of_mem_ball (Metric.closedBall_subset_ball (by show δ₂ / 4 < δ₂ / 2; linarith) hx)).ne'
          (inner_pos_V (Metric.closedBall_subset_ball (by linarith) hx)).ne'
    have integral_pos : 0 < ∫ x, φ x * ⟪f x, f x₀⟫_ℝ ∂μ :=
      (integral_pos_iff_support_of_nonneg h_nonneg integrable_prod).mpr
        (lt_of_lt_of_le hμ (measure_mono closedBall_subset_support))
    linarith
