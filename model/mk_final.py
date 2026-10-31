"""Grava final_numbers.json (números usados pelo manuscrito e pelo ESM) a partir do modelo e dos .npy do PSA."""
import json, numpy as np, analyses, psa, inputs
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
OUT = _os.path.join(_HERE, 'resultados', 'final_numbers.json')
def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return o
p, c, i, s = analyses.base_case(True)
N = dict(base=dict(p={k: v for k, v in p.items() if isinstance(v, (int, float, str, type(None)))}, c=c, i=i, s=s),
         scen=analyses.scenarios(True), owsa=analyses.owsa(True), cohort=analyses.incident_cohort(s, p))
res = {r: np.load(_os.path.join(_HERE, 'resultados', f'psa_rho{r}.npy')) for r in (0.8, 0.0, 0.5, 0.95)}
N['psa'] = psa.summarise(res[0.8])
grid = [0, 5000, 10000, 15000, 20000, 30000, 40000, 120000]
N['ceac'] = dict(zip([str(g) for g in grid], psa.ceac(res[0.8], grid)))
for r in (0.0, 0.5, 0.95): N[f'psa_rho{r}'] = psa.summarise(res[r])
json.dump(clean(N), open(OUT, 'w'))
print('ok', round(s['icer']), N['psa']['p_ce_40000'])
