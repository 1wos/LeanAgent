#!/usr/bin/env python3
"""Check statistical formulas, joins, and saved result invariants."""
import json
import unittest

import numpy as np
import analyze as a


class StatisticalChecks(unittest.TestCase):
    def test_split_units_change_overlap(self):
        rows = [dict(hash='a',file='one'),dict(hash='a',file='one'),dict(hash='b',file='two')]
        record = a.overlap_experiment(rows,'record',np.random.default_rng(1))
        file = a.overlap_experiment(rows,'file',np.random.default_rng(1))
        self.assertAlmostEqual(record['row_conditional_expected_percent'],100*1.6/3)
        self.assertEqual(file['row_conditional_expected_percent'],0)

    def test_cross_file_clones_remain(self):
        rows = [dict(hash='a',file='one'),dict(hash='a',file='two')]
        self.assertAlmostEqual(a.overlap_experiment(rows,'file',np.random.default_rng(2))[
            'row_conditional_expected_percent'],80)

    def test_file_effect_removes_between_file_level(self):
        rows = [dict(hash=str(i),file='a' if i<2 else 'b',length=l,
                     heads={'simp':1} if i%2 else {}) for i,l in enumerate([9,19,99,199])]
        result = a.fixed_file_effect(rows,'simp',np.random.default_rng(1))
        self.assertAlmostEqual(result['raw']['ratio'],2)
        self.assertAlmostEqual(result['unique_weighted']['ratio'],2)

    def test_hash_weighting_invariant_to_copy_in_same_file(self):
        rows = [dict(hash=str(i),file='a',length=l,heads={'simp':1} if i%2 else {})
                for i,l in enumerate([9,19,29,99])]
        original = a.fixed_file_effect(rows,'simp',np.random.default_rng(1))
        repeated = a.fixed_file_effect(rows+[rows[1]]*20,'simp',np.random.default_rng(1))
        self.assertAlmostEqual(original['unique_weighted']['ratio'],repeated['unique_weighted']['ratio'])
        self.assertNotAlmostEqual(original['raw']['ratio'],repeated['raw']['ratio'])

    def test_saved_counts_and_reweighting(self):
        x=json.loads((a.HERE/'results.json').read_text())
        self.assertEqual(sum(r['n'] for r in x['profiles'].values()),323207)
        self.assertEqual(sum(r['ge200'] for r in x['profiles'].values()),48519)
        for s,r in x['split_experiments'].items():
            for cutoff,v in r.items():
                self.assertLessEqual(v['file']['row_conditional_expected_percent'],
                                     v['record']['row_conditional_expected_percent']+1e-9)
                if 'group' in v:
                    self.assertLessEqual(v['group']['row_conditional_expected_percent'],
                                         v['file']['row_conditional_expected_percent']+1e-9)
        for mode in ['raw','unique_weighted']:
            self.assertAlmostEqual(sum(x['length_standardized'][mode]['target_bin_weights']),1)
            for r in x['length_standardized'][mode]['sources'].values():
                self.assertTrue(all(0 <= v <= 100 for v in r['tactic_percent'].values()))
        for r in x['long_clone_audit'].values():
            self.assertEqual(r['n']-r['unique'],r['redundant_records'])

    def test_saved_inputs_unchanged(self):
        x=json.loads((a.HERE/'results.json').read_text())
        for path,want in x['inputs_sha256'].items():
            self.assertEqual(a.sha(a.ROOT/path),want,path)
        self.assertEqual(a.sha(a.HERE/'analyze.py'),x['code_sha256'])


if __name__=='__main__':
    unittest.main(verbosity=2)
