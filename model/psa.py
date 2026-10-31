"""Análise de sensibilidade probabilística (PSA).

Curvas: os dois parâmetros Gompertz de cada curva [logit(fração curada), log(-a)] são sorteados juntos de uma
normal multivariada (decomposição de Cholesky). A matriz de variância vem da informação observada de dados
pseudoindividuais anuais, com censura calibrada para reproduzir o IC95% publicado de S(4) (Vieira Martins 2026).
DFS e OS do mesmo braço são ligadas por cópula gaussiana (rho); OS >= DFS é imposto por rejeição.
Demais parâmetros: beta para utilidades e proporções, gama para custos e parâmetros de longo prazo.
"""
import json, os
import numpy as np
import inputs, model

HERE = os.path.dirname(os.path.abspath(__file__))
U = json.load(open(os.path.join(HERE, 'curve_unc.json')))
_lg = lambda x: np.log(x / (1 - x))
# OS do blinatumomabe (2 óbitos): variância da fração curada tirada do IC95% publicado (75,9-98,3%)
U['os_i']['V'] = [[((_lg(0.983) - _lg(0.759)) / 3.92) ** 2, 0.0], [0.0, U['os_i']['V'][1][1]]]
U['os_i']['mean'][0] = _lg(0.9333)
L = {k: np.linalg.cholesky(np.array(v['V'])) for k, v in U.items()}
M = {k: np.array(v['mean']) for k, v in U.items()}


def to_ab(theta):
    lp, la = theta
    pc = 1 / (1 + np.exp(-lp)); a = -np.exp(la)
    return a, a * np.log(pc)


def _gamma(rng, mean, sd):
    k = (mean / sd) ** 2; return rng.gamma(k, mean / k)


SD = dict(smr=0.25, med_pr=0.25, vial=0.10, c_ivig=0.20, c_hsct=0.20, c_salv=0.20)   # DP relativo (pressuposto)


def draw_params(rng, b):
    p = dict(b)
    for k, rel in SD.items():
        p[k] = _gamma(rng, b[k], rel * b[k])
    p.update(u_int=rng.beta(65, 35), u_ef=rng.beta(76, 24), u_pr=rng.beta(67, 33), u_dec=rng.beta(*b.get('u_dec_beta', (94, 6))),
             p_hsct_c=rng.beta(64.2, 149.8), p_hsct_i=rng.beta(10, 20),
             frac_rel_c=rng.beta(0.886 * 122.6, 0.114 * 122.6), frac_rel_i=rng.beta(0.796 * 5, 0.204 * 5),
             p_ivig=rng.beta(19, 11), p_gcsf=rng.beta(5, 25))
    if b.get('pathway_B'):
        import inputs
        p.update(pB_cur=rng.beta(159, 32), pB_hsct=rng.beta(87, 72), pB_hsct_delay=_gamma(rng, b['pB_hsct_delay'], 0.07),
                 pB_salv_cycle=_gamma(rng, b['pB_salv_cycle'], 0.20 * b['pB_salv_cycle']),
                 c_pr=_gamma(rng, b['c_pr'], 0.25 * b['c_pr']),
                 pB_n_bm=rng.triangular(2, 3, 5),
                 pB_eol_days=_gamma(rng, b['pB_eol_days'], 3.0), pB_eol_icu_p=rng.beta(10.2, 13.8),
                 pB_eol_icu_days=_gamma(rng, b['pB_eol_icu_days'], 1.5))
        p['pB_eol_full'], p['pB_eol_icu'] = inputs.eol_costs(p)
    return p


def draw_arm(rng, dfs, os_, rho):
    tt = np.arange(1, 8.0)
    while True:
        z1 = rng.standard_normal(2); z2 = rho * z1 + np.sqrt(1 - rho ** 2) * rng.standard_normal(2)
        ad, bd = to_ab(M[dfs] + L[dfs] @ z1); ao, bo = to_ab(M[os_] + L[os_] @ z2)
        if np.all(model.surv('gompertz', (ao, bo), tt) >= model.surv('gompertz', (ad, bd), tt)):
            return ('gompertz', (float(ad), float(bd))), ('gompertz', (float(ao), float(bo)))


def run(rho=0.8, n=5000, seed=2026, corrected=True, **over):
    rng = np.random.default_rng(seed)
    b = inputs.base(corrected); b.update(over)
    out = np.zeros((n, 4))
    for s in range(n):
        p = draw_params(rng, b)
        dc, oc = draw_arm(rng, 'dfs_c', 'os_c', rho)
        di, oi = draw_arm(rng, 'dfs_i', 'os_i', rho)
        c, i = model.run(p, dict(dfs_c=dc, os_c=oc, dfs_i=di, os_i=oi))
        out[s] = [c['cost'], i['cost'], c['qaly'], i['qaly']]
    return out


def summarise(res, wtps=(40000, 120000)):
    dc = res[:, 1] - res[:, 0]; dq = res[:, 3] - res[:, 2]
    q = lambda x: (float(x.mean()), float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5)))
    out = dict(d_cost=q(dc), d_qaly=q(dq), p_qaly_neg=float((dq < 0).mean()), p_cost_saving=float((dc < 0).mean()))
    for w in wtps:
        nmb = w * dq - dc
        out[f'nmb_{w}'] = q(nmb); out[f'p_ce_{w}'] = float((nmb > 0).mean())
    return out


def ceac(res, grid):
    dc = res[:, 1] - res[:, 0]; dq = res[:, 3] - res[:, 2]
    return [float(((w * dq - dc) > 0).mean()) for w in grid]
