"""Figura S1: KM atuarial reconstruído (Vieira Martins 2026, Fig. 1B-D) e as 7 famílias ajustadas, 0-7 anos."""
import json, csv, os, numpy as np, matplotlib
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import model as M
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = _os.path.join(_HERE, 'resultados', 'figuras')
_os.makedirs(OUT, exist_ok=True)
CV = json.load(open(os.path.join(HERE, 'curves.json')))
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
TIT = {'dfs_c': 'Disease-free survival, Interfant-06', 'os_c': 'Overall survival, Interfant-06',
       'dfs_i': 'Disease-free survival, blinatumomab', 'os_i': 'Overall survival, blinatumomab'}
PUB = {'dfs_c': .440, 'os_c': .602, 'dfs_i': .833, 'os_i': .933}
FAM = [('gompertz', 'Gompertz', '#0072B2'), ('mixture_cure_weibull', 'Mixture cure', '#009E73'),
       ('gengamma', 'Generalised gamma*', '#E69F00'), ('lognormal', 'Log-normal', '#CC79A7'),
       ('loglogistic', 'Log-logistic', '#56B4E9'), ('weibull', 'Weibull', '#D55E00'), ('exponential', 'Exponential', '#555555')]
fig, axs = plt.subplots(2, 2, figsize=(10, 8.2))
tt = np.linspace(0.005, 7, 500)
for ax, ck, lab in zip(axs.flat, TIT, 'ABCD'):
    tb = np.array([[float(x) for x in r] for r in list(csv.reader(open(os.path.join(HERE, 'R/dados/reais', f'{ck}_tabela.csv'))))[1:]])
    t, n, ca = tb.T; cens = np.diff(ca); ev = n[:-1] - n[1:] - cens
    s = np.concatenate([[1], np.cumprod(1 - ev / (n[:-1] - cens / 2))])
    for f, nm, col in FAM:
        with np.errstate(all='ignore'):
            ax.plot(tt, M.surv(f, CV[ck][f]['params'], tt), color=col, lw=1.3, label=nm)
    ax.step(t, s, where='post', color='black', lw=2.2, label='Actuarial estimate (published numbers at risk)')
    ax.plot([4], [PUB[ck]], 'o', color='black', ms=8, label='Published 4-year estimate')
    ax.set(xlim=(0, 7), ylim=(0, 1.02), title=TIT[ck], xticks=range(8))
    ax.text(-0.13, 1.02, lab, transform=ax.transAxes, fontsize=14, fontweight='bold')
    ax.spines[['top', 'right']].set_visible(False)
for ax in axs[:, 0]: ax.set_ylabel('Survival probability')
for ax in axs[1]: ax.set_xlabel('Years')
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h[-2:] + h[:-2], l[-2:] + l[:-2], loc='lower center', bbox_to_anchor=(0.5, 0.025), ncol=3, frameon=False, fontsize=9)
fig.text(0.5, 0.005, '*Estimate at the boundary of the parameter space; not used in the scenario analysis.', ha='center', fontsize=8, style='italic')
fig.tight_layout(rect=(0, 0.12, 1, 1))
fig.savefig(os.path.join(OUT, 'FigureS1_seven_families.png'), dpi=300); print('ok')
