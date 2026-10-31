"""Análises: caso-base, cenários, sensibilidade univariada (BML), PSA e coorte incidente exploratória."""
import numpy as np
import inputs, model


def base_case(corrected=True, **over):
    p = inputs.base(corrected); p.update(over)
    c, i = model.run(p)
    return p, c, i, model.summary(c, i, p)


# ---------------- cenários (tabela 4 + novos)
def scenarios(corrected=True):
    b = inputs.base(corrected)
    S = [
        ('Caso-base', 'Base', {}),
        ('Preço ao consumidor, R$21.095/frasco', 'Preço e dose', {'vial': b['vial_pmc']}),
        ('PMVG com ICMS 17%', 'Preço e dose', {'vial': b['vial_icms17']}),
        ('PMVG, lista 2026', 'Preço e dose', {'vial': b['vial_2026']}),
        ('Maior compra pública observada', 'Preço e dose', {'vial': b['vial_bps_max']}),
        ('Menor compra pública observada', 'Preço e dose', {'vial': b['vial_bps_min']}),
        ('6 frascos (28 µg úteis)', 'Preço e dose', {'n_vials_override': 6}),
        ('Uso fracionado pleno, sem desperdício', 'Preço e dose', {'fractional_vials': True}),
        ('4 frascos (lactente de 3-4 meses)', 'Preço e dose', {'n_vials_override': 4}),
        ('Bolsa de 96 h, um frasco novo por bolsa (7 frascos)', 'Preço e dose', {'bag_hours': 96}),
        ('Bolsa de 48 h, um frasco novo por bolsa (14 frascos)', 'Preço e dose', {'bag_hours': 48}),
        ('Conta teórica do manuscrito (5 frascos, aproveitamento total)', 'Prática da farmácia', {'n_vials_override': 5}),
        ('Guia/HCPA A: 1a semana internado com bolsas de 24 h; depois 96 h em casa', 'Prática da farmácia', {'schedule': 'A'}),
        ('Guia/HCPA B: 3 dias internado (mínimo da bula); depois 96 h em casa', 'Prática da farmácia', {'schedule': 'B'}),
        ('Guia/HCPA C: 3 dias internado; depois 72 h em casa, preparadas em pares', 'Prática da farmácia', {'schedule': 'C'}),
        ('Guia/HCPA A com perda de uma bolsa (+1 frasco)', 'Prática da farmácia', {'schedule': 'A', 'lost_vials': 1}),
        ('Guia/HCPA A sem reaproveitar o frasco aberto', 'Prática da farmácia', {'schedule': 'A', 'sharing': 'none'}),
        ('Guia/HCPA D: bolsas de 24 h o ciclo inteiro (pior caso operacional)', 'Prática da farmácia', {'schedule': 'D'}),
        ('Weibull', 'Extrapolação', {'family': 'weibull'}),
        ('Mixture cure', 'Extrapolação', {'family': 'mixture_cure_weibull'}),
        ('Log-normal', 'Extrapolação', {'family': 'lognormal'}),
        ('Log-logística', 'Extrapolação', {'family': 'loglogistic'}),
        ('Sem excesso de mortalidade, SMR 1', 'Mortalidade e utilidade', {'smr': 1.0}),
        ('SMR 12', 'Mortalidade e utilidade', {'smr': 12.0}),
        ('Utilidade uniforme 0,76', 'Mortalidade e utilidade', {'uniform_utility': 0.76}),
        ('TCTH pelo código SIGTAP isolado', 'Custos', {'c_hsct': b['c_hsct_sigtap']}),
        ('TCTH por microcusteio', 'Custos', {'c_hsct': b['c_hsct_micro']}),
        ('Sem custos de toxicidade', 'Custos', {'no_tox': True}),
        ('Desconto 0%', 'Desconto e horizonte', {'disc': 0.0}),
        ('Desconto 10%', 'Desconto e horizonte', {'disc': 0.10}),
        ('Horizonte 20 anos', 'Desconto e horizonte', {'horizon': 20}),
        ('Horizonte 10 anos', 'Desconto e horizonte', {'horizon': 10}),
        ('Cura assumida a partir de 4 anos (fim do seguimento mediano)', 'Extrapolação', {'t_obs': 4.0}),
        ('Sobreviventes pós-recaída aos 7 anos passam a curados', 'Extrapolação', {'pr_cure': True}),
        ('Resgate com QT de 3ª linha', 'Custos', {'pB_salv_cycle': 800 + 16.8 * 552}),
        ('Pós-recaída: episódio fixo (alternativa A; resgate de 13 ciclos para todas as recaídas, sem TCTH nem fim de vida)', 'Pós-recaída', {'pathway_B': False}),
        ('Pós-recaída: versão anterior (R$700/ciclo, resgate líquido; histórico)', 'Pós-recaída', {'pathway_B': False, 'c_pr': 700.0, 'c_salv': 13 * (1381.76 + 16.8 * 552 - 700)}),
        ('Pós-recaída: intenção curativa 0,787 (sem conduta = suporte)', 'Pós-recaída', {'pB_cur': 159 / 202}),
        ('Pós-recaída: todas as recaídas com intenção curativa', 'Pós-recaída', {'pB_cur': 1.0}),
        ('Pós-recaída: TCTH em 40% dos tratados', 'Pós-recaída', {'pB_hsct': 0.40}),
        ('Pós-recaída: TCTH em 70% dos tratados', 'Pós-recaída', {'pB_hsct': 0.70}),
        ('Pós-recaída: sem custo de fim de vida', 'Pós-recaída', {'pB_eol_mult': 0.0}),
        ('Pós-recaída: custo de fim de vida dobrado', 'Pós-recaída', {'pB_eol_mult': 2.0}),
        ('Pós-recaída: 5 reavaliações medulares', 'Pós-recaída', {'pB_n_bm': 5}),
        ('Pós-recaída: acompanhamento trimestral', 'Pós-recaída', {'c_pr': b['pr_visit'] / 3}),
        ('QT pelos códigos genéricos do modelo original', 'Custos', {'c_int': 4703.76, 'c_maint': 500.0}),
        ('Sem decremento de sobrevivente', 'Mortalidade e utilidade', {'u_dec': 1.0}),
        ('Decremento de sobrevivente 0,94 (modelo original)', 'Mortalidade e utilidade', {'u_dec': 0.94}),
        ('Norma de utilidade e fim da manutenção calibrados (modelo original)', 'Mortalidade e utilidade', {'pop_norm': None, 'end_maint': 2.19222}),
        ('PMC + 6 frascos + TCTH pelo SIGTAP', 'Combinado',
         {'vial': b['vial_pmc'], 'n_vials_override': 6, 'c_hsct': b['c_hsct_sigtap']}),
        ('Pior caso: PMC + 14 frascos + TCTH pelo SIGTAP', 'Combinado',
         {'vial': b['vial_pmc'], 'bag_hours': 48, 'c_hsct': b['c_hsct_sigtap']}),
        ('Pior caso com preço de governo: PMVG ICMS 17% + 14 frascos + TCTH pelo SIGTAP', 'Combinado',
         {'vial': b['vial_icms17'], 'bag_hours': 48, 'c_hsct': b['c_hsct_sigtap']}),
        ('PMVG ICMS 17% + 7 frascos + TCTH pelo SIGTAP', 'Combinado',
         {'vial': b['vial_icms17'], 'bag_hours': 96, 'c_hsct': b['c_hsct_sigtap']}),
    ]
    out = []
    for name, group, over in S:
        p = dict(b, **over)
        c, i = model.run(p)
        s = model.summary(c, i, p)
        s.update(name=name, group=group, vials=model.vials_needed(p))
        out.append(s)
    return out


# ---------------- sensibilidade univariada na escala de BML
def owsa(corrected=True):
    b = inputs.base(corrected)
    R = [
        ('Taxa de desconto', 'disc', 0.0, 0.10),
        ('Preço do frasco (−10% a ICMS 17%)', 'vial', 0.9 * b['vial'], b['vial_icms17']),
        ('Frascos por curso', 'n_vials_override', 5, 9),
        ('SMR pós-cura', 'smr', 1.0, 12.0),
        ('Custo por ciclo de resgate', 'pB_salv_cycle', 0.75 * b['pB_salv_cycle'], 1.25 * b['pB_salv_cycle']),
        ('TCTH após recaída (proporção dos tratados)', 'pB_hsct', 0.40, 0.70),
        ('Intenção curativa após recaída', 'pB_cur', 159 / 202, 1.0),
        ('Custo de fim de vida (×0 a ×2)', 'pB_eol_mult', 0.0, 2.0),
        ('Custo do TCTH', 'c_hsct', b['c_hsct_sigtap'], b['c_hsct_micro']),
        ('Decremento de sobrevivente', 'u_dec', 0.927 if corrected else 0.88, 1.0),
        ('Utilidade livre de evento', 'u_ef', 0.68, 0.84),
        ('Utilidade em terapia intensiva', 'u_int', 0.55, 0.75),
        ('Utilidade pós-recaída', 'u_pr', 0.57, 0.77),
        ('Sobrevida mediana pós-recaída (anos)', 'med_pr', 1.0, 3.0),
        ('TCTH, braço blinatumomabe', 'p_hsct_i', 0.20, 0.50),
        ('TCTH, braço Interfant-06', 'p_hsct_c', 0.24, 0.36),
        ('Fração de eventos que são recaída, blinatumomabe', 'frac_rel_i', 0.60, 1.0),
        ('Custo da IVIg', 'c_ivig', 0.75 * b['c_ivig'], 1.25 * b['c_ivig']),
        ('Custo por ciclo da fase intensiva', 'c_int', 0.75 * b['c_int'], 1.25 * b['c_int']),
    ]
    base_nmb = model.summary(*model.run(b), b)['nmb']
    out = []
    for lab, k, lo, hi in R:
        r = []
        for v in (lo, hi):
            p = dict(b); p[k] = v
            r.append(model.summary(*model.run(p), p)['nmb'])
        out.append(dict(label=lab, key=k, low=lo, high=hi, nmb_low=r[0], nmb_high=r[1], base=base_nmb,
                        swing=abs(r[1] - r[0])))
    return sorted(out, key=lambda d: -d['swing'])


# ---------------- coorte incidente exploratória (não é análise de impacto orçamentário)
def incident_cohort(s, p):
    n = p['incident_infants']
    return dict(infants=n, drug_per_patient=p['vial'] * model.vials_needed(p),
                gross_drug=n * p['vial'] * model.vials_needed(p),
                net_lifetime=n * s['d_cost'])
