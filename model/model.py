"""Motor do modelo de sobrevida particionada (3 estados: livre de evento, pós-recaída, óbito).

Ocupação dos estados lida diretamente de duas curvas (DFS e OS) até o fim do período observado (7 anos).
Depois disso: sobreviventes livres de evento considerados curados, com mortalidade da população geral
(IBGE, tábua completa de 2024) multiplicada pelo SMR; pacientes pós-recaída com mortalidade em excesso (mediana pós-recaída).
"""
import json, os
import numpy as np
from scipy.stats import norm, gamma as G

HERE = os.path.dirname(os.path.abspath(__file__))
_qx = json.load(open(os.path.join(HERE, 'qx.json')))
QX = np.array([_qx[str(a)] for a in range(101)])          # tábua do modelo original (2022, interpolada); só para reproduzir o manuscrito antigo
_q24 = json.load(open(os.path.join(HERE, 'dados_fonte', 'qx_ibge_2024.json')))['qx']
QX24 = np.array([_q24[str(a)] for a in range(101)])        # IBGE, Tábua Completa de Mortalidade, Brasil 2024, ambos os sexos
# Norma populacional brasileira do EQ-5D-3L (Santos, Monteiro, Santos. Health Qual Life Outcomes 2021;19:162), por faixa etária.
# A amostra vai de 18 a 64 anos: abaixo de 18 usa-se o valor de 18-19; acima de 64, o de 60-64.
NORM_SANTOS = [(0, 0.873), (20, 0.876), (25, 0.859), (30, 0.850), (35, 0.834), (40, 0.817),
               (45, 0.801), (50, 0.765), (55, 0.762), (60, 0.761)]
_NL = np.array([a for a, _ in NORM_SANTOS]); _NV = np.array([v for _, v in NORM_SANTOS])
CURVES = json.load(open(os.path.join(HERE, 'curves.json')))


# ---------------- famílias paramétricas
def surv(family, params, t):
    t = np.asarray(t, float)
    p = params
    with np.errstate(all='ignore'):
        if family == 'gompertz':
            a, b = p; return np.exp(-(b / a) * np.expm1(a * t))
        if family == 'weibull':
            lam, k = p; return np.exp(-(t / lam) ** k)
        if family == 'exponential':
            return np.exp(-p[0] * t)
        if family == 'lognormal':
            mu, s = p; return np.where(t > 0, norm.sf((np.log(np.maximum(t, 1e-12)) - mu) / s), 1.0)
        if family == 'loglogistic':
            al, be = p; return 1 / (1 + (t / al) ** be)
        if family == 'mixture_cure_weibull':
            pi, lam, k = p; return pi + (1 - pi) * np.exp(-(t / lam) ** k)
        if family == 'gengamma':
            mu, sig, Q = p
            w = (np.log(np.maximum(t, 1e-12)) - mu) / sig; qq = Q ** -2; u = qq * np.exp(Q * w)
            s = G.sf(u, qq) if Q > 0 else G.cdf(u, qq)
            return np.where(t > 0, s, 1.0)
    raise ValueError(family)


def curve_set(family='gompertz'):
    return {k: (family, CURVES[k][family]['params']) for k in ('dfs_c', 'os_c', 'dfs_i', 'os_i')}


def pop_utility(age, p):
    if p.get('pop_norm') == 'santos2021':
        return _NV[np.searchsorted(_NL, np.asarray(age, float), side='right') - 1]
    return np.clip(p['pop_u0'] - p['pop_slope'] * np.maximum(age - 18, 0), 0, 1)


# Esquemas de bolsas para um ciclo de 28 dias (672 h). Cada grupo = bolsas preparadas juntas na mesma sessão.
# Regras do Guia Blincyto/bula ANVISA (04/11/2024): bolsa hospitalar 270 mL,
# ambulatorial 250 mL, infunde 240 mL; frasco reconstituído estável 24 h refrigerado (pode servir a mais de uma
# bolsa); bolsa pronta até 10 dias refrigerada incluindo a infusão; internação mínima nos 3 primeiros dias.
_H24, _A24, _A72, _A96 = (24, 'int'), (24, 'dom'), (72, 'dom'), (96, 'dom')
SCHEDULES = {
    'A': [[_H24]] * 7 + [[_A96]] * 5 + [[_A24]],                          # prática descrita pela farmácia
    'B': [[_H24]] * 3 + [[_A96]] * 6 + [[_A24]],                          # mínimo de internação do guia
    'C': [[_H24]] * 3 + [[_A72, _A72]] * 4 + [[_A24]],                    # 72 h em casa, preparadas em pares
    'D': [[_H24]] * 28,                                                   # pior caso operacional
    'E': [[_A96]] * 7,   # caso-base: cassetes de 96 h (250 mL, infunde 240 mL), cálculo usado para lactentes < 0,4 m²
}
PREP_ML = {'int': 270, 'dom': 250}


def vials_from_schedule(p, schedule, sharing='share24'):
    """Frascos por ciclo. sharing: 'share24' = saldo do frasco aberto usado em sessão até 24 h depois (prática HCPA);
    'none' = frascos novos a cada sessão; 'pool' = aproveitamento total (limite teórico)."""
    import math
    daily = p['dose_ug_m2_day'] * p['bsa']; ug = p['ug_usable_vial']
    t = 0.0; sessions = []
    for grp in schedule:
        tp = t; need = 0.0
        for h, s in grp:
            need += daily * h / 24 * PREP_ML[s] / 240; t += h
            assert t - tp <= 240 + 1e-9, 'bolsa preparada passaria de 10 dias'
        sessions.append((tp, need))
    assert abs(t - 672) < 1e-6
    if sharing == 'pool':
        return math.ceil(sum(x for _, x in sessions) / ug - 1e-9)
    if sharing == 'none':
        return sum(math.ceil(x / ug - 1e-9) for _, x in sessions)
    n = 0; rem = 0.0; t_open = -1e9
    for tp, need in sessions:
        if tp - t_open > 24 + 1e-9: rem = 0.0
        if rem >= need: rem -= need; continue
        need -= rem; k = math.ceil(need / ug - 1e-9); n += k; rem = k * ug - need; t_open = tp
    return n


def vials_needed(p):
    """Frascos por curso: esquema de bolsas (schedule), troca fixa (bag_hours) ou número fixo (n_vials)."""
    if p.get('n_vials_override') is not None:
        return p['n_vials_override']
    if p.get('fractional_vials'):
        return p['dose_ug_m2_day'] * p['bsa'] * 28 / p['ug_usable_vial']
    if p.get('bag_hours'):
        bags = int(np.ceil(28 * 24 / p['bag_hours']))
        dose_bag = p['dose_ug_m2_day'] * p['bsa'] * p['bag_hours'] / 24
        return bags * int(np.ceil(dose_bag / p['ug_usable_vial']))
    if p.get('schedule'):
        return vials_from_schedule(p, SCHEDULES[p['schedule']], p.get('sharing', 'share24')) + p.get('lost_vials', 0)
    if p.get('bag_hours'):
        bags = int(np.ceil(28 * 24 / p['bag_hours']))
        dose_bag = p['dose_ug_m2_day'] * p['bsa'] * p['bag_hours'] / 24
        return bags * int(np.ceil(dose_bag / p['ug_usable_vial']))
    if p.get('fractional_vials'):
        return p['dose_ug_m2_day'] * p['bsa'] * 28 / p['ug_usable_vial']
    return p['n_vials']


# ---------------- alternativa B: custo por recaída, condicionado ao momento da recaída (valor no instante da recaída)
def relapse_pathway_B(p, mu):
    """Custo esperado por recaída, descontado até o instante da recaída. s = tempo desde a recaída.
    Ramos (Driessen 2016): intenção curativa p_cur; destes, TCTH h após d_h anos; restante cuidados de suporte."""
    dt = p['dt']; r = p['disc']; D = lambda s: (1 + r) ** (-s)
    p_cur, h, d_h = p['pB_cur'], p['pB_hsct'], p['pB_hsct_delay']
    c_sc = p['pB_salv_cycle']                         # QT de 2ª linha + diárias, bruto (sem abater c_pr)
    k = np.arange(13); sk = (k + 0.5) * dt
    S = np.exp(-mu * sk)
    # resgate: TCTH-ramo recebe QT até o TCTH (vivo por definição); não-TCTH recebe 13 ciclos ponderados pela sobrevida
    w_pre = np.clip(d_h / dt - k, 0, 1)
    salv = p_cur * c_sc * (h * np.sum(w_pre * D(sk)) + (1 - h) * np.sum(S * D(sk)))
    hsct = p_cur * h * (p.get('pB_c_hsct') or p['c_hsct']) * D(d_h)
    # avaliação medular: diagnóstico da recaída (todos) + n_bm reavaliações nos curativos (ponderadas pela sobrevida aos 3 meses)
    bm = p['pB_c_dx'] + p_cur * p['pB_n_bm'] * p['pB_c_bm'] * np.exp(-mu * 0.25) * D(0.25)
    # fim de vida: todas as recaídas morrem no modelo (sem cura pós-recaída); densidade mu*exp(-mu s), desconto contínuo
    # curativos no 1º ano: internação terminal já nas diárias do resgate/TCTH → só UTI; demais: custo completo
    dl = np.log(1 + r); m = mu + dl
    e_in = mu / m * (1 - np.exp(-m)); e_out = mu / m * np.exp(-m)
    eol_cur = e_in * p['pB_eol_icu'] + e_out * p['pB_eol_full']
    eol_sup = (e_in + e_out) * p['pB_eol_full']
    eol = (p_cur * eol_cur + (1 - p_cur) * eol_sup) * p.get('pB_eol_mult', 1.0)
    return dict(salv=salv, hsct=hsct, bm=bm, eol=eol)


def eol_until(p, mu, T):
    """Custo de fim de vida por recaída contando só óbitos até T anos após a recaída (T = horizonte restante)."""
    r = p['disc']; dl = np.log(1 + r); m = mu + dl; T = np.maximum(np.asarray(T, float), 0)
    e_in = mu / m * (1 - np.exp(-m * np.minimum(1.0, T)))
    e_out = np.where(T > 1, mu / m * (np.exp(-m) - np.exp(-m * T)), 0.0)
    p_cur = p['pB_cur']
    return (p_cur * (e_in * p['pB_eol_icu'] + e_out * p['pB_eol_full'])
            + (1 - p_cur) * (e_in + e_out) * p['pB_eol_full']) * p.get('pB_eol_mult', 1.0)


# ---------------- um braço
def arm(p, dfs, os_, intervention):
    dt = p['dt']; n = int(round(p['horizon'] / dt))
    t = np.arange(n + 1) * dt
    age = p['age0'] + t
    S_d = surv(*dfs, t); S_o = np.maximum(surv(*os_, t), S_d)       # OS nunca abaixo de DFS
    k_obs = int(np.floor(min(p['t_obs'], p['horizon']) / dt))
    ef = S_d.copy(); rel = S_o - S_d
    qx = (QX24 if p.get('life_table') == 'ibge2024' else QX)[np.minimum(age.astype(int), 100)]
    h_bg = -np.log(1 - qx)
    mu = np.log(2) / p['med_pr']
    if k_obs < n:
        idx = np.arange(k_obs + 1, n + 1)
        q_cured = np.minimum(1.0, p['smr'] * qx[idx - 1])
        if p.get('pr_cure'):
            # cenário: quem está vivo após recaída no ponto de cura passa a ter o destino dos curados
            ef[k_obs + 1:] = (ef[k_obs] + rel[k_obs]) * np.cumprod((1 - q_cured) ** dt)
            rel[k_obs + 1:] = 0.0
        else:
            ef[k_obs + 1:] = ef[k_obs] * np.cumprod((1 - q_cured) ** dt)
            rel[k_obs + 1:] = rel[k_obs] * np.cumprod(np.exp(-(mu + h_bg[idx - 1]) * dt))
    # correção de meio ciclo na ocupação dos estados
    efm = (ef[:-1] + ef[1:]) / 2; relm = (rel[:-1] + rel[1:]) / 2; alm = efm + relm
    tm = t[:-1] + dt / 2; agem = p['age0'] + tm
    dm = (1 + p['disc']) ** (-tm)
    u_ef = np.where(tm < p['t_int'], p['u_int'],
                    np.where(tm < p['t_obs'], p['u_ef'], pop_utility(agem, p) * p['u_dec']))
    if p.get('uniform_utility') is not None:
        u_ef = np.where(tm < p['t_obs'], p['uniform_utility'], u_ef)
    qaly = np.sum((efm * u_ef + relm * p['u_pr']) * dt * dm)
    ly_d = np.sum(alm * dt * dm); ly_u = np.sum(alm * dt)
    # custos de estado (o pathway é o mesmo nos dois braços; o custo acumulado difere pela ocupação)
    cyc = np.arange(n)
    c_state = np.where(cyc < p['n_int_cycles'], p['c_int'], np.where(tm < p['end_maint'], p['c_maint'], 0.0))
    chemo = np.sum(efm * c_state * dm)
    fu = np.sum(efm * np.where(tm >= p['end_maint'], p['c_fu'], 0.0) * dm)
    pr = np.sum(relm * p['c_pr'] * dm)
    # recaídas: eventos de DFS no período observado x fração que é recaída; custo pontual (sem meio ciclo)
    frac = p['frac_rel_i'] if intervention else p['frac_rel_c']
    d_ev = np.maximum(S_d[:-1] - S_d[1:], 0) * (t[1:] <= p['t_obs'] + 1e-9)
    n_rel = np.sum(d_ev) * frac
    salv = np.sum(d_ev * frac * p['c_salv'] * (1 + p['disc']) ** (-t[1:]))
    # --- custos por evento ligados à recaída (desligados por padrão; alternativa B)
    rel_ev = d_ev * frac                                   # recaídas por ciclo (período observado)
    # sobreposição demonstrada com o resgate: componente do custo por ciclo que já está nas diárias do resgate,
    # descontado por recaída pelos ciclos em que o paciente está vivo durante o resgate (sobrevida pós-recaída)
    ov = p.get('pr_overlap_per_cycle', 0.0)
    if ov:
        alive = np.exp(-mu * (np.arange(13) + 0.5) * dt).sum()
        salv -= np.sum(rel_ev * ov * alive * (1 + p['disc']) ** (-t[1:]))
    # TCTH após a recaída: proporção das recaídas, custo unitário do TCTH, descontado no momento da recaída + atraso
    p_hr = p.get('p_hsct_relapse', 0.0)
    hsct_r = np.sum(rel_ev * p_hr * p.get('c_hsct_relapse', p['c_hsct'])
                    * (1 + p['disc']) ** (-(t[1:] + p.get('hsct_relapse_delay', 0.5)))) if p_hr else 0.0
    # fim de vida: mortes no estado pós-recaída = entradas por recaída + ocupação − ocupação seguinte
    c_eol = p.get('c_eol', 0.0)
    if c_eol:
        entries = np.zeros(n); entries[:] = rel_ev
        d_pr = np.maximum(rel[:-1] + entries - rel[1:], 0)
        eol = np.sum(d_pr * c_eol * (1 + p['disc']) ** (-t[1:]))
        n_pr_deaths = float(d_pr.sum())
    else:
        eol = 0.0; n_pr_deaths = float(np.maximum(rel[:-1] + rel_ev - rel[1:], 0).sum())
    if p.get('pathway_B'):
        pb = relapse_pathway_B(p, mu)
        dfac = (1 + p['disc']) ** (-t[1:])
        salv = float(np.sum(rel_ev * pb['salv'] * dfac)); hsct_r = float(np.sum(rel_ev * pb['hsct'] * dfac))
        eol = float(np.sum(rel_ev * eol_until(p, mu, p['horizon'] - t[1:]) * dfac)); bm = float(np.sum(rel_ev * pb['bm'] * dfac))
        salv += bm
    hsct = ((p['p_hsct_i'] if intervention else p['p_hsct_c']) * p['c_hsct'] * (1 + p['disc']) ** (-p['t_hsct'])
            if p['t_hsct'] <= p['horizon'] else 0.0)
    drug = p['vial'] * vials_needed(p) if intervention else 0.0
    tox = (p['p_ivig'] * p['c_ivig'] + p['p_gcsf'] * p['c_gcsf']) if (intervention and not p.get('no_tox')) else 0.0
    cost = drug + tox + chemo + hsct + salv + pr + fu + hsct_r + eol
    return dict(cost=cost, qaly=qaly, ly_d=ly_d, ly_u=ly_u, drug=drug, tox=tox, chemo=chemo, hsct=hsct,
                salv=salv, pr=pr, fu=fu, n_rel=n_rel, hsct_r=hsct_r, eol=eol, n_pr_deaths=n_pr_deaths)


def run(p, curves=None):
    cv = curves or curve_set(p.get('family', 'gompertz'))
    c = arm(p, cv['dfs_c'], cv['os_c'], False)
    i = arm(p, cv['dfs_i'], cv['os_i'], True)
    return c, i


def summary(c, i, p):
    dc = i['cost'] - c['cost']; dq = i['qaly'] - c['qaly']; dl = i['ly_d'] - c['ly_d']
    return dict(cost_c=c['cost'], cost_i=i['cost'], d_cost=dc, qaly_c=c['qaly'], qaly_i=i['qaly'], d_qaly=dq,
                ly_c=c['ly_d'], ly_i=i['ly_d'], d_ly=dl, lyu_c=c['ly_u'], lyu_i=i['ly_u'],
                icer=dc / dq if dq else float('nan'), icer_ly=dc / dl if dl else float('nan'),
                nmb=p['wtp'] * dq - dc, nmb_mod=p['wtp_mod'] * dq - dc,
                pct_ref=(dc / dq) / p['wtp'] if dq else float('nan'))
