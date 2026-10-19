"""Build the 32 block combinations of the putnam_1995_a3 reference proof.

Each of the five blocks E, A, B, C, D is either the reference proof's own lines
or a short proof. The `have` statement lines are kept, so every combination
compiles. File name F15_EABCD: 1 = short proof, 0 = reference lines.

usage (from this folder):
  python make_variants.py              # imports used for the measured files
  python make_variants.py --full       # header `import Mathlib` instead
  python make_variants.py --tokens     # also print official-rule token counts
"""
import itertools, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(HERE, '..', 'local-v4.26')
R = open(os.path.join(LOCAL, 'P15_ref.lean'), encoding='utf-8').read().split('\n')
L = lambda a, b: R[a-1:b]          # 1-based inclusive
HEAD = R[:15]                      # imports .. statement line (line 15)
# header for this env: partial imports (same for all variants)
IMPORTS = """import Mathlib.RingTheory.Int.Basic
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Tactic.Ring
import Mathlib.RingTheory.Coprime.Lemmas
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Data.Nat.Prime.Basic
import Mathlib.Data.Int.GCD
import Mathlib.Util.CountHeartbeats
import Aesop""".split('\n')
if '--full' in sys.argv:
    IMPORTS = ['import Mathlib', 'import Aesop']
I4 = lambda s: [('    ' + x) if x.strip() else x for x in s.strip('\n').split('\n')]
KEY = I4("""have key : ∀ (x y : Fin 9 → ℤ) (i : Fin 9), digits_to_num (fun j => if j = i then y j else x j) = digits_to_num x + (y i - x i) * 10 ^ (i : ℕ) := fun x y i => by
  subst hdigits_to_num
  beta_reduce
  rw [show (y i - x i) * 10 ^ i.1 = ∑ j, if j = i then (y j - x j) * 10 ^ j.1 else 0 by simp, ← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl fun j _ => by split_ifs with h <;> [(subst h; ring); simp]
""")
A5 = I4("""have h₅ : ∀ (i : Fin 9), 7 ∣ (e i - d i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num d := fun i => by
  have := h₃ i
  rwa [key, add_comm] at this
""")
A6 = I4("""have h₆ : ∀ (i : Fin 9), 7 ∣ (f i - e i) * (10 : ℤ) ^ (i : ℕ) + digits_to_num e := fun i => by
  have := h₄ i
  rwa [key, add_comm] at this
""")
B7 = I4("""have h₇ : 7 ∣ digits_to_num e + digits_to_num d := by
  have hS := Finset.dvd_sum (s := .univ) fun i _ => h₅ i
  subst hdigits_to_num
  simp only [Finset.sum_add_distrib, sub_mul, Finset.sum_sub_distrib, Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul] at hS ⊢
  convert dvd_sub hS (dvd_mul_right 7 (∑ i : Fin 9, d i * 10 ^ (i : ℕ))) using 1
  push_cast
  ring
""")
C8 = I4("""have h₈ : ∀ (i : Fin 9), 7 ∣ (f i - d i) * (10 : ℤ) ^ (i : ℕ) := fun i => by
  convert dvd_sub (dvd_add (h₅ i) (h₆ i)) h₇ using 1
  ring
""")
D9 = I4("""have h₉ : ∀ (i : Fin 9), 7 ∣ d i - f i := fun i =>
  dvd_sub_comm.mp ((IsCoprime.pow_right ⟨3, -2, by norm_num⟩).dvd_of_dvd_mul_right (h₈ i))
""")
E_PRO = ["  intro d e f h",
         "  obtain ⟨-, h₃⟩ := (hrelation d e).mp h.1",
         "  obtain ⟨-, h₄⟩ := (hrelation e f).mp h.2"]
def build(E, A, B, C, D):
    body = []
    if A: body += KEY + A5 + [''] + A6
    else: body += L(27, 74) + [''] + L(76, 123)
    body += ['']
    body += B7 if B else L(125, 198)
    body += ['']
    body += C8 if C else L(200, 231)
    body += ['']
    body += D9 if D else L(233, 286)
    body += ['']
    if E:
        ded = [x[2:] if x.startswith('  ') else x for x in body]
        proof = E_PRO + [''] + ded + ['  exact h₉']
    else:
        proof = L(16, 25) + [''] + body + L(288, 291)
    stmt = R[9:15]   # 'theorem' .. ':= by'
    return '\n'.join(IMPORTS + ['', 'set_option maxHeartbeats 100000000', 'set_option Elab.async false', '',
                                '#count_heartbeats in'] + stmt + proof +
                     ['', '#print axioms putnam_1995_a3', ''])
OUT = os.path.join(HERE, 'variants')
os.makedirs(OUT, exist_ok=True)
names = []
for bits in itertools.product([0, 1], repeat=5):
    name = 'F15_' + ''.join(map(str, bits))   # order E A B C D
    open(os.path.join(OUT, name + '.lean'), 'w', encoding='utf-8', newline='\n').write(build(*bits))
    names.append(name)
print(f'wrote {len(names)} files to variants/')
if '--tokens' in sys.argv:
    sys.path.insert(0, os.path.join(LOCAL, 'tools'))
    from proof_tokens import proof_length
    stmt = open(os.path.join(LOCAL, 'tools', 'statement15.lean'), encoding='utf-8').read().rstrip('\n')
    for name in names:
        t = open(os.path.join(OUT, name + '.lean'), encoding='utf-8').read()
        t = t[t.index('theorem'):].split('#print axioms')[0]
        print(f'{name} {proof_length(t, stmt)}')
