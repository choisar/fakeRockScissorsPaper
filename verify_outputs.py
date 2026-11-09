"""Audit saved CSV, exact values, seeds, individual controls and source hashes."""
import csv
import hashlib
import json
from math import sqrt, isclose
from pathlib import Path
from random import Random
from analysis import summarize
from engine import GameConfig, play_game

ROOT = Path(__file__).parent


def verify(folder):
    data = json.loads((folder/'results.json').read_text(encoding='utf-8'))
    for name, digest in data['metadata']['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    maximum_z = 0
    for c in data['conditions']:
        n,m,k = c['players'],c['colluders'],c['catchers']
        with (folder/(c['id']+'.csv')).open(encoding='utf-8',newline='') as file:
            rows = [{key:float(value) for key,value in row.items()} for row in csv.DictReader(file)]
        assert len(rows) == c['trials']
        for i,row in enumerate(rows):
            assert row['game'] == i
            assert 0 <= row['survived_c'] <= m and 0 <= row['survived_n'] <= n-m
            assert row['survived_c'] + row['survived_n'] == n-k
            assert isclose(row['delta'],row['survived_c']/m-row['survived_n']/(n-m),abs_tol=1e-14)
        s = summarize(rows,n,m,k)
        for key in ['p_c','p_n','delta','standard_error']:
            assert isclose(s[key],c['stats'][key],abs_tol=1e-14)
        z = abs(s['delta']-c['exact']['delta']['value'])/s['standard_error']
        assert z < 6, (c['id'],z)
        maximum_z = max(maximum_z,z)
        baseline = (n-k)/n
        for rate in c['control_individual_survival']:
            assert abs(rate-baseline) < 6*sqrt(baseline*(1-baseline)/c['trials'])
        for i,rate in enumerate(c['individual_survival']):
            exact = c['exact']['p_c' if i<m else 'p_n']['value']
            assert abs(rate-exact) < 6*sqrt(exact*(1-exact)/c['trials'])
        rng = Random(c['seed']+':experiment')
        for row in rows[:100]:
            caught = play_game(GameConfig(n,m,k),rng)['catchers']
            assert row['survived_c'] == m-sum(p<m for p in caught)
    return dict(conditions=len(data['conditions']),games_per_arm=data['metadata']['trials'],
                maximum_exact_deviation_in_standard_errors=maximum_z,
                checks='CSV consistency; regenerated statistics; 100-game seed replay per condition; source hashes; individual rates within 6 SE of theory')


if __name__ == '__main__':
    result = {name:verify(ROOT/'outputs'/name) for name in ['main','seed-check']}
    draft = (ROOT/'APPLICATION_DRAFT.md').read_text(encoding='utf-8').split('## 본문\n\n')[1].split('\n\n## 수치 근거')[0]
    result['draft_characters_including_whitespace'] = len(draft)
    assert len(draft) <= 800
    (ROOT/'outputs'/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
