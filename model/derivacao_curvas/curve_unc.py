"""Incerteza dos parâmetros Gompertz: dados anuais pseudo-individuais (n, eventos, censuras por intervalo)
gerados das curvas ajustadas; censura calibrada para que o IC95% de S(4) reproduza o IC publicado
(Vieira Martins, JCO 2026). Matriz de variância = inversa da informação observada (Hessiana numérica)."""
import numpy as np
from scipy.optimize import minimize, brentq
import psm

N = {'dfs_c': 214, 'os_c': 214, 'dfs_i': 30, 'os_i': 30}
CI4 = {'dfs_c': (0.440, 0.370, 0.508), 'os_c': (0.602, 0.530, 0.667),
       'dfs_i': (0.833, 0.645, 0.927), 'os_i': (0.933, 0.759, 0.983)}

def pseudo(curve, cens_scale):
    a, b = psm.BASE[curve]; n = N[curve]
    base = np.array([0, 0, 0.05, 0.15, 0.30, 0.45, 0.85]) if curve.endswith('_i') else np.array([0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30])
    cf = np.clip(base * cens_scale, 0, 0.98)
    rows = []; at = n
    for j in range(1, 8):
        s0, s1 = psm.gomp(j - 1, a, b), psm.gomp(j, a, b)
        c = at * cf[j - 1]
        d = (at - c / 2) * (1 - s1 / s0)          # actuarial: censura no meio do intervalo
        rows.append((j - 1, j, d, c)); at = at - d - c
    rows.append((7, 7, 0.0, at))   # em risco ao fim do seguimento: censura administrativa em 7 anos
    return rows

def to_ab(theta):
    """theta = (logit fração curada p, log(-a)); S(t) = p ** (1 - exp(a t))"""
    lp, la = np.asarray(theta[0]), np.asarray(theta[1])
    p = 1 / (1 + np.exp(-lp)); a = -np.exp(la); b = a * np.log(p)
    return a, b

def from_ab(a, b):
    p = np.exp(b / a); return np.array([np.log(p / (1 - p)), np.log(-a)])

def nll(theta, rows):
    a, b = to_ab(theta)
    ll = 0
    for t0, t1, d, c in rows:
        s0 = psm.gomp(t0, a, b); s1 = psm.gomp(t1, a, b); sm = psm.gomp((t0 + t1) / 2, a, b)
        ll += (d * np.log(max(s0 - s1, 1e-300)) if d > 0 else 0) + c * np.log(max(sm, 1e-300))
    return -ll

def hess(f, x, h=1e-4):
    x = np.asarray(x, float); k = len(x); H = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            e_i = np.eye(k)[i] * h; e_j = np.eye(k)[j] * h
            H[i, j] = (f(x + e_i + e_j) - f(x + e_i - e_j) - f(x - e_i + e_j) + f(x - e_i - e_j)) / (4 * h * h)
    return H

def fit(curve, cens_scale):
    rows = pseudo(curve, cens_scale)
    a, b = psm.BASE[curve]
    r = minimize(nll, from_ab(a, b), args=(rows,), method='Nelder-Mead', options={'xatol': 1e-8, 'fatol': 1e-10, 'maxiter': 20000})
    V = np.linalg.inv(hess(lambda th: nll(th, rows), r.x))
    return r.x, V, rows

def ci_width_s4(mean, V, nsim=20000, seed=1):
    rng = np.random.default_rng(seed)
    th = rng.multivariate_normal(mean, V, nsim)
    a, b = to_ab(th.T); s4 = psm.gomp(4, a, b)
    return np.percentile(s4, [2.5, 97.5])

def calibrate(curve):
    """escala de censura que iguala a largura do IC95% de S(4) à publicada (escala log-log)."""
    est, lo, hi = CI4[curve]
    target = np.log(-np.log(lo)) - np.log(-np.log(hi))
    def g(sc):
        m, V, _ = fit(curve, sc); l, h = ci_width_s4(m, V)
        return (np.log(-np.log(l)) - np.log(-np.log(h))) - target
    best = None
    for sc in np.linspace(0, 1.15, 24):
        try:
            v = g(sc)
        except Exception:
            continue
        if best is None or abs(v) < abs(best[1]): best = (sc, v)
    return best

if __name__ == '__main__':
    out = {}
    for cv in N:
        sc, err = calibrate(cv)
        m, V, rows = fit(cv, sc)
        l, h = ci_width_s4(m, V)
        at = [N[cv]];
        for r in rows[:-1]: at.append(at[-1] - r[2] - r[3])
        print(f'{cv}: censura x{sc:.2f}  IC95 S(4) simulado {l:.3f}-{h:.3f}  publicado {CI4[cv][1]}-{CI4[cv][2]}  '
              f'eventos {sum(r[2] for r in rows):.1f}  em risco/ano {[round(x,1) for x in at]}  -2logL {2*nll(m, rows):.2f}')
        out[cv] = dict(mean=m.tolist(), V=V.tolist(), cens=sc)
    import json; json.dump(out, open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'curve_unc.json'), 'w'), indent=1)
