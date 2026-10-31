"""Roda todas as análises e grava resultados/Resultados_modelo_Interfant.xlsx e as figuras 3 e 4.

Uso:  python run_all.py            (5.000 simulações no PSA)
      python run_all.py --quick    (500 simulações, para testes)
"""
import os, sys, json
import numpy as np
import inputs, model, analyses, psa

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'resultados'); os.makedirs(OUT, exist_ok=True)
NSIM = 500 if '--quick' in sys.argv else 5000

# manuscrito (tabela 4/5), para validação
MS = {'Caso-base': (10566, 5.374, 1966), 'Preço ao consumidor, R$21.095/frasco': (70449, 5.374, 13109),
      'PMVG com ICMS 17%': (21313, 5.374, 3966), 'PMVG, lista 2026': (12280, 5.374, 2285),
      'Maior compra pública observada': (16746, 5.374, 3116), 'Menor compra pública observada': (8878, 5.374, 1652),
      '6 frascos (28 µg úteis)': (19684, 5.374, 3663), 'Uso fracionado pleno, sem desperdício': (4365, 5.374, 812),
      '4 frascos (lactente de 3-4 meses)': (1447, 5.374, 269), 'Weibull': (12923, 5.456, 2369),
      'Mixture cure': (12916, 5.413, 2386), 'Gama generalizada': (4879, 5.896, 827), 'Log-normal': (12498, 5.443, 2296),
      'Sem excesso de mortalidade, SMR 1': (10670, 6.051, 1763), 'SMR 12': (10530, 5.131, 2052),
      'Utilidade uniforme 0,76': (10566, 5.694, 1856), 'TCTH pelo código SIGTAP isolado': (9330, 5.374, 1736),
      'TCTH por microcusteio': (16762, 5.374, 3119), 'Sem custos de toxicidade': (5413, 5.374, 1007),
      'Desconto 0%': (9059, 15.760, 575), 'Desconto 10%': (12668, 2.772, 4570), 'Horizonte 20 anos': (10291, 3.582, 2873),
      'Horizonte 10 anos': (10203, 1.873, 5447), 'Pior caso combinado (PMC + 6 frascos + microcusteio)': (97740, 5.374, 18187)}
APPROX = {'Mixture cure', 'Gama generalizada', 'Utilidade uniforme 0,76'}


def main():
    R = {}
    # caso-base
    for corr in (False, True):
        p, c, i, s = analyses.base_case(corr)
        R['base_corr' if corr else 'base_orig'] = dict(p=p, c=c, i=i, s=s)
    pb = R['base_corr']['p']; sb = R['base_corr']['s']
    R['scen_corr'] = analyses.scenarios(True)
    R['scen_orig'] = analyses.scenarios(False)
    R['owsa'] = analyses.owsa(True)
    R['cohort'] = analyses.incident_cohort(sb, pb)
    # PSA
    R['psa'] = {}
    for rho in (0.8, 0.0, 0.5, 0.95):
        res = psa.run(rho=rho, n=NSIM)
        np.save(os.path.join(OUT, f'psa_rho{rho}.npy'), res)
        R['psa'][rho] = dict(res=res, sum=psa.summarise(res))
        print(f'PSA rho={rho}: P(CE40k)={R["psa"][rho]["sum"]["p_ce_40000"]:.4f}', flush=True)
    import report
    report.write_xlsx(R, os.path.join(OUT, 'Resultados_modelo_Interfant.xlsx'), MS, APPROX)
    report.figures(R, OUT)
    s = sb
    print(f"Caso-base corrigido: dC {s['d_cost']:.0f}  dQ {s['d_qaly']:.3f}  RCEI {s['icer']:.0f}  BML {s['nmb']:.0f}")
    return R


if __name__ == '__main__':
    main()
