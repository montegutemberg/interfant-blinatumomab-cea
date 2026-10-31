"""Reconstrução do modelo de sobrevida particionada (versão do manuscrito, Gompertz/JCO 2026).
Parâmetros-base: aba Inputs do Modelo.xlsx. Curvas: S(t) da aba Curvas, Gompertz recuperada exatamente."""
import json, numpy as np

QX = json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'qx.json')))
QX = np.array([QX[str(a)] for a in range(101)])

BASE = dict(
    age0=0.42, dt=0.07692, horizon=100, disc=0.05, t_obs=7.0,
    # Gompertz (a, b): S(t) = exp(-(b/a)(exp(a t) - 1))
    dfs_c=(-0.7822, 0.6890), os_c=(-0.6207, 0.3436),
    dfs_i=(-1.1408, 0.2086), os_i=(-7.9940, 0.5518),
    smr=8.0, med_pr=1.5,
    u_int=0.65, u_ef=0.76, u_pr=0.67, u_dec=0.94, t_int=2.0,
    vial=9118.23, n_vials=5, p_ivig=0.63, c_ivig=8009, p_gcsf=0.17, c_gcsf=630,
    c_int=4703.76, c_maint=500, c_fu=10, c_salv=121856.8, c_pr=700,
    frac_rel_c=0.886, frac_rel_i=0.796,
    c_hsct=94254.25, p_hsct_c=0.30, p_hsct_i=0.333, t_hsct=1.0,
    n_int_cycles=6, end_maint=2.19222,
    wtp=40000,
)

def gomp(t, a, b):
    return np.exp(-(b / a) * np.expm1(a * t))

def pop_utility(age):
    # norma populacional ajustada por idade (decai lentamente com a idade); parâmetro de calibração
    return np.clip(BASE_POP[0] - BASE_POP[1] * np.maximum(age - 18, 0), 0, 1)
BASE_POP = [0.9413, 0.004]   # calibrado para reproduzir 7,156 e 12,530 QALY

def arm(p, dfs_ab, os_ab, intervention):
    dt = p['dt']; n = int(round(p['horizon'] / dt))
    t = np.arange(n + 1) * dt
    age = p['age0'] + t
    dfs = gomp(t, *dfs_ab); os_ = np.maximum(gomp(t, *os_ab), dfs)
    k7 = int(np.floor(p['t_obs'] / dt))
    ef = dfs.copy(); rel = os_ - dfs
    qx = QX[np.minimum(age.astype(int), 100)]
    h_bg = -np.log(1 - qx)                       # hazard anual de fundo
    mu = np.log(2) / p['med_pr']
    idx = np.arange(k7 + 1, n + 1)
    qa = np.minimum(1.0, p['smr'] * qx[idx - 1])
    ef[k7 + 1:] = ef[k7] * np.cumprod((1 - qa) ** dt)
    rel[k7 + 1:] = rel[k7] * np.cumprod(np.exp(-(mu + h_bg[idx - 1]) * dt))
    alive = ef + rel
    # correção de meio ciclo (trapézio)
    efm = (ef[:-1] + ef[1:]) / 2; relm = (rel[:-1] + rel[1:]) / 2; alm = efm + relm
    tm = t[:-1] + dt / 2; agem = p['age0'] + tm
    dm = (1 + p['disc']) ** (-tm)
    # utilidades
    u_ef = np.where(tm < p['t_int'], p['u_int'], np.where(tm < p['t_obs'], p['u_ef'], pop_utility(agem) * p['u_dec']))
    qaly = np.sum((efm * u_ef + relm * p['u_pr']) * dt * dm)
    ly_d = np.sum(alm * dt * dm); ly_u = np.sum(alm * dt)
    # custos
    cyc = np.arange(n)
    c_state = np.where(cyc < p['n_int_cycles'], p['c_int'], np.where(tm < p['end_maint'], p['c_maint'], 0))
    chemo = np.sum(efm * c_state * dm)
    fu = np.sum(efm * np.where(tm >= p['end_maint'], p['c_fu'], 0) * dm)
    pr = np.sum(relm * p['c_pr'] * dm)
    frac = p['frac_rel_i'] if intervention else p['frac_rel_c']
    d_events = np.maximum(dfs[:-1] - dfs[1:], 0) * (t[1:] <= p['t_obs'] + 1e-9)
    n_rel = np.sum(d_events) * frac
    salv = np.sum(d_events * frac * p['c_salv'] * (1 + p['disc']) ** (-t[1:]))
    hsct = (p['p_hsct_i'] if intervention else p['p_hsct_c']) * p['c_hsct'] * (1 + p['disc']) ** (-p['t_hsct'])
    drug = p['vial'] * p['n_vials'] if intervention else 0
    tox = (p['p_ivig'] * p['c_ivig'] + p['p_gcsf'] * p['c_gcsf']) if intervention else 0
    cost = drug + tox + chemo + hsct + salv + pr + fu
    return dict(cost=cost, qaly=qaly, ly_d=ly_d, ly_u=ly_u, drug=drug, tox=tox, chemo=chemo, hsct=hsct,
                salv=salv, pr=pr, fu=fu, n_rel=n_rel)

def run(p=None, curves=None):
    p = dict(BASE, **(p or {}))
    cv = curves or dict(dfs_c=p['dfs_c'], os_c=p['os_c'], dfs_i=p['dfs_i'], os_i=p['os_i'])
    c = arm(p, cv['dfs_c'], cv['os_c'], False); i = arm(p, cv['dfs_i'], cv['os_i'], True)
    return c, i

if __name__ == '__main__':
    c, i = run()
    for k in c: print(f'{k:6s} {c[k]:12.3f} {i[k]:12.3f} {i[k]-c[k]:12.3f}')
    print('ICER', (i['cost'] - c['cost']) / (i['qaly'] - c['qaly']))
