import unittest
import contextlib
import io
import json
import tempfile
from argparse import Namespace
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
from itertools import product
from random import Random
from math import sqrt
from analysis import summarize, holm_adjust
from engine import GameConfig, play_game
from exact import expected_colluder_catchers, exact_summary, first_branches
from simulate import run
from verify_outputs import verify


@lru_cache(None)
def labelled_oracle(pool, colluders, k):
    """Small identity-labelled brute force; independent state representation."""
    if k == 0:
        return Fraction(0)
    if k == len(pool):
        return Fraction(sum(p < colluders for p in pool))
    choices = [(0,) if p < colluders and any(q >= colluders for q in pool)
               else (0,1,2) for p in pool]
    values = []
    for hands in product(*choices):
        losing = {(0,1):1,(0,2):0,(1,2):2}.get(tuple(sorted(set(hands))))
        if losing is None:
            continue
        losers = tuple(p for p,h in zip(pool,hands) if h == losing)
        if len(losers) >= k:
            value = labelled_oracle(losers,colluders,k)
        else:
            winners = tuple(p for p in pool if p not in losers)
            value = sum(p < colluders for p in losers) + labelled_oracle(winners,colluders,k-len(losers))
        values.append(value)
    return sum(values,Fraction(0))/len(values)


class ScriptedRandom:
    def __init__(self, values):
        self.values = iter(values)
    def randrange(self, stop):
        return next(self.values)


class ResearchTests(unittest.TestCase):
    def test_input_validation(self):
        for args in [(1,0,1),(4,-1,1),(4,5,1),(4,2,0),(4,2,4)]:
            with self.assertRaises(ValueError):
                GameConfig(*args)

    def test_exact_against_independent_labelled_enumeration(self):
        for n in range(2,7):
            for c in range(1,n):
                for k in range(1,n):
                    with self.subTest(n=n,c=c,k=k):
                        self.assertEqual(expected_colluder_catchers(c,n-c,k),
                                         labelled_oracle(tuple(range(n)),c,k))

    def test_hand_calculated_examples(self):
        # 3 players, 2 colluders, 1 catcher: noncolluder alone wins or loses
        # with equal conditional probability. When colluders lose they split risk.
        s = exact_summary(2,1,1)
        self.assertEqual(s['p_c']['fraction'],'3/4')
        self.assertEqual(s['p_n']['fraction'],'1/2')
        self.assertEqual(exact_summary(3,3,2)['delta']['fraction'],'1/6')
        self.assertEqual(exact_summary(2,2,2)['delta']['fraction'],'0')

    def test_deadlock_release_and_too_many_losers(self):
        result = play_game(GameConfig(3,2,1),ScriptedRandom([2,0,1]),trace=True)
        self.assertEqual(result['catchers'],[1])
        self.assertTrue(result['events'][1]['released'])
        self.assertEqual(result['events'][0]['next_pool'],[0,1])

    def test_too_few_losers(self):
        result = play_game(GameConfig(4,2,2),ScriptedRandom([1,0,2,0,1]),trace=True)
        self.assertEqual(len(result['catchers']),2)
        self.assertIn(2,result['catchers'])

    def test_seed_invariants_and_control(self):
        cfg = GameConfig(6,3,2)
        self.assertEqual(play_game(cfg,Random(42),True),play_game(cfg,Random(42),True))
        rng = Random(104)
        counts = [0]*6
        for _ in range(12000):
            caught = play_game(GameConfig(6,0,2),rng)['catchers']
            self.assertEqual(len(set(caught)),2)
            for p in caught:
                counts[p] += 1
        for count in counts:
            self.assertLess(abs(count/12000-1/3),6*sqrt((1/3)*(2/3)/12000))

    def test_simulation_matches_exact(self):
        for n,c,k in [(4,2,2),(6,2,2),(6,3,1)]:
            rng = Random(923)
            values = []
            for _ in range(12000):
                caught = play_game(GameConfig(n,c,k),rng)['catchers']
                sc = c-sum(p<c for p in caught)
                sn = n-c-sum(p>=c for p in caught)
                values.append(dict(survived_c=sc,survived_n=sn,delta=sc/c-sn/(n-c)))
            s = summarize(values,n,c,k)
            self.assertLess(abs(s['delta']-exact_summary(c,n-c,k)['delta']['value']),6*s['standard_error'])

    def test_game_level_standard_error_and_holm(self):
        rows = [dict(survived_c=2,survived_n=0,delta=1),dict(survived_c=0,survived_n=2,delta=-1)]
        self.assertEqual(summarize(rows,4,2,2)['standard_error'],1)
        self.assertEqual(holm_adjust([.01,.04,.03]),[.03,.06,.06])

    def test_normal_inference_against_hand_calculation(self):
        rows = [dict(survived_c=2, survived_n=0, delta=1),
                dict(survived_c=1, survived_n=1, delta=0)]
        stats = summarize(rows, 4, 2, 2)
        self.assertEqual(stats['delta'], .5)
        self.assertEqual(stats['standard_error'], .5)
        self.assertAlmostEqual(stats['ci95'][0], -.48)
        self.assertAlmostEqual(stats['ci95'][1], 1.48)
        self.assertAlmostEqual(stats['p_value_normal'], .31731050786291415)
        self.assertIsNone(stats['inference_reason'])

    def test_constant_samples_have_no_inference(self):
        for n, m, k, sc, sn in [(4, 2, 2, 1, 1), (4, 2, 2, 2, 0), (6, 3, 2, 3, 1)]:
            delta = sc/m-sn/(n-m)
            with self.subTest(delta=delta):
                rows = [dict(survived_c=sc, survived_n=sn, delta=delta)] * 7
                stats = summarize(rows, n, m, k)
                self.assertEqual(stats['standard_error'], 0)
                self.assertEqual(stats['delta'], delta)
                self.assertIsNone(stats['ci95'])
                self.assertIsNone(stats['p_value_normal'])
                self.assertEqual(stats['inference_reason'], 'zero_sample_variance')
        self.assertEqual(holm_adjust([.01, None, .04, .03]), [.04, None, .09, .09])
        self.assertEqual(holm_adjust([None, None]), [None, None])
        with self.assertRaises(ValueError):
            summarize([], 4, 2, 2)

    def test_draw_and_exact_quota_terminate_without_extra_throw(self):
        # First draw, then the noncolluder alone loses: no further RNG calls.
        result = play_game(GameConfig(3, 2, 1), ScriptedRandom([0, 1]), trace=True)
        self.assertEqual(result['catchers'], [2])
        self.assertFalse(result['events'][0]['terminal'])
        final = result['events'][-1]
        self.assertTrue(final['terminal'])
        self.assertIsNone(final['next_pool'])
        self.assertIn('선정 종료', final['action'])
        for c, n, k in [(2, 1, 1), (2, 1, 2)]:
            terminal = [b for b in first_branches(c, n, k) if b['losing_c']+b['losing_n'] == k]
            self.assertTrue(terminal)
            for branch in terminal:
                self.assertTrue(branch['terminal'])
                self.assertIsNone(branch['next_state'])
                self.assertEqual(branch['confirmed_c'], branch['losing_c'])


class SavedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temporary.name) / 'experiment'
        with contextlib.redirect_stdout(io.StringIO()):
            cls.data = run(Namespace(players=[3, 4], colluders=[2], catchers=[1, 2],
                                     trials=200, seed=23, output=cls.folder))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_saved_experiment_verifies(self):
        self.assertEqual(verify(self.folder)['conditions'], 4)

    def test_corrupted_statistics_exact_values_and_trace_are_rejected(self):
        cases = [
            ('ci95', lambda c: c['stats'].__setitem__('ci95', [999, 1000])),
            ('p_value_normal', lambda c: c['stats'].__setitem__('p_value_normal', .987654321)),
            ('p_value_holm', lambda c: c['stats'].__setitem__('p_value_holm', .987654321)),
            ('exact fraction', lambda c: c['exact']['delta'].__setitem__('fraction', '999')),
            ('exact value', lambda c: c['exact']['delta'].__setitem__('value', .999)),
            ('exact branches', lambda c: c['first_branches'][0].__setitem__('next_state', [99, 99, 99])),
            ('sample trace', lambda c: c['sample_game'].__setitem__('catchers', [])),
        ]
        file = self.folder / 'results.json'
        original = file.read_text(encoding='utf-8')
        try:
            for label, mutate in cases:
                with self.subTest(field=label):
                    data = json.loads(original)
                    mutate(data['conditions'][0])
                    file.write_text(json.dumps(data), encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, label):
                        verify(self.folder)
        finally:
            file.write_text(original, encoding='utf-8')

    def test_zero_variance_saved_sample_verifies(self):
        # Find a deterministic two-game constant sample using the real engine.
        for seed in range(20):
            rng = Random(f'{seed}:2:1:1:experiment')
            games = [play_game(GameConfig(2, 1, 1), rng)['catchers'] for _ in range(2)]
            if games[0] == games[1]:
                break
        else:
            self.fail('constant-sample fixture not found')
        folder = Path(self.temporary.name) / 'constant'
        with contextlib.redirect_stdout(io.StringIO()):
            data = run(Namespace(players=[2], colluders=[1], catchers=[1], trials=2, seed=seed, output=folder))
        stats = data['conditions'][0]['stats']
        self.assertIsNone(stats['p_value_holm'])
        self.assertIsNone(stats['ci95'])
        result = verify(folder)
        self.assertEqual(result['zero_variance_conditions'], ['n2_c1_k1'])
        self.assertIsNone(result['maximum_exact_deviation_in_standard_errors'])


if __name__ == '__main__':
    unittest.main()
