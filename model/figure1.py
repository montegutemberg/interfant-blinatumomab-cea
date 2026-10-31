"""Figura 1: (a) ocupação dos estados no braço Interfant-06; (b) curvas Gompertz ajustadas contra as estimativas
atuariais reconstruídas dos números em risco (Vieira Martins 2026), com os valores publicados aos 4 anos.
Recriado em 26/10/2026 para reprodutibilidade (o script original da figura submetida não foi preservado);
reproduz o mesmo conteúdo da Fig. 1 submetida."""
import os, csv, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import model
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'resultados', 'figuras')
cv = model.curve_set('gompertz'); t = np.linspace(0, 10, 501)
S = {k: model.surv(*cv[k], t) for k in cv}
os_c = np.maximum(S['os_c'], S['dfs_c'])
BLUE, ORANGE, GREY, GOLD, SKY = '#1f77b4', '#d95f02', '#e6e6e6', '#e6a817', '#6cb8e6'
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.3), dpi=300)
a1.fill_between(t, 0, S['dfs_c'], color=SKY); a1.fill_between(t, S['dfs_c'], os_c, color=GOLD); a1.fill_between(t, os_c, 1, color=GREY)
a1.plot(t, os_c, 'k-', lw=1.2); a1.plot(t, S['dfs_c'], 'k--', lw=1.2)
a1.text(1.5, 0.2, 'Event-free', fontsize=7); a1.text(5.5, 0.48, 'Post-relapse', fontsize=7); a1.text(2.5, 0.85, 'Death', fontsize=7)
a1.set_xlim(0, 10); a1.set_ylim(0, 1); a1.set_xlabel('Years since start of post-induction treatment', fontsize=7)
a1.set_ylabel('Proportion of cohort', fontsize=7); a1.set_title('a', loc='left', fontweight='bold', fontsize=9)
PUB = {'dfs_c': 0.440, 'os_c': 0.602, 'dfs_i': 0.833, 'os_i': 0.933}
STY = {'dfs_c': (ORANGE, '-', 'Interfant-06, DFS'), 'os_c': (ORANGE, '--', 'Interfant-06, OS'),
       'dfs_i': (BLUE, '-', 'Blinatumomab, DFS'), 'os_i': (BLUE, '--', 'Blinatumomab, OS')}
for k, (c, ls, lab) in STY.items():
    tb = np.array([[float(x) for x in r] for r in list(csv.reader(open(os.path.join(HERE, 'R', 'dados', 'reais', f'{k}_tabela.csv'))))[1:]])
    tt, n, ca = tb.T; cens = np.diff(ca); ev = n[:-1] - n[1:] - cens
    s = np.concatenate([[1], np.cumprod(1 - ev / np.maximum(n[:-1] - cens / 2, 1e-9))])
    a2.step(tt, s, where='post', color=c, lw=0.7, alpha=0.35)
    a2.plot(t, S[k], color=c, ls=ls, lw=1.3, label=lab); a2.plot(4, PUB[k], 'o', color=c, ms=3)
a2.axvline(7, color='grey', ls=':', lw=0.8); a2.text(3.2, 0.03, 'observed', fontsize=6, ha='center'); a2.text(8.5, 0.03, 'extrapolated', fontsize=6, ha='center')
a2.set_xlim(0, 10); a2.set_ylim(0, 1.02); a2.set_xlabel('Years since start of post-induction treatment', fontsize=7)
a2.set_ylabel('Survival probability', fontsize=7); a2.legend(fontsize=6, frameon=False, loc='lower left', bbox_to_anchor=(0, 0.08))
a2.set_title('b', loc='left', fontweight='bold', fontsize=9)
for ax in (a1, a2): ax.tick_params(labelsize=6.5)
os.makedirs(OUT, exist_ok=True); fig.tight_layout(); fig.savefig(os.path.join(OUT, 'Figure1_model_fit_reproduzida.png')); print('ok')
