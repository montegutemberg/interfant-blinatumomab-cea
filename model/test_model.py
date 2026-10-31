"""Testes de consistência. Rodar: python test_model.py"""
import numpy as np
import inputs, model, analyses


def close(a, b, tol):
    return abs(a / b - 1) <= tol


def test_reproduces_manuscript():
    p, c, i, s = analyses.base_case(corrected=False)
    assert close(s['d_qaly'], 5.374, 0.005), s['d_qaly']
    assert close(s['d_cost'], 10566, 0.02), s['d_cost']
    assert close(s['icer'], 1966, 0.02), s['icer']
    assert close(c['ly_u'], 21.902, 0.01) and close(i['ly_u'], 40.684, 0.01)
    assert close(c['n_rel'], 0.517, 0.01) and close(i['n_rel'], 0.133, 0.01)


def test_ipca_correction():
    assert close(inputs.ipca_factor(2021), 1.0579 * 1.0462 * 1.0483, 1e-9)
    b = inputs.base(True)
    assert close(b['c_hsct'], 94254.25 * inputs.ipca_factor(2021), 1e-9)


def test_states_and_constraints():
    p = inputs.base(True)
    cv = model.curve_set('gompertz')
    t = np.arange(0, 7.01, 0.25)
    for arm in ('c', 'i'):
        # a OS ajustada do blinatumomabe fica até 2 pp abaixo da DFS nos primeiros 4 meses;
        # o modelo aplica OS >= DFS (como no manuscrito), então a ocupação pós-recaída nunca é negativa
        raw_gap = model.surv(*cv[f'dfs_{arm}'], t) - model.surv(*cv[f'os_{arm}'], t)
        assert raw_gap.max() < 0.025 and np.all(t[raw_gap > 1e-9] < 0.4)
    c, i = model.run(p)
    for r in (c, i):
        assert r['qaly'] > 0 and r['ly_d'] < r['ly_u']
        assert abs(sum(r[k] for k in ('drug', 'tox', 'chemo', 'hsct', 'salv', 'pr', 'fu', 'hsct_r', 'eol')) - r['cost']) < 1e-6


def test_vials():
    p = inputs.base(True)
    assert model.vials_needed(dict(p, bag_hours=96)) == 7
    assert model.vials_needed(dict(p, bag_hours=48)) == 14
    assert close(model.vials_needed(dict(p, fractional_vials=True)), 15 * 0.36 * 28 / p['ug_usable_vial'], 1e-9)
    assert [model.vials_needed(dict(p, schedule=s)) for s in 'ABCDE'] == [9, 8, 7, 14, 7]
    assert model.vials_needed(p) == 7


def test_threshold_reporting():
    p, c, i, s = analyses.base_case(True)
    assert s['nmb'] > 0 and s['icer'] < p['wtp']


if __name__ == '__main__':
    for name, f in list(globals().items()):
        if name.startswith('test_'):
            f(); print('ok ', name)
