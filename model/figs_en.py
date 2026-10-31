"""Figuras em inglês para o manuscrito (PharmacoEconomics - Open)."""
import os, numpy as np
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch
import analyses, psa
OUT = _os.path.join(_HERE, 'resultados', 'figuras')
_os.makedirs(OUT, exist_ok=True)
INK = '#0b0b0b'; INK2 = '#52514e'; GRID = '#e4e3df'; BLUE = '#2a78d6'; ORANGE = '#eb6834'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8})
k = FuncFormatter(lambda x, _: f'{x/1000:,.0f}')
def style(ax):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8); ax.grid(color=GRID, linewidth=0.6); ax.set_axisbelow(True)
LAB = {'disc': 'Discount rate', 'n_vials_override': 'Vials per course', 'smr': 'Standardised mortality ratio, cured survivors',
       'p_hsct_i': 'HSCT, blinatumomab group', 'c_salv': 'Relapse salvage episode cost', 'u_dec': 'Long-term survivor utility decrement',
       'vial': 'Vial price', 'p_hsct_c': 'HSCT, Interfant-06 group', 'u_ef': 'Event-free utility after treatment', 'c_hsct': 'HSCT cost',
       'frac_rel_i': 'Share of DFS events that are relapses, blinatumomab', 'u_pr': 'Post-relapse utility', 'u_int': 'Utility during intensive therapy',
       'c_ivig': 'IVIG cost', 'med_pr': 'Median post-relapse survival, years', 'c_int': 'Intensive-phase cost per cycle',
       'pB_salv_cycle': 'Salvage cost per cycle', 'pB_hsct': 'HSCT after relapse, share of treated', 'pB_cur': 'Relapses treated with curative intent', 'pB_eol_mult': 'End-of-life cost (×0 to ×2)'}

SUB = OUT
def save(fig, name):
    os.makedirs(SUB, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + '.png'))
    sub = {'Figure2_tornado': 'Fig2', 'Figure3_PSA': 'Fig3'}.get(name)
    if sub:
        fig.savefig(os.path.join(SUB, sub + '.tif'), dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
        fig.savefig(os.path.join(SUB, sub + '.pdf'))
def fmt(v):
    if abs(v) >= 20: return f'{v:,.0f}'
    return f'{v:.0f}' if float(v).is_integer() else f'{v:.2f}'
# Figure 2: tornado
d = analyses.owsa(True)[:12][::-1]; base = d[0]['base']
fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
for i, r in enumerate(d):
    lo, hi = r['nmb_low'], r['nmb_high']
    ax.barh(i, lo - base, left=base, height=0.62, color=BLUE, edgecolor='white', linewidth=1)
    ax.barh(i, hi - base, left=base, height=0.62, color=ORANGE, edgecolor='white', linewidth=1)
    left_val, right_val = (r['low'], r['high']) if lo < hi else (r['high'], r['low'])
    ax.text(min(lo, hi) - 6000, i, fmt(left_val), va='center', ha='right', fontsize=6.5, color=INK2)
    ax.text(max(lo, hi) + 6000, i, fmt(right_val), va='center', ha='left', fontsize=6.5, color=INK2)
ax.set_yticks(range(len(d))); ax.set_yticklabels([LAB[x['key']] for x in d], fontsize=7.5, color=INK)
ax.axvline(base, color=INK, linewidth=0.8); ax.axvline(0, color='#c0392b', linewidth=1.2)
ax.text(0, len(d) - 0.3, ' INMB = 0', color='#c0392b', fontsize=6.5, va='bottom')
ax.xaxis.set_major_formatter(k); ax.set_xlabel('Incremental net monetary benefit at R\\$40,000 per QALY (R\\$ thousands)', color=INK2)
lo_all = min(min(x['nmb_low'], x['nmb_high']) for x in d); hi_all = max(max(x['nmb_low'], x['nmb_high']) for x in d)
ax.set_xlim(-20000, hi_all + 70000); style(ax); ax.grid(axis='y', visible=False)
ax.legend(handles=[Patch(color=BLUE, label='Lower parameter value'), Patch(color=ORANGE, label='Upper parameter value')], loc='lower right', fontsize=7, frameon=False)
fig.tight_layout(); save(fig, 'Figure2_tornado'); plt.close(fig)
# Figure 3: CE plane + CEAC
res = np.load(_os.path.join(_HERE, 'resultados', 'psa_rho0.8.npy')); res0 = np.load(_os.path.join(_HERE, 'resultados', 'psa_rho0.0.npy'))
dc = res[:, 1] - res[:, 0]; dq = res[:, 3] - res[:, 2]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.4), dpi=300)
a1.scatter(dq, dc, s=3, color=BLUE, alpha=0.35, linewidths=0)
xs = np.array([0, max(7.5, dq.max() * 1.05)])
a1.plot(xs, 40000 * xs, color=INK, linewidth=1.2, label='R\\$40,000 per QALY')
a1.plot(xs, 120000 * xs, color=INK2, linewidth=1.0, linestyle=(0, (4, 3)), label='R\\$120,000 per QALY (illustrative)')
a1.axhline(0, color=INK2, linewidth=0.6)
a1.set_xlim(0, xs[1]); lim = max(abs(dc).max() * 1.15, 60000); a1.set_ylim(-lim * 0.5, lim)
a1.yaxis.set_major_formatter(k); a1.set_xlabel('Incremental QALYs', color=INK2); a1.set_ylabel('Incremental cost (R\\$ thousands)', color=INK2)
a1.legend(fontsize=6.5, frameon=False, loc='upper right'); style(a1); a1.set_title('a', loc='left', fontweight='bold', fontsize=9)
grid = np.linspace(0, 150000, 151)
a2.plot(grid, psa.ceac(res, grid), color=BLUE, linewidth=2, label='Base case (DFS-OS correlation 0.8)')
a2.plot(grid, psa.ceac(res0, grid), color=ORANGE, linewidth=1.4, linestyle=(0, (4, 3)), label='Independent DFS and OS draws')
a2.axvline(40000, color=INK2, linewidth=0.8, linestyle=':'); a2.text(41500, 0.5, 'R\\$40,000', fontsize=6.5, color=INK2)
a2.set_ylim(0, 1.02); a2.xaxis.set_major_formatter(k); a2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0%}'))
a2.set_xlabel('Willingness to pay (R\\$ thousands per QALY)', color=INK2); a2.set_ylabel('Probability cost-effective', color=INK2)
a2.legend(fontsize=6.5, frameon=False, loc='lower right'); style(a2); a2.set_title('b', loc='left', fontweight='bold', fontsize=9)
fig.tight_layout(); save(fig, 'Figure3_PSA'); plt.close(fig)
# ESM: convergence
n = np.arange(1, len(dc) + 1); nmb = 40000 * dq - dc
run_mean = np.cumsum(nmb) / n; run_p = np.cumsum(nmb > 0) / n
fig, (b1, b2) = plt.subplots(1, 2, figsize=(7.2, 3.0), dpi=300)
b1.plot(n, run_mean, color=BLUE, linewidth=1.2); b1.axhline(run_mean[-1], color=INK2, linewidth=0.6, linestyle=':')
b1.yaxis.set_major_formatter(k); b1.set_xlabel('Number of simulations', color=INK2); b1.set_ylabel('Running mean INMB (R\\$ thousands)', color=INK2); style(b1)
b1.set_title('a', loc='left', fontweight='bold', fontsize=9)
b2.plot(n, run_p, color=BLUE, linewidth=1.2); b2.set_ylim(0.95, 1.001)
b2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0%}'))
b2.set_xlabel('Number of simulations', color=INK2); b2.set_ylabel('Running probability cost-effective', color=INK2); style(b2)
b2.set_title('b', loc='left', fontweight='bold', fontsize=9)
fig.tight_layout(); save(fig, 'FigureS2_convergence'); plt.close(fig)
rel = abs(run_mean[999] / run_mean[-1] - 1), abs(run_mean[2499] / run_mean[-1] - 1)
print('convergence: |mean@1000/mean@5000-1|=%.4f, @2500=%.4f; final %.0f' % (rel[0], rel[1], run_mean[-1]))
