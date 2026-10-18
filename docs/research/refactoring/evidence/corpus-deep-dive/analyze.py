#!/usr/bin/env python3
"""Read-only corpus experiments. Requires numpy; writes only beside this script.

Run from any directory: python3 analyze.py
No network, Lean invocation, model call, source extraction, or input modification.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = ROOT / 'corpus/results'
SEED = 20261018
SOURCES = ['strata', 'physlib', 'cslib', 'arklib', 'leanpool']
TACTICS = ['simp', 'rw', 'simp_all', 'grind', 'exact', 'apply', 'intro',
           'intros', 'induction', 'cases', 'ext', 'ring', 'norm_num',
           'omega', 'fun_prop', 'aesop', 'have', 'rfl']
MODELS = ['simp', 'rw', 'simp_all', 'grind', 'induction', 'omega', 'ring', 'aesop']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                      allow_nan=False) + '\n')


def pct(a, b):
    return float(100 * a / b) if b else None


def summary(values):
    x = np.asarray(values, dtype=float)
    return dict(n=len(x), mean=float(x.mean()), median=float(np.median(x)),
                p10=float(np.quantile(x, .1)), p90=float(np.quantile(x, .9)),
                min=float(x.min()), max=float(x.max())) if len(x) else {'n': 0}


def codes(values):
    mapping = {}
    return np.array([mapping.setdefault(v, len(mapping)) for v in values], dtype=int)


def overlap_experiment(rows, unit, rng, repeats=100):
    """Independent Bernoulli 80/20 splits; overlap conditional on test membership.

    Formula for each row: 1 - .2**(number of distinct units with its hash - 1).
    This is a row-conditional expectation, not E[ratio] for random test size.
    Simulations report the ratio for each nonempty test draw separately.
    """
    hashes = codes([r['hash'] for r in rows])
    units = np.arange(len(rows)) if unit == 'record' else codes([r[unit] for r in rows])
    by_hash = collections.defaultdict(set)
    for h, u in zip(hashes, units):
        by_hash[int(h)].add(int(u))
    unit_counts = np.array([len(by_hash[h]) for h in range(len(by_hash))])
    expected = 1 - .2 ** (unit_counts[hashes] - 1)
    sizes, rates = [], []
    for _ in range(repeats):
        test = rng.random(int(units.max()) + 1)[units] < .2
        if not test.any():
            continue
        train_present = np.bincount(hashes[~test], minlength=len(by_hash)) > 0
        rates.append(float(train_present[hashes[test]].mean() * 100))
        sizes.append(int(test.sum()))
    return dict(n=len(rows), units=int(units.max()) + 1,
                row_conditional_expected_percent=float(expected.mean() * 100),
                simulation=dict(repetitions=repeats, nonempty=len(rates),
                                mean_percent=float(np.mean(rates)),
                                p025_percent=float(np.quantile(rates, .025)),
                                p975_percent=float(np.quantile(rates, .975)),
                                test_size=summary(sizes)))


def fixed_file_effect(rows, tactic, rng, reps=400):
    """File fixed effects, one tactic indicator, y=log(1+length).

    Inverse within-source hash frequency weights make every proof string total
    weight one, retaining its file occurrences. Bootstrap resamples files.
    """
    files = codes([r['file'] for r in rows])
    x = np.array([tactic in r['heads'] for r in rows], dtype=float)
    y = np.log1p([r['length'] for r in rows])
    freq = collections.Counter(r['hash'] for r in rows)
    w_unique = np.array([1 / freq[r['hash']] for r in rows])
    answer = {'tactic': tactic, 'uses': int(x.sum()), 'n': len(rows)}
    for label, w in [('raw', np.ones(len(rows))), ('unique_weighted', w_unique)]:
        n = np.bincount(files, weights=w)
        nx = np.bincount(files, weights=w*x)
        ny = np.bincount(files, weights=w*y)
        nxy = np.bincount(files, weights=w*x*y)
        den = nx - nx*nx/n
        num = nxy - nx*ny/n
        mixed = den > 1e-9
        if not mixed.any():
            answer[label] = {'mixed_files': 0, 'ratio': None}
            continue
        numerator, denominator = num[mixed], den[mixed]
        beta = numerator.sum()/denominator.sum()
        z = {'mixed_files': int(mixed.sum()), 'ratio': float(np.exp(beta)),
             'log_coefficient': float(beta),
             'rows_in_mixed_files': int(np.isin(files, np.flatnonzero(mixed)).sum())}
        if label == 'unique_weighted' and mixed.sum() >= 5:
            boot = []
            for start in range(0, reps, 40):
                sample = rng.integers(0, len(numerator), (min(40, reps-start), len(numerator)))
                boot.extend(np.exp(numerator[sample].sum(axis=1)/denominator[sample].sum(axis=1)))
            z['file_bootstrap_95_percentile'] = [float(v) for v in np.quantile(boot, [.025, .975])]
            z['bootstrap_repetitions'] = reps
        answer[label] = z
    return answer


def main():
    rng = np.random.default_rng(SEED)
    previous_path = ROOT / 'reports/corpus-survey/analysis.json'
    previous = json.loads(previous_path.read_text())
    inputs = dict(previous['input_sha256'])
    for name, expected in inputs.items():
        assert sha(ROOT/name) == expected, name
    inputs[str(previous_path.relative_to(ROOT))] = sha(previous_path)
    lengths = {}
    length_count = 0
    for r in read_rows(RESULTS/'proof_lengths/lengths.jsonl.gz'):
        length_count += 1
        if r['proof_style'] == 'by' and not r['contains_sorry']:
            key = (r['source'], r['id'])
            assert key not in lengths
            lengths[key] = r
    all_rows, counts = [], collections.Counter()
    for r in read_rows(RESULTS/'all_sources/declarations.jsonl.gz'):
        counts[r['source']] += 1
        key = (r['source'], r['id'])
        if key not in lengths:
            continue
        v = lengths.pop(key)
        assert v['proof_sha256'] == r['proof_sha256']
        assert not r['contains_sorry']
        p = r['file_path'].split('/')
        group = p[1] if r['source'] == 'leanpool' and p[0] == 'LeanPool' else p[0]
        all_rows.append(dict(source=r['source'], id=r['id'], name=r['name'],
                             file=r['file_path'], group=group, hash=r['proof_sha256'],
                             length=v['proof_length'], heads=r['heads']))
    assert not lengths and len(all_rows) == 323207 and length_count == 380489
    by_source = {s: [r for r in all_rows if r['source'] == s] for s in SOURCES}
    for s in previous['sources']:
        assert counts[s['id']] == s['declarations']
        assert len(by_source.get(s['id'], [])) == s['eligible']
    print('Joined and verified 323,207 primary records.', flush=True)

    # 1. Profile shifts after proof-string weighting and long-proof selection.
    profiles = {}
    for s, rows in by_source.items():
        freq = collections.Counter(r['hash'] for r in rows)
        weights = np.array([1/freq[r['hash']] for r in rows])
        lens = np.array([r['length'] for r in rows])
        long = lens >= 200
        profile = {'n': len(rows), 'unique_strings': len(freq), 'ge200': int(long.sum()), 'tactics': {}}
        for t in TACTICS:
            uses = np.array([t in r['heads'] for r in rows])
            profile['tactics'][t] = dict(raw_percent=pct(uses.sum(), len(rows)),
                unique_weighted_percent=pct(weights[uses].sum(), weights.sum()),
                long_percent=pct(uses[long].sum(), long.sum()),
                long_unique_weighted_percent=pct(weights[uses & long].sum(), weights[long].sum()))
        profile['length'] = summary(lens)
        profiles[s] = profile

    # Common length distribution, equal source contribution; raw and unique weighted.
    edges = np.array([10, 25, 50, 100, 200])
    strata = {}
    for s, rows in by_source.items():
        b = np.searchsorted(edges, [r['length'] for r in rows], side='right')
        frequency = collections.Counter(r['hash'] for r in rows)
        w = np.array([1/frequency[r['hash']] for r in rows])
        strata[s] = (b, w)
    length_standardized = {'bins': ['<10', '10–24', '25–49', '50–99', '100–199', '≥200']}
    for mode in ['raw', 'unique_weighted']:
        weights_by_source = {s:(np.ones(len(rows)) if mode=='raw' else strata[s][1])
                             for s,rows in by_source.items()}
        masses = {s:np.bincount(strata[s][0],weights=weights_by_source[s],minlength=6)
                  for s in SOURCES}
        assert all((v > 0).all() for v in masses.values())
        target = np.mean([v/v.sum() for v in masses.values()],axis=0)
        standardized = {}
        for s,rows in by_source.items():
            w = weights_by_source[s]
            standardized[s] = {'bin_counts':np.bincount(strata[s][0],minlength=6).tolist(),
                'tactic_percent':{t:float(100*np.dot(target,
                    np.bincount(strata[s][0],weights=w*np.array([t in r['heads'] for r in rows]),minlength=6)/masses[s]))
                    for t in TACTICS}}
        length_standardized[mode] = {'target_bin_weights':target.tolist(), 'sources':standardized}

    # 2. Cross-source exact proof overlap, including a long-proof sensitivity.
    cross = {}
    for cutoff in [0, 200]:
        pop = [r for r in all_rows if r['length'] >= cutoff]
        sets = {s: {r['hash'] for r in pop if r['source'] == s} for s in SOURCES}
        cross[str(cutoff)] = []
        for i, a in enumerate(SOURCES):
            for b in SOURCES[i+1:]:
                shared = sets[a] & sets[b]
                affected_a = sum(r['hash'] in shared for r in pop if r['source'] == a)
                affected_b = sum(r['hash'] in shared for r in pop if r['source'] == b)
                examples = [dict(source=r['source'], id=r['id'], name=r['name'], file=r['file'],
                                 length=r['length'], proof_sha256=r['hash'])
                            for r in sorted(pop, key=lambda r: -r['length'])
                            if r['source'] in (a, b) and r['hash'] in shared][:8]
                cross[str(cutoff)].append(dict(a=a, b=b, shared_unique_strings=len(shared),
                    affected_a=affected_a, affected_b=affected_b,
                    jaccard_percent=pct(len(shared), len(sets[a] | sets[b])), examples=examples))

    # 3. Actual 80/20 split simulations; file and LeanPool project holdouts.
    split = {}
    for s, rows in by_source.items():
        split[s] = {}
        for cutoff in [0, 200]:
            pop = [r for r in rows if r['length'] >= cutoff]
            split[s][str(cutoff)] = {u: overlap_experiment(pop, u, rng)
                                    for u in ['record', 'file'] + (['group'] if s == 'leanpool' else [])}
    print('Completed exact-overlap and split experiments.', flush=True)

    # 4. Length associations before and after controlling for source/file/repeats.
    effects = {s: [fixed_file_effect(rows, t, rng) for t in MODELS]
               for s, rows in by_source.items()}
    print('Completed file bootstrap sensitivity experiments.', flush=True)

    # 5. LeanPool project heterogeneity and macro vs micro aggregation.
    lp_groups = collections.defaultdict(list)
    for r in by_source['leanpool']:
        lp_groups[r['group']].append(r)
    groups = []
    for group, rows in lp_groups.items():
        groups.append(dict(group=group, n=len(rows), unique_strings=len({r['hash'] for r in rows}),
                           files=len({r['file'] for r in rows}), length=summary([r['length'] for r in rows]),
                           ge200_percent=pct(sum(r['length'] >= 200 for r in rows), len(rows)),
                           tactic_percent={t:pct(sum(t in r['heads'] for r in rows),len(rows)) for t in TACTICS}))
    groups.sort(key=lambda r: -r['n'])
    substantial = [g for g in groups if g['n'] >= 100]
    macro = {t: float(np.mean([g['tactic_percent'][t] for g in substantial])) for t in TACTICS}
    covered = sum(g['n'] for g in substantial)
    micro_same_groups = {t:sum(g['n']*g['tactic_percent'][t] for g in substantial)/covered for t in TACTICS}
    hhi = sum((g['n']/len(by_source['leanpool']))**2 for g in groups)
    heterogeneity = dict(groups=groups, substantial_groups=len(substantial),
                         substantial_group_minimum=100, effective_group_count=1/hhi,
                         substantial_group_records=covered,
                         substantial_group_coverage_percent=pct(covered,len(by_source['leanpool'])),
                         micro_same_groups_tactic_percent=micro_same_groups,
                         macro_tactic_percent=macro,
                         median_across_substantial_groups=summary([g['length']['median'] for g in substantial]))

    # 6. Warm-up controls with matching source and proof length, no warm-up rows.
    warm_path = RESULTS/'warmup.json'
    inputs[str(warm_path.relative_to(ROOT))] = sha(warm_path)
    warmup = json.loads(warm_path.read_text())
    warm_names = {r['name'] for r in warmup}
    warm_hashes = {r['hash'] for r in all_rows if r['name'] in warm_names}
    matched = []
    for w in warmup:
        if w['source'] not in by_source or w['source'] == 'leanpool':
            continue
        selected = [r for r in by_source[w['source']] if r['name'] == w['name']]
        assert len(selected) == 1
        selected = selected[0]
        assert selected['length'] == w['official_proof_length']
        # Deduplicate eligible controls by exact proof string; deterministic order.
        candidates = {}
        for r in sorted(by_source[w['source']], key=lambda r: (r['file'],r['id'])):
            if r['name'] not in warm_names and r['hash'] not in warm_hashes and .5 <= r['length']/selected['length'] <= 2:
                candidates.setdefault(r['hash'], r)
        nearest = sorted(candidates.values(), key=lambda r: (abs(math.log(r['length']/selected['length'])), r['id']))[:50]
        assert len(nearest) >= 10
        matched.append(dict(number=w['number'], source=w['source'], length=selected['length'],
                            observed_heads=selected['heads'], controls=nearest))
    warm_results = {}
    for size in [20, 50]:
        samples = [rng.integers(0, min(size, len(m['controls'])), 20000) for m in matched]
        stats = []
        for t in TACTICS:
            observed = sum(t in m['observed_heads'] for m in matched)
            simulated = sum(np.array([t in r['heads'] for r in m['controls'][:size]])[idx]
                            for m, idx in zip(matched, samples))
            stats.append(dict(tactic=t, observed_of_12=observed,
                              matched_expected=float(simulated.mean()),
                              randomization_interval_95=[float(v) for v in np.quantile(simulated,[.025,.975])],
                              fraction_at_least_observed=float(np.mean(simulated >= observed))))
        warm_results[str(size)] = stats
    warm = dict(n=12, repetitions=20000, by_control_count=warm_results,
                control_definition='Same source, length ratio [0.5,2], nearest abs(log ratio); unique proof strings; known warm-up names and exact proof hashes excluded. Controls may repeat across different matched warm-ups.',
                matching_diagnostics=[dict(number=m['number'], source=m['source'], length=m['length'],
                    controls=len(m['controls']), length_min=min(r['length'] for r in m['controls']),
                    length_max=max(r['length'] for r in m['controls']),
                    ids=[r['id'] for r in m['controls']]) for m in matched])

    # 7. Confirm whether long repeats are shared proof bodies or full source snippets.
    long_lookup = {(r['source'],r['id']):r for r in all_rows if r['length'] >= 200}
    long_meta = []
    for s in SOURCES:
        path = RESULTS / f'warmup_candidates/{s}/ge200.jsonl.gz'
        inputs[str(path.relative_to(ROOT))] = sha(path)
        for r in read_rows(path):
            base = long_lookup.pop((s,r['id']))
            assert r['proof_sha256'] == hashlib.sha256(r['proof'].encode()).hexdigest() == base['hash']
            assert r['src_sha256'] == hashlib.sha256(r['src'].encode()).hexdigest()
            long_meta.append(dict(source=s, id=r['id'], name=r['name'], file=r['file_path'],
                                   group=base['group'], length=base['length'], proof_sha256=base['hash'],
                                   src_sha256=r['src_sha256'], source_link=r.get('source_link'),
                                   proof_preview=r['proof'][:400]))
    assert not long_lookup and len(long_meta) == 48519
    clone_results = {}
    for field in ['proof_sha256','src_sha256']:
        clusters = collections.defaultdict(list)
        for r in long_meta:
            clusters[r[field]].append(r)
        duplicates = [v for v in clusters.values() if len(v)>1]
        duplicates.sort(key=lambda v: (-len(v), -v[0]['length'], v[0]['id']))
        clone_results[field] = dict(n=len(long_meta), unique=len(clusters),
            redundant_records=sum(len(v)-1 for v in duplicates),
            records_in_repeated_clusters=sum(len(v) for v in duplicates),
            cross_source_clusters=sum(len({r['source'] for r in v})>1 for v in duplicates),
            cross_leanpool_group_clusters=sum(len({r['group'] for r in v if r['source']=='leanpool'})>1 for v in duplicates),
            largest_clusters=[dict(size=len(v), sources=sorted({r['source'] for r in v}),
                groups=sorted({r['group'] for r in v}), examples=v[:8]) for v in duplicates[:15]])
    print('Verified raw proof and full-declaration hashes for all 48,519 long candidates.', flush=True)

    out = dict(schema_version=1, analysis_date='2026-10-18', seed=SEED,
        runtime=dict(python=platform.python_version(), numpy=np.__version__),
        population='by proofs without direct sorry/admit; pinned snapshot; no semantic deduplication or Lean validation',
        inputs_sha256=inputs, code_sha256=sha(Path(__file__)),
        counts=dict(primary=323207, all_source_declarations=382121, exported_extra_warmup_references=3,
                    length_records=380489, long_candidates=48519),
        profiles=profiles, length_standardized=length_standardized,
        cross_source_overlap=cross, split_experiments=split,
        file_fixed_effects=effects, leanpool_heterogeneity=heterogeneity,
        warmup_matched=warm, long_clone_audit=clone_results,
        limitations=['Tactic counts are lexical detections, not Lean execution traces.',
                    'Exact proof strings or declaration snippets are not semantic theorem identity; context can differ.',
                    'Split overlap is a contamination proxy, not a measured model performance effect.',
                    'Fixed-file effects are associations; tactic selection and proof length are jointly determined.',
                    'File bootstrap is sensitivity to file composition, not a random sample confidence guarantee.',
                    'Warm-up matching is exploratory and has correlated/overlapping controls; no confirmatory p-values.',
                    'PutnamBench original has no eligible completed proofs; its three warm-ups excluded from comparisons.',
                    'No wall-clock, heartbeat, compilation, semantic validity or model generalization measurements.'])
    dump('results.json', out)
    dump('validation.json', dict(status='passed', joined_primary_records=323207,
          long_candidate_proof_and_src_hashes_verified=48519,
          expected_input_hashes_verified=5, source_counts_match=True,
          inputs_unchanged=all(sha(ROOT/name)==expected for name,expected in inputs.items()),
          outputs={'results.json':sha(HERE/'results.json')}))
    print('Saved results.json and validation.json', flush=True)


if __name__ == '__main__':
    main()
