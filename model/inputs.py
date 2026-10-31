"""Inputs do modelo, com fonte, ano de valoração e status de cada um.

Cada parâmetro tem:
  value      valor usado no caso-base
  unit       unidade
  source     referência específica
  year       ano de valoração monetária (só para custos), usado na correção pelo IPCA
  status     'ok' = documentado no manuscrito/planilha; 'premissa' = valor assumido ou calibrado (testado em cenário);
             'pendente' = falta referência específica
"""

# IPCA anual (dez/dez), IBGE. Usado para levar custos de outros anos a reais de 2024.
IPCA_2026_JAN_SET = 0.039513   # IPCA jan-set/2026 (variações mensais; conferir no IBGE)
IPCA = {2020: 0.0452, 2021: 0.1006, 2022: 0.0579, 2023: 0.0462, 2024: 0.0483, 2025: 0.0426}   # 2025: IBGE, divulgado em 09/01/2026
COST_YEAR = 2024


def ipca_factor(year, to=COST_YEAR):
    f = 1.0
    for y in range(year + 1, to + 1):
        f *= 1 + IPCA[y]
    return f


P = {}


def add(key, value, unit, source, status='ok', year=None, note=''):
    P[key] = dict(value=value, unit=unit, source=source, status=status, year=year, note=note)


# ---------------- Estrutura
add('age0', 0.42, 'anos', 'Mediana de 5 meses ao diagnóstico; Vieira Martins et al., J Clin Oncol 2026')
add('dt', 4 / 52, 'anos', 'Ciclos de 4 semanas, cadência do Interfant-06 (Pieters et al., J Clin Oncol 2019)')
add('horizon', 100, 'anos', 'Horizonte vitalício; Diretriz de Avaliação Econômica, MS 2025')
add('disc', 0.05, 'por ano', 'Diretriz de Avaliação Econômica em Saúde, 3a ed., MS 2025')
add('t_obs', 7.0, 'anos', 'Último tempo tabulado de números em risco; Vieira Martins et al., 2026')
add('family', 'gompertz', '', 'Menor AIC e BIC nas 4 curvas (tabela 3 do manuscrito)')

# ---------------- Sobrevida de longo prazo
add('smr', 8.0, 'razão', 'Excesso de mortalidade tardia em sobreviventes de LLA infantil (Childhood Cancer Survivor Study)',
    status='pendente', note='Citar o artigo específico da CCSS que dá o SMR 8')
add('med_pr', 1.5, 'anos', 'Sobrevida mediana pós-recaída em LLA do lactente', status='pendente',
    note='Na planilha consta apenas "Literatura"; indicar a referência (p. ex., Interfant-99/06 pós-recaída)')

# ---------------- Utilidades
add('u_int', 0.65, '', 'Utilidade em terapia intensiva (0-2 anos)', status='pendente', note='Indicar fonte publicada')
add('u_ef', 0.76, '', 'Livre de evento após o tratamento', status='pendente', note='Indicar fonte publicada')
add('u_pr', 0.67, '', 'Pós-recaída', status='pendente', note='Indicar fonte publicada')
add('u_dec', 0.94, 'multiplicador', 'Decremento de sobrevivente sobre a norma populacional', status='pendente', note='Indicar fonte')
add('t_int', 2.0, 'anos', 'Duração da terapia intensiva por protocolo (Interfant-06)')
add('pop_norm', 'santos2021', '', 'Norma populacional brasileira do EQ-5D-3L por faixa etária (Santos, Monteiro, Santos. Health Qual Life Outcomes 2021;19:162); 18-19 anos antes dos 18 e 60-64 após os 64',
    note='Substitui a norma calibrada (0,9413 − 0,004/ano), mantida só para reproduzir o manuscrito antigo')
add('life_table', 'ibge2024', '', 'IBGE, Tábua Completa de Mortalidade, Brasil 2024, ambos os sexos; 90-100 anos extrapolados (Gompertz, idades 80-89)')
add('pop_u0', 0.9413, '', 'Norma populacional de utilidade aos 18 anos', status='premissa',
    note='Norma calibrada da versão anterior; usada só no cenário de comparação (caso-base: norma brasileira, Santos 2021)')
add('pop_slope', 0.004, 'por ano', 'Queda anual da norma populacional após os 18 anos', status='premissa',
    note='Idem: calibrada; com 0,004/ano a utilidade aos 70 anos é cerca de 0,73')

# ---------------- Fármaco
add('vial', 9118.23, 'R$/frasco', 'CMED, PMVG com ICMS 0%, lista de 04/06/2024', year=2024)
add('schedule', 'E', '', 'Cassetes de 96 h com 250 mL (240 mL infundidos): cálculo de preparo para ASC < 0,4 m² (Princess Máxima Center, Stutterheim) adotado no tratamento de lactentes; um frasco por cassete, 7 por ciclo', status='premissa', note='Caso-base: 7 frascos por ciclo')
add('n_vials', 5, 'frascos/curso', '35 µg úteis por frasco (retirada de 2,8 mL); BSA 0,36 m²; 15 µg/m²/dia por 28 dias',
    status='premissa', note='Conta teórica da versão anterior; o caso-base usa o esquema de preparo (schedule)')
add('dose_ug_m2_day', 15, 'µg/m²/dia', 'Protocolo Interfant-06 + blinatumomabe (van der Sluis et al., N Engl J Med 2023)')
add('bsa', 0.36, 'm²', 'Mediana para lactente de 5 meses')
add('ug_usable_vial', 35, 'µg', 'Volume extraível de 2,8 mL a 12,5 µg/mL; bula ANVISA 04/11/2024 (Guia Blincyto)', note='A farmácia relata retirar até 3 mL na prática (37,5 µg); não muda a contagem de frascos nos esquemas testados')

# ---------------- Toxicidade
add('p_ivig', 0.63, 'proporção', 'Vieira Martins et al., J Clin Oncol 2026 (63% receberam IVIg)')
add('c_ivig', 8009, 'R$/paciente', 'Banco de Preços em Saúde, frasco de 5 g, 4 doses', year=2024, status='premissa',
    note='Ano das compras do BPS')
add('p_gcsf', 0.17, 'proporção', 'Vieira Martins et al., J Clin Oncol 2026 (17%)')
add('c_gcsf', 630, 'R$/paciente', 'Banco de Preços em Saúde, 300 µg', year=2024, status='premissa')

# ---------------- Custos assistenciais
add('c_int', 4703.76, 'R$/ciclo', 'SIGTAP/SIH via Relatório Conitec nº 725/2022', year=2024, status='premissa',
    note='Valores de tabela SUS não são corrigidos pela inflação')
add('n_int_cycles', 6, 'ciclos', 'Fase intensiva do Interfant-06 (6 ciclos de 4 semanas)', status='premissa')
add('c_maint', 500, 'R$/ciclo', 'SIH/SUS', year=2024, status='pendente', note='Especificar procedimentos e competência')
add('end_maint', 2.19222, 'anos', 'Fim da manutenção (valor calibrado do modelo original; só para reproduzir o manuscrito antigo)', status='premissa')
add('end_maint_protocol', 99 / 52, 'anos', 'Interfant-06: tratamento até 104 semanas do diagnóstico (NCT00550992); o tempo zero do modelo é o início do pós-indução (dia 36), logo 104 − 5 = 99 semanas')
add('c_fu', 10, 'R$/ciclo', 'Consulta ambulatorial SIGTAP', year=2024, status='pendente')
add('c_salv', 121856.8, 'R$/episódio', '13 ciclos (1 ano) × [QT de 3ª linha R$800 (SIGTAP 03.04.07.004-1) + 16,8 diárias × R$552 − R$700 já contados no estado pós-recaída]; componentes do Relatório Conitec nº 725/2022', year=2024, status='premissa',
    note='')
add('c_salv_2l', 13 * (1381.76 + 16.8 * 552 - 700), 'R$/episódio', '13 ciclos × [QT de 2ª linha R$1.381,76 (SIGTAP 03.04.07.002-5, "quimioterapia da 1ª recidiva", competência 03/2026) + 16,8 diárias × R$552 − R$700 do estado pós-recaída]', year=2024)
# ---------------- Custo pós-recaída reconstruído (SIGTAP 03/2026; valores por procedimento)
PR_VISIT = {'03.01.01.007-2 Consulta médica em atenção especializada': 10.00, '02.02.02.038-0 Hemograma completo': 4.11,
            '02.02.01.031-7 Dosagem de creatinina': 1.85, '02.02.01.069-4 Dosagem de ureia': 1.85,
            '02.02.01.064-3 Dosagem de TGO': 2.01, '02.02.01.065-1 Dosagem de TGP': 2.01,
            '02.02.01.036-8 Dosagem de desidrogenase lática': 3.68}
add('pr_visit', sum(PR_VISIT.values()), 'R$/visita', 'Visita de acompanhamento: consulta especializada + hemograma + creatinina, ureia, TGO, TGP e LDH (SIGTAP, competência 03/2026)')
add('pr_visits_per_cycle', 12 / 13, 'visitas/ciclo', 'Premissa: uma visita por mês (12/ano) em ciclos de 4 semanas; testada em cenário', status='premissa')
add('c_pr_recon', sum(PR_VISIT.values()) * 12 / 13, 'R$/ciclo', 'Custo pós-recaída reconstruído: acompanhamento ambulatorial mensal')
add('qt_lla_ini', 8689.65, 'R$/mês', 'SIGTAP 03.04.07.006-8, QT de LLA na infância e adolescência, 1ª linha, fases terapêuticas iniciais (até 6 meses); Portaria GM/MS 159/2018; competência 03/2026')
add('qt_lla_man', 302.07, 'R$/mês', 'SIGTAP 03.04.07.007-6, QT de LLA na infância e adolescência, 1ª linha, manutenção (até 30 meses); Portaria GM/MS 159/2018; competência 03/2026')
add('apac_per_cycle', 12 / 13, 'APAC/ciclo', 'APAC é mensal (12 por ano); o modelo tem 13 ciclos de 4 semanas por ano')
add('c_int_lla', 8689.65 * 12 / 13 + 6 * 552 + 10, 'R$/ciclo', 'QT de LLA fases iniciais (por ciclo de 4 semanas) + 6 diárias × R$552 + 1 consulta R$10')
add('c_maint_lla', 302.07 * 12 / 13, 'R$/ciclo', 'QT de LLA manutenção, por ciclo de 4 semanas')
add('u_dec_chen', 0.967, 'multiplicador', 'Sobreviventes de LLA infantil: utilidade 0,028 menor que a população geral (HUI3; IC95% −0,062 a 0,007); Chen et al., Qual Life Res 2022;31:343-74; sobre norma de ~0,85 equivale a 0,967')
add('c_pr', 700, 'R$/ciclo', 'Acompanhamento pós-recaída', year=2024, status='pendente')
add('frac_rel_c', 0.886, 'proporção', 'CIR 49,6% / falha de DFS 56,0%; Vieira Martins et al., 2026')
add('frac_rel_i', 0.796, 'proporção', 'CIR 13,3% / falha de DFS 16,7%; Vieira Martins et al., 2026')

# ---------------- TCTH
add('c_hsct_src', 94254.25, 'R$', 'Custo inicial do TCTH; van Beurden-Tan et al., J Bras Econ Saúde 2022;14:41-50',
    year=2021, status='premissa', note='Ano de valoração presumido 2021 (estudo publicado em 2022)')
add('c_hsct_sigtap', 54939, 'R$', 'SIGTAP 05.05.01.001-1, TCTH alogênico aparentado de medula óssea, tabela 2026',
    year=2024, status='premissa', note='Valor assumido igual em 2024')
add('c_hsct_micro_src', 291400, 'R$', 'Microcusteio TDABC; Vargas et al., J Bras Econ Saúde 2021;13:166-74',
    year=2020, status='premissa', note='Ano de valoração presumido 2020')
add('p_hsct_c', 0.30, 'proporção', 'Derivado de van der Sluis et al., N Engl J Med 2023 (controles Interfant-06)')
add('p_hsct_i', 0.333, 'proporção', 'Derivado de van der Sluis et al., N Engl J Med 2023 (10/30)')
add('t_hsct', 1.0, 'anos', 'Momento do TCTH (ciclo 13)', status='premissa')

# ---------------- Preços alternativos (cenários)
add('vial_pmc', 21094.99, 'R$/frasco', 'CMED, preço máximo ao consumidor, 2024', year=2024)
add('vial_icms17', 11268, 'R$/frasco', 'CMED, PMVG com ICMS 17%, 2024', year=2024)
add('vial_2026_src', 9670.81, 'R$/frasco', 'CMED, PMVG com ICMS 0%, lista publicada em 09/10/2026', year=2026, status='ok',
    note='Deflacionado para 2024 pelo IPCA de 2025 (4,26%) e de jan-set/2026 (3,95%)')
add('vial_2026', 9461, 'R$/frasco', 'Lista 2026 usada no manuscrito antigo (só para reproduzi-lo; o caso corrigido usa vial_2026_src deflacionado)', year=2026)
add('vial_bps_max_src', 10354.28, 'R$/frasco', 'Banco de Preços em Saúde: compra judicial por pregão, FUNSAUDE/PR, 112 frascos, 01/07/2022', year=2022, status='ok')
add('vial_bps_min_src', 8780.67, 'R$/frasco', 'Banco de Preços em Saúde: compra judicial por dispensa, Fundo Especial de Saúde de Campo Grande/MS, 27 frascos, 01/06/2021 (outra compra de 11 frascos em 06/12/2021 a R$9.207,91)', year=2021, status='ok')

# ---------------- Limiares
add('wtp', 40000, 'R$/QALY', 'Valor de referência Conitec, R$40.000/QALY (Diretriz 2025)', status='pendente',
    note='Citar o documento normativo da Conitec sobre limiares')
add('wtp_ly', 35000, 'R$/AVG', 'Valor de referência Conitec por ano de vida ganho', status='pendente')
add('wtp_mod', 120000, 'R$/QALY', 'Modificador de até 3x; mostrado só como cenário ilustrativo ')

# ---------------- Via pós-recaída (alternativa B, caso-base desde 24/10/2026)
DRI = 'Driessen EMC et al. Leukemia 2016;30:1184-7 (Interfant-99, 202 recaídas)'
add('pB_cur', 159 / 191, 'proporção', 'Recaídas tratadas com intenção curativa: 159/(159+32); ' + DRI, note='Beta(159; 32)')
add('pB_hsct', 87 / 159, 'proporção', 'TCTH entre os tratados com intenção curativa: 87/159; ' + DRI, note='Beta(87; 72)')
add('pB_hsct_delay', 4.2 / 12, 'anos', 'Mediana recaída → TCTH 4,2 meses; ' + DRI)
add('pB_salv_cycle', 1381.76 + 16.8 * 552, 'R$/ciclo', 'Resgate bruto: QT 2ª linha SIGTAP 03.04.07.002-5 (03/2026) + 16,8 diárias × R$552 (Conitec 725/2022)')
add('pB_c_dx', 5.79 + 10 * 80 + 160, 'R$/recaída', 'Mielograma 02.02.09.019-1 + imunofenotipagem 02.02.03.023-7 ×10 + cariótipo 02.02.10.002-2 (SIGTAP 03/2026)')
add('pB_n_bm', 3, 'nº', 'Reavaliações medulares no resgate curativo (premissa validada pelas autoras clínicas)')
add('pB_c_bm', 5.79 + 10 * 80, 'R$', 'Mielograma + imunofenotipagem 10 marcadores (SIGTAP 03/2026)')
add('pB_eol_days', 10, 'dias', 'Internação terminal (premissa validada pelas autoras clínicas)')
add('pB_eol_icu_p', 0.425, 'proporção', 'UTI nos últimos 30 dias: Widger K et al. BMC Pediatr 2023;23:375')
add('pB_eol_icu_days', 4, 'dias', 'Dias de UTI pediátrica no fim de vida (premissa validada pelas autoras clínicas)')
add('c_icu_ped', 600.0, 'R$/dia', 'Diária UTI pediátrica II, SIGTAP 08.02.01.015-6 (03/2026)')


def eol_costs(b):
    icu = b['pB_eol_icu_p'] * b['pB_eol_icu_days'] * b['c_icu_ped']
    return b['pB_eol_days'] * 552 + icu, icu


# ---------------- Coorte incidente exploratória
add('incident_infants', 32, 'lactentes/ano', 'Painel de monitoramento do tratamento oncológico, DATASUS (acesso 13/08/2026)',
    status='premissa', note='Estimativa exploratória, não é análise de impacto orçamentário')


def base(corrected=True):
    """Dicionário de parâmetros. corrected=True aplica as correções de ano-base (IPCA)."""
    b = {k: v['value'] for k, v in P.items()}
    if corrected:
        b['c_hsct'] = P['c_hsct_src']['value'] * ipca_factor(P['c_hsct_src']['year'])
        b['c_hsct_micro'] = P['c_hsct_micro_src']['value'] * ipca_factor(P['c_hsct_micro_src']['year'])
        b['vial_bps_max'] = P['vial_bps_max_src']['value'] * ipca_factor(P['vial_bps_max_src']['year'])
        b['vial_bps_min'] = P['vial_bps_min_src']['value'] * ipca_factor(P['vial_bps_min_src']['year'])
        b['vial_2026'] = P['vial_2026_src']['value'] / ((1 + IPCA[2025]) * (1 + IPCA_2026_JAN_SET))
        b['c_int'] = P['c_int_lla']['value']; b['c_maint'] = P['c_maint_lla']['value']
        b['c_pr'] = P['c_pr_recon']['value']
        b['c_salv'] = 13 * (1381.76 + 16.8 * 552 - b['c_pr'])          # resgate líquido do custo pós-recaída
        b['u_dec'] = P['u_dec_chen']['value']; b['u_dec_beta'] = (70.99, 2.42)
        b['end_maint'] = P['end_maint_protocol']['value']
        b['pathway_B'] = True
        b['c_salv'] = 13 * P['pB_salv_cycle']['value']                    # resgate bruto (usado só se pathway_B=False)
        b['pB_eol_full'], b['pB_eol_icu'] = eol_costs(b)
        b['pB_c_hsct'] = None                                              # segue c_hsct (mesmo custo unitário)
    else:
        b['pop_norm'] = None; b['life_table'] = None
        b['ug_usable_vial'] = 35   # premissa do manuscrito (2,8 mL)
        b['schedule'] = None       # manuscrito: 5 frascos
        b['c_hsct'] = P['c_hsct_src']['value']
        b['c_hsct_micro'] = P['c_hsct_micro_src']['value']
        b['vial_bps_max'] = P['vial_bps_max_src']['value']
        b['vial_bps_min'] = P['vial_bps_min_src']['value']
    return b
