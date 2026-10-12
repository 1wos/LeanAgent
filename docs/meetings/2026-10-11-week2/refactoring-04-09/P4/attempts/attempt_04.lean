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
    have bump_exists : ∃ φ : Y → ℝ, IsTestFunction φ ∧
        (∀ x ∈ Function.support φ, 0 ≤ φ x) ∧
        Function.support φ ⊆ Metric.ball x₀ (δ₂/2) ∧
        (∀ x ∈ Metric.closedBall x₀ (δ₂/4), 0 < φ x) := by
          haveI : HasContDiffBump Y := hasContDiffBump_of_innerProductSpace Y
          let φ1 : ContDiffBump x₀ :=
            ⟨δ₂ / 4, δ₂ / 2, by positivity, by linarith⟩
          refine ⟨φ1.toFun, ⟨φ1.contDiff, φ1.hasCompactSupport⟩, fun x _ => φ1.nonneg,
            by rw [ContDiffBump.support_eq], fun x hx => φ1.pos_of_mem_ball ?_⟩
          rw [Metric.mem_closedBall] at hx
          exact Metric.mem_ball.mpr (lt_of_le_of_lt hx (by show δ₂ / 4 < δ₂ / 2; linarith))
    obtain ⟨φ, hφ_testfun, hφ_non_neg, hφ_support_subset, hφ_pos_inner⟩ :=
      bump_exists
    let g : Y → V := fun x => φ x • f x₀
    have hg_test : IsTestFunction g := IsTestFunction.smul_right hφ_testfun contDiff_const
    have key_integral := hg g hg_test
    simp only [g, inner_smul_right'] at key_integral
    have support_subset : Function.support φ ⊆ Metric.ball x₀ δ₂ :=
      hφ_support_subset.trans (Metric.ball_subset_ball (by linarith))
    have supp_subset2 : Function.support (fun x => φ x * ⟪f x, f x₀⟫_ℝ) ⊆ Function.support φ := by
      intro x hprod hφ0
      simp [hφ0] at hprod
    have integrable_prod :
      Integrable (fun x => φ x * ⟪f x, f x₀⟫_ℝ) μ :=
      (Continuous.mul hφ_testfun.smooth.continuous hinner_cont).integrable_of_hasCompactSupport
        (hφ_testfun.supp.mono supp_subset2)
    have h_nonneg : ∀ x, 0 ≤ φ x * ⟪f x, f x₀⟫_ℝ := by
      intro x
      by_cases hx : x ∈ Function.support φ
      · exact mul_nonneg (hφ_non_neg x hx) (inner_pos_V (support_subset hx)).le
      · simp [Function.notMem_support.mp hx]
    have hμ_ball : 0 < μ (Metric.ball x₀ (δ₂/4)) :=
      Metric.isOpen_ball.measure_pos μ (Metric.nonempty_ball.mpr (by linarith))
    have hμ : 0 < μ (Metric.closedBall x₀ (δ₂/4)) :=
      lt_of_lt_of_le hμ_ball (measure_mono Metric.ball_subset_closedBall)
    have closedBall_subset_support :
        Metric.closedBall x₀ (δ₂/4)
          ⊆ Function.support (fun x => φ x * ⟪f x, f x₀⟫_ℝ) :=
        fun x hx => mul_ne_zero (hφ_pos_inner x hx).ne'
          (inner_pos_V (Metric.closedBall_subset_ball (by linarith) hx)).ne'
    have integral_pos : 0 < ∫ x, φ x * ⟪f x, f x₀⟫_ℝ ∂μ :=
      (integral_pos_iff_support_of_nonneg h_nonneg integrable_prod).mpr
        (lt_of_lt_of_le hμ (measure_mono closedBall_subset_support))
    linarith
