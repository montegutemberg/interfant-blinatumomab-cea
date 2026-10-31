# -*- coding: utf-8 -*-
"""Gera Modelo_PSM_Blinatumomabe_Lactentes.xlsx: modelo de sobrevida particionada com fórmulas vivas."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter as L
import inputs as I, model as Mo

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resultados', 'final_numbers.json')))
CURVES = json.load(open(os.path.join(HERE, 'curves.json')))
OUT = os.path.join(HERE, 'excel', 'Modelo_PSM_Blinatumomabe_Lactentes.xlsx')

F = 'Arial'
fN = Font(name=F, size=10); fB = Font(name=F, size=10, bold=True); fT = Font(name=F, size=14, bold=True)
fIn = Font(name=F, size=10, color='0000FF'); fH = Font(name=F, size=10, bold=True, color='FFFFFF')
fI = Font(name=F, size=9, italic=True, color='52514E'); fLink = Font(name=F, size=10, color='008000')
HF = PatternFill('solid', fgColor='1F4E79'); INF = PatternFill('solid', fgColor='DDEBF7')
SEC = PatternFill('solid', fgColor='EDEDED'); YEL = PatternFill('solid', fgColor='FFF2CC'); RED = PatternFill('solid', fgColor='F8CBAD')
OUTF = PatternFill('solid', fgColor='E2EFDA')
thin = Side(style='thin', color='BFBFBF'); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical='top')

wb = openpyxl.Workbook()
NAMES = {}
def name(nm, ref):
    wb.defined_names[nm] = DefinedName(nm, attr_text=ref); NAMES[nm] = ref

def hdr(ws, r, vals, widths=None, c0=1):
    for j, v in enumerate(vals):
        c = ws.cell(r, c0 + j, v); c.font = fH; c.fill = HF; c.alignment = Alignment(wrap_text=True, vertical='center'); c.border = BOX
    if widths:
        for j, w in enumerate(widths): ws.column_dimensions[L(c0 + j)].width = w

def title(ws, t, sub=None):
    ws['A1'] = t; ws['A1'].font = fT
    if sub: ws['A2'] = sub; ws['A2'].font = fI

def put(ws, r, c, v, font=fN, fmt=None, fill=None, border=True, align=None):
    cell = ws.cell(r, c, v); cell.font = font
    if fmt: cell.number_format = fmt
    if fill: cell.fill = fill
    if border: cell.border = BOX
    if align: cell.alignment = align
    return cell

# =====================================================================  LEIA-ME
ws = wb.active; ws.title = 'Leia-me'
ws.column_dimensions['A'].width = 130
txt = [
 ('Modelo de sobrevida particionada: blinatumomabe em primeira linha para lactentes com LLA KMT2A-rearranjada (perspectiva SUS)', fT),
 ('Versão do manuscrito submetido à PharmacoEconomics – Open (outubro de 2026).', fN),
 ('', fN),
 ('Como usar', fB),
 ('1. Edite apenas as células em azul (fonte azul, fundo azul-claro) nas abas Inputs, Frascos e Curvas. Todo o resto é fórmula.', fN),
 ('2. Para rodar um cenário, escolha o número em Inputs!C4 (lista na aba Cenarios). O valor 1 é o caso-base. Os resultados aparecem na aba Resultados.', fN),
 ('3. A família paramétrica das curvas é escolhida em Inputs (1 Gompertz, 2 Weibull, 3 Log-normal, 4 Log-logística, 5 Exponencial, 6 Mixture cure Weibull, 7 Gama generalizada).', fN),
 ('4. O número de frascos por ciclo vem da aba Frascos (esquema de preparo); um cenário pode substituí-lo.', fN),
 ('', fN),
 ('Estrutura', fB),
 ('Três estados (livre de evento, pós-recaída, morte). A ocupação vem de duas curvas: livre de evento = DFS; pós-recaída = OS − DFS. Ciclos de 4 semanas, horizonte vitalício (100 anos), meio ciclo na ocupação, desconto de 5% ao ano.', fN),
 ('Até 7 anos (período observado), as curvas paramétricas definem os estados. Depois, os livres de evento são considerados curados, com mortalidade da tábua completa do IBGE de 2024 multiplicada pelo SMR; os pós-recaída morrem com taxa ln(2)/mediana pós-recaída somada à mortalidade de fundo.', fN),
 ('Recaídas = quedas da DFS no período observado × fração de eventos que são recaída; cada recaída gera um episódio de resgate (custo pontual). TCTH: custo pontual em 1 ano, proporção por braço.', fN),
 ('Abas: Inputs · Cenarios · Frascos · Curvas · Tabua_IBGE · Modelo_Interfant · Modelo_Blina · Resultados · Sensibilidade_BML · PSA · Coorte_incidente · Validacao · Custo_Pos_Recaida', fN),
 ('', fN),
 ('Cores', fB),
 ('Azul = input editável · Preto = fórmula · Verde = resultado principal · Amarelo = premissa (valor assumido ou calibrado, testado em cenário)', fN),
 ('', fN),
 ('O que é fórmula viva e o que é resultado importado', fB),
 ('Caso-base, cenários (um por vez), coorte incidente: fórmulas vivas. Sensibilidade univariada (tornado) e PSA (5.000 simulações com normal multivariada e cópula DFS–OS): resultados do script Python (modelo_interfant), porque o Excel não roda essas simulações sem macros. A aba Validacao mostra que a planilha reproduz o Python.', fN),
]
for k, (t, f) in enumerate(txt, 1):
    c = ws.cell(k, 1, t); c.font = f; c.alignment = WRAP

# =====================================================================  INPUTS
wsI = wb.create_sheet('Inputs')
title(wsI, 'Inputs do modelo', 'Coluna C = valor base (editável). Coluna E = valor em uso (base ou cenário ativo). As fórmulas do modelo usam a coluna E por nomes definidos (in_...).')
put(wsI, 4, 1, 'Cenário ativo (nº, ver aba Cenarios)', fB); put(wsI, 4, 3, 1, fIn, fill=INF); name('in_cen', "Inputs!$C$4")
put(wsI, 4, 4, '=INDEX(Cenarios!$C$5:$C$60,in_cen)', fB, border=False)
hdr(wsI, 6, ['Parâmetro', 'Nome', 'Valor base', 'Unidade', 'Valor em uso', 'Fonte', 'Status', 'Observação'], [44, 16, 14, 14, 14, 62, 11, 60])

# colunas da aba Cenarios que podem substituir inputs
SCEN_COLS = {'in_vial': 'E', 'in_vials': 'F', 'in_family': 'G', 'in_smr': 'H', 'in_disc': 'I', 'in_horizon': 'J',
             'in_c_hsct': 'K', 'in_t_obs': 'L', 'in_tox_on': 'M', 'in_pr_cure': 'N', 'in_salv_qt': 'O', 'in_u_dec': 'P', 'in_norm_br': 'Q', 'in_end_maint': 'R', 'in_c_int': 'S', 'in_c_maint': 'T', 'in_c_pr': 'U', 'in_salv_net': 'AA'}
SCEN_COLS_B = {'in_pathB': 'V', 'in_pB_cur': 'W', 'in_pB_hsct': 'X', 'in_pB_eol_mult': 'Y', 'in_pB_nbm': 'Z'}
OVCOLS = ['E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA']
P = I.P
rowsI = [
 'Estrutura',
 ('Idade de entrada', 'in_age0', 0.42, 'anos', P['age0']),
 ('Duração do ciclo', 'in_dt', '=4/52', 'anos', P['dt']),
 ('Horizonte', 'in_horizon', 100, 'anos', P['horizon']),
 ('Taxa de desconto anual', 'in_disc', 0.05, 'por ano', P['disc']),
 ('Fim do período observado (ponto de cura)', 'in_t_obs', 7, 'anos', P['t_obs']),
 ('Família paramétrica (1–6)', 'in_family', 1, 'índice', dict(source='1 Gompertz (menor AIC e BIC nas 4 curvas); ver aba Curvas. A 7 (gama generalizada) fica só como registro do ajuste', status='ok', note='')),
 'Sobrevida de longo prazo',
 ('SMR dos curados', 'in_smr', 8, 'razão', P['smr']),
 ('Mediana de sobrevida pós-recaída', 'in_med_pr', 1.5, 'anos', P['med_pr']),
 ('Mortalidade pós-recaída (derivada)', 'in_mu', '=LN(2)/in_med_pr', 'por ano', dict(source='ln(2) / mediana', status='ok', note='')),
 ('Vivos pós-recaída no ponto de cura passam a curados (1 = sim, 0 = não)', 'in_pr_cure', 0, '', dict(source='Cenário de sensibilidade; caso-base 0', status='ok', note='Com 1, quem está vivo após recaída aos 7 anos segue a mortalidade, a utilidade e o custo dos curados')),
 'Utilidades',
 ('Terapia intensiva (0–2 anos)', 'in_u_int', 0.65, '', P['u_int']),
 ('Livre de evento após o tratamento (até 7 anos)', 'in_u_ef', 0.76, '', P['u_ef']),
 ('Pós-recaída', 'in_u_pr', 0.67, '', P['u_pr']),
 ('Decremento de sobrevivente (multiplicador)', 'in_u_dec', 0.967, '', dict(source='Chen et al., Qual Life Res 2022;31:343-74: sobreviventes de LLA infantil com utilidade 0,028 menor que a população geral (HUI3); sobre norma de ~0,85 equivale a 0,967', status='ok', note='Cenários: 1,0 e 0,94 (modelo original)')),
 ('Duração da terapia intensiva', 'in_t_int', 2, 'anos', P['t_int']),
 ('Norma populacional: 1 = brasileira por faixa etária (Santos 2021); 0 = calibrada do modelo original', 'in_norm_br', 1, '', dict(source='Santos M, Monteiro AL, Santos B. EQ-5D Brazilian population norms. Health Qual Life Outcomes 2021;19:162. Tabela na aba Tabua_IBGE (colunas D-E)', status='ok', note='18-64 anos; abaixo de 18 usa 18-19 e acima de 64 usa 60-64')),
 ('Norma calibrada aos 18 anos (só com a chave em 0)', 'in_pop_u0', 0.9413, '', dict(source='Valor calibrado do modelo original, sem fonte', status='premissa', note='Mantido só para o cenário de comparação')),
 ('Queda anual da norma calibrada após os 18 anos', 'in_pop_slope', 0.004, 'por ano', dict(source='Idem', status='premissa', note='')),
 'Blinatumomabe e toxicidade',
 ('Preço do frasco 38,5 µg (PMVG, ICMS 0%)', 'in_vial', 9118.23, 'R$', P['vial']),
 ('Frascos por ciclo', 'in_vials', '=Frascos!$C$22', 'frascos', dict(source='Aba Frascos (esquema de preparo); caso-base: 7 cassetes de 96 h', status='premissa', note='')),
 ('Custos de toxicidade ativos (1 = sim, 0 = não)', 'in_tox_on', 1, '', dict(source='Cenário "sem custos de toxicidade"', status='ok', note='')),
 ('Proporção com IVIg', 'in_p_ivig', 0.63, '', P['p_ivig']),
 ('Custo de IVIg por paciente', 'in_c_ivig', 8009, 'R$', P['c_ivig']),
 ('Proporção com G-CSF', 'in_p_gcsf', 0.17, '', P['p_gcsf']),
 ('Custo de G-CSF por paciente', 'in_c_gcsf', 630, 'R$', P['c_gcsf']),
 'Custos assistenciais (R$ de 2024)',
 ('QT pediátrica de 2ª linha, 1ª recidiva (SIGTAP 03.04.07.002-5)', 'in_qt_2l', 1381.76, 'R$', dict(source='SIGTAP competência 03/2026', status='ok', note='')),
 ('QT pediátrica de 3ª linha, 2ª recidiva (SIGTAP 03.04.07.004-1)', 'in_qt_3l', 800, 'R$', dict(source='SIGTAP competência 03/2026', status='ok', note='')),
 ('Diária hospitalar', 'in_diaria', 552, 'R$', dict(source='Relatório Conitec nº 725/2022, p. 38: custo médio de hospitalização por dia de pacientes com LLA (SIGTAP/DATASUS), R$551,77', status='ok', note='Não é um procedimento SIGTAP; o código citado no relatório (03.01.01.007-2) é o da consulta')),
 ('Consulta ambulatorial', 'in_consulta', 10, 'R$', dict(source='Relatório Conitec nº 725/2022, p. 39', status='premissa', note='')),
 ('Diárias por ciclo na fase intensiva', 'in_dias_int', 6, 'diárias', dict(source='Modelo original (PSM.xlsx)', status='premissa', note='')),
 ('QT de LLA infância, 1ª linha, fases iniciais, por mês (SIGTAP 03.04.07.006-8)', 'in_qt_lla_ini', 8689.65, 'R$/mês', dict(source='Portaria GM/MS 159/2018; SIGTAP competência 03/2026', status='ok', note='Até 6 meses')),
 ('QT de LLA infância, 1ª linha, manutenção, por mês (SIGTAP 03.04.07.007-6)', 'in_qt_lla_man', 302.07, 'R$/mês', dict(source='Portaria GM/MS 159/2018; SIGTAP competência 03/2026', status='ok', note='Até 30 meses')),
 ('APAC por ciclo de 4 semanas', 'in_apac', '=12/13', 'APAC/ciclo', dict(source='APAC mensal (12/ano); modelo com 13 ciclos/ano', status='ok', note='')),
 ('Ciclo da fase intensiva', 'in_c_int', '=in_qt_lla_ini*in_apac+in_dias_int*in_diaria+in_consulta', 'R$/ciclo', dict(source='QT de LLA fases iniciais + 6 diárias + 1 consulta', status='ok', note='Cenário com códigos genéricos do modelo original: R$4.703,76')),
 ('Ciclos da fase intensiva', 'in_n_int', 6, 'ciclos', P['n_int_cycles']),
 ('Ciclo de manutenção', 'in_c_maint', '=in_qt_lla_man*in_apac', 'R$/ciclo', dict(source='QT de LLA manutenção por ciclo de 4 semanas', status='ok', note='Cenário: R$500 do modelo original')),
 ('Fim da manutenção', 'in_end_maint', '=99/52', 'anos', dict(source='Interfant-06: tratamento até 104 semanas do diagnóstico (ClinicalTrials.gov NCT00550992); tempo zero do modelo = início do pós-indução (dia 36): 104 − 5 = 99 semanas', status='ok', note='Valor calibrado do modelo original (2,19222) fica como cenário')),
 ('Seguimento do livre de evento', 'in_c_fu', '=in_consulta', 'R$/ciclo', dict(source='Uma consulta por ciclo', status='ok', note='')),
 ('QT usada no resgate, por ciclo', 'in_salv_qt', '=in_qt_2l', 'R$', dict(source='SIGTAP define a 2ª linha como quimioterapia da 1ª recidiva (03.04.07.002-5) e a 3ª como da 2ª recidiva', status='ok', note='Cenário: 3ª linha (R$800), como no modelo original')),
 ('Diárias por ciclo de resgate', 'in_salv_dias', 16.8, 'diárias', dict(source='Relatório Conitec nº 725/2022, p. 38', status='ok', note='')),
 ('Ciclos do episódio de resgate', 'in_salv_ciclos', 13, 'ciclos', dict(source='Pressuposto do modelo: 1 ano de resgate', status='premissa', note='A Conitec usou 2 ciclos de tratamento subsequente')),
 ('Abater o custo pós-recaída do resgate (1 = sim, só na versão histórica)', 'in_salv_net', 0, '', dict(source='Versão anterior (R$700) subtraía o custo do estado nos 13 ciclos; desacoplado desde 24/10/2026', status='ok', note='')),
 ('Episódio de resgate fixo por recaída (só com a via B desligada)', 'in_c_salv', '=in_salv_ciclos*(in_salv_qt+in_salv_dias*in_diaria-in_salv_net*in_c_pr)', 'R$', dict(source='13 × (QT + 16,8 diárias); alternativa A (custos mínimos)', status='ok', note='No caso-base o custo da recaída vem da aba Via_Pos_Recaida')),
 ('Custo por ciclo no estado pós-recaída', 'in_c_pr', '=Custo_Pos_Recaida!$C$32', 'R$/ciclo', dict(source='Aba Custo_Pos_Recaida: cenário selecionado (base = acompanhamento ambulatorial mensal, SIGTAP 03/2026)', status='premissa', note='Frequência mensal é premissa a validar com os autores clínicos; o valor original sem fonte (R$700) ficou como cenário')),
 ('Fração de eventos de DFS que são recaída, Interfant-06', 'in_frac_c', 0.886, '', P['frac_rel_c']),
 ('Fração de eventos de DFS que são recaída, blinatumomabe', 'in_frac_i', 0.796, '', P['frac_rel_i']),
 'TCTH',
 ('Custo do TCTH na fonte (R$ de 2021)', 'in_c_hsct_src', 94254.25, 'R$', P['c_hsct_src']),
 ('Custo do TCTH (R$ de 2024, corrigido pelo IPCA)', 'in_c_hsct', '=in_c_hsct_src*INDEX($C$100:$C$104,MATCH(2021,$A$100:$A$104,0))', 'R$', dict(source='van Beurden-Tan 2022 × fator IPCA 2021→2024', status='premissa', note='Ano de valoração presumido 2021')),
 ('Proporção com TCTH, Interfant-06', 'in_p_hsct_c', 0.30, '', P['p_hsct_c']),
 ('Proporção com TCTH, blinatumomabe', 'in_p_hsct_i', 0.333, '', P['p_hsct_i']),
 ('Momento do TCTH', 'in_t_hsct', 1, 'anos', P['t_hsct']),
 'Valores usados só em cenários (R$ de 2024)',
 ('Preço ao consumidor (PMC)', 'in_vial_pmc', 21094.99, 'R$', P['vial_pmc']),
 ('PMVG com ICMS 17%', 'in_vial_icms17', 11268, 'R$', P['vial_icms17']),
 ('PMVG ICMS 0%, lista CMED de 09/10/2026 (nominal)', 'in_vial_2026_src', 9670.81, 'R$', dict(source='CMED, lista PMVG publicada em 09/10/2026', status='ok', note='')),
 ('IPCA 2025', 'in_ipca2025', 0.0426, '', dict(source='IBGE, divulgado em 09/01/2026', status='ok', note='')),
 ('IPCA jan-set/2026', 'in_ipca2026', 0.039513, '', dict(source='Variações mensais do IPCA (jan-set/2026)', status='premissa', note='IBGE')),
 ('PMVG out/2026 deflacionado para R$ de 2024', 'in_vial_2026', '=in_vial_2026_src/((1+in_ipca2025)*(1+in_ipca2026))', 'R$', dict(source='Lista out/2026 ÷ IPCA 2025 e jan-set/2026', status='ok', note='')),
 ('Maior compra pública (01/07/2022, R$ de 2022)', 'in_bps_max_src', 10354.28, 'R$', P['vial_bps_max_src']),
 ('Menor compra pública (01/06/2021, R$ de 2021)', 'in_bps_min_src', 8780.67, 'R$', P['vial_bps_min_src']),
 ('Maior compra pública (R$ de 2024)', 'in_bps_max', '=in_bps_max_src*INDEX($C$100:$C$104,MATCH(2022,$A$100:$A$104,0))', 'R$', dict(source='IPCA 2022→2024', status='ok', note='')),
 ('Menor compra pública (R$ de 2024)', 'in_bps_min', '=in_bps_min_src*INDEX($C$100:$C$104,MATCH(2021,$A$100:$A$104,0))', 'R$', dict(source='IPCA 2021→2024', status='ok', note='')),
 ('TCTH pelo código SIGTAP 05.05.01.001-1', 'in_hsct_sigtap', 54939, 'R$', P['c_hsct_sigtap']),
 ('TCTH por microcusteio (R$ de 2020)', 'in_hsct_micro_src', 291400, 'R$', P['c_hsct_micro_src']),
 ('TCTH por microcusteio (R$ de 2024)', 'in_hsct_micro', '=in_hsct_micro_src*INDEX($C$100:$C$104,MATCH(2020,$A$100:$A$104,0))', 'R$', dict(source='Vargas 2021 × IPCA 2020→2024', status='premissa', note='')),
 'Limiares e outros',
 ('Valor de referência por QALY', 'in_wtp', 40000, 'R$/QALY', P['wtp']),
 ('Valor de referência por ano de vida', 'in_wtp_ly', 35000, 'R$/AV', P['wtp_ly']),
 ('Modificador de até 3× (só ilustrativo)', 'in_wtp_mod', 120000, 'R$/QALY', P['wtp_mod']),
 ('Câmbio médio 2024', 'in_fx', 5.39, 'R$/US$', dict(source='Média de 2024', status='ok', note='')),
 ('Lactentes elegíveis por ano (coorte exploratória)', 'in_incid', 32, 'lactentes', P['incident_infants']),
]
r = 7; ROWI = {}
for item in rowsI:
    if isinstance(item, str):
        for c in range(1, 9): wsI.cell(r, c).fill = SEC
        wsI.cell(r, 1, item).font = fB; r += 1; continue
    lab, nm, val, unit, meta = item
    put(wsI, r, 1, lab); put(wsI, r, 2, nm, fI)
    isf = isinstance(val, str) and val.startswith('=')
    put(wsI, r, 3, val, fN if isf else fIn, fill=None if isf else INF)
    put(wsI, r, 4, unit)
    if nm in SCEN_COLS:
        col = SCEN_COLS[nm]
        f = f'=IF(INDEX(Cenarios!${col}$5:${col}$60,in_cen)="",C{r},INDEX(Cenarios!${col}$5:${col}$60,in_cen))'
    else:
        f = f'=C{r}'
    put(wsI, r, 5, f, fB)
    name(nm, f"Inputs!$E${r}"); ROWI[nm] = r
    src = meta.get('source', '') if isinstance(meta, dict) else ''
    st = meta.get('status', '') if isinstance(meta, dict) else ''
    note = meta.get('note', '') if isinstance(meta, dict) else ''
    put(wsI, r, 6, src, align=WRAP); c = put(wsI, r, 7, st); put(wsI, r, 8, note, align=WRAP)
    if st == 'premissa': c.fill = YEL
    if st == 'pendente': c.fill = RED
    fmt = '0.0000' if isinstance(val, float) and abs(val) < 2 else ('#,##0.00' if isinstance(val, (int, float)) and abs(val) >= 100 else 'General')
    for cc in (3, 5): wsI.cell(r, cc).number_format = fmt
    r += 1
# IPCA (linhas 98-104)
assert r < 97, r
put(wsI, 98, 1, 'IPCA anual (dez/dez), IBGE — fator acumulado até 2024', fB, border=False)
hdr(wsI, 99, ['Ano', 'IPCA no ano', 'Fator até 2024'])
for k, y in enumerate([2020, 2021, 2022, 2023, 2024]):
    rr = 100 + k
    put(wsI, rr, 1, y); put(wsI, rr, 2, I.IPCA[y], fIn, '0.00%', INF)
    put(wsI, rr, 3, 1, fmt='0.0000')
# fator: produto de (1+IPCA) dos anos seguintes até 2024 → usar fórmula explícita
for k, y in enumerate([2020, 2021, 2022, 2023, 2024]):
    rr = 100 + k
    terms = '*'.join(f'(1+B{x})' for x in range(rr + 1, 105))
    wsI.cell(rr, 3).value = f'={terms}' if terms else 1
wsI.freeze_panes = 'A7'

# =====================================================================  CENÁRIOS
wsC = wb.create_sheet('Cenarios')
title(wsC, 'Cenários', 'Escolha o nº em Inputs!C4. Célula em branco = usa o valor base. Colunas AC–AE: resultados do script Python, para conferência.')
hdr(wsC, 4, ['Nº', 'Grupo', 'Cenário', 'Descrição curta', 'Preço do frasco', 'Frascos', 'Família', 'SMR', 'Desconto', 'Horizonte', 'Custo TCTH', 'Ponto de cura', 'Toxicidade (1/0)', 'Pós-recaída curados (1/0)', 'QT do resgate (R$)', 'Decremento sobrevivente', 'Norma BR (1/0)', 'Fim da manutenção', 'Ciclo intensivo (R$)', 'Ciclo manutenção (R$)', 'Pós-recaída (R$/ciclo)', 'Via B (1/0)', 'Intenção curativa', 'TCTH pós-recaída', 'Fim de vida (×)', 'Reavaliações medulares', 'Abater c_pr no resgate (1/0)', 'Referência no script Python', 'Python: Δ custo', 'Python: Δ QALY', 'Python: RCEI'],
    [5, 18, 52, 30, 12, 9, 8, 7, 9, 9, 12, 10, 11, 12, 11, 11, 9, 11, 12, 12, 12, 9, 10, 10, 9, 10, 10, 40, 13, 11, 11])
SC = [
 ('Base', 'Caso-base', '7 frascos, PMVG ICMS 0%', {}, 'Caso-base'),
 ('Preço', 'PMVG com ICMS 17%', '', {'E': '=in_vial_icms17'}, 'PMVG com ICMS 17%'),
 ('Preço', 'PMVG, lista CMED de out/2026 deflacionada para 2024', '', {'E': '=in_vial_2026'}, 'PMVG, lista 2026'),
 ('Preço', 'Maior compra pública observada', 'R$ de 2024', {'E': '=in_bps_max'}, 'Maior compra pública observada'),
 ('Preço', 'Menor compra pública observada', 'R$ de 2024', {'E': '=in_bps_min'}, 'Menor compra pública observada'),
 ('Preço', 'Preço ao consumidor (PMC)', '', {'E': '=in_vial_pmc'}, 'Preço ao consumidor, R$21.095/frasco'),
 ('Frascos', 'Uso fracionado pleno (teórico)', 'dose total ÷ 35 µg', {'F': '=Frascos!$C$15/Frascos!$C$9'}, 'Uso fracionado pleno, sem desperdício'),
 ('Frascos', 'Conta teórica do manuscrito', '5 frascos', {'F': 5}, 'Conta teórica do manuscrito (5 frascos, aproveitamento total)'),
 ('Frascos', '3 dias com bolsas de 24 h; depois 96 h', 'esquema B', {'F': '=Frascos!$D$29'}, 'Guia/HCPA B: 3 dias internado (mínimo da bula); depois 96 h em casa'),
 ('Frascos', '1a semana com bolsas de 24 h; depois 96 h', 'esquema A', {'F': '=Frascos!$D$28'}, 'Guia/HCPA A: 1a semana internado com bolsas de 24 h; depois 96 h em casa'),
 ('Frascos', 'Esquema A com perda de uma bolsa', '+1 frasco', {'F': '=Frascos!$D$32'}, 'Guia/HCPA A com perda de uma bolsa (+1 frasco)'),
 ('Frascos', 'Esquema A sem reaproveitar o frasco aberto', '', {'F': '=Frascos!$D$33'}, 'Guia/HCPA A sem reaproveitar o frasco aberto'),
 ('Frascos', 'Bolsas de 24 h o ciclo inteiro', 'pior caso operacional', {'F': '=Frascos!$D$31'}, 'Guia/HCPA D: bolsas de 24 h o ciclo inteiro (pior caso operacional)'),
 ('Extrapolação', 'Weibull', '', {'G': 2}, 'Weibull'),
 ('Extrapolação', 'Log-normal', '', {'G': 3}, 'Log-normal'),
 ('Extrapolação', 'Log-logística', '', {'G': 4}, 'Log-logística'),
 ('Extrapolação', 'Mixture cure (Weibull)', '', {'G': 6}, 'Mixture cure'),
 ('Extrapolação', 'Cura assumida a partir de 4 anos', '', {'L': 4}, 'Cura assumida a partir de 4 anos (fim do seguimento mediano)'),
 ('Extrapolação', 'Vivos pós-recaída aos 7 anos passam a curados', 'cenário de sensibilidade', {'N': 1}, 'Sobreviventes pós-recaída aos 7 anos passam a curados'),
 ('Mortalidade', 'Sem excesso de mortalidade (SMR 1)', '', {'H': 1}, 'Sem excesso de mortalidade, SMR 1'),
 ('Mortalidade', 'SMR 12', '', {'H': 12}, 'SMR 12'),
 ('Custos', 'TCTH pelo código SIGTAP isolado', '', {'K': '=in_hsct_sigtap'}, 'TCTH pelo código SIGTAP isolado'),
 ('Custos', 'TCTH por microcusteio', 'R$ de 2024', {'K': '=in_hsct_micro'}, 'TCTH por microcusteio'),
 ('Custos', 'Sem custos de toxicidade', '', {'M': 0}, 'Sem custos de toxicidade'),
 ('Custos', 'Resgate com QT de 3ª linha', 'SIGTAP 03.04.07.004-1 (modelo original)', {'O': '=in_qt_3l'}, 'Resgate com QT de 3ª linha'),
 ('Pós-recaída', 'Episódio fixo de resgate (alternativa A)', '13 ciclos para todas as recaídas; sem TCTH nem fim de vida', {'V': 0}, 'Pós-recaída: episódio fixo (alternativa A; resgate de 13 ciclos para todas as recaídas, sem TCTH nem fim de vida)'),
 ('Pós-recaída', 'Versão anterior (R$700/ciclo; histórico)', 'resgate líquido do custo do estado', {'V': 0, 'U': 700, 'AA': 1}, 'Pós-recaída: versão anterior (R$700/ciclo, resgate líquido; histórico)'),
 ('Pós-recaída', 'Intenção curativa 0,787', 'sem conduta informada = suporte', {'W': '=159/202'}, 'Pós-recaída: intenção curativa 0,787 (sem conduta = suporte)'),
 ('Pós-recaída', 'Todas as recaídas com intenção curativa', '', {'W': 1}, 'Pós-recaída: todas as recaídas com intenção curativa'),
 ('Pós-recaída', 'TCTH em 40% dos tratados', '', {'X': 0.40}, 'Pós-recaída: TCTH em 40% dos tratados'),
 ('Pós-recaída', 'TCTH em 70% dos tratados', '', {'X': 0.70}, 'Pós-recaída: TCTH em 70% dos tratados'),
 ('Pós-recaída', 'Sem custo de fim de vida', '', {'Y': 0}, 'Pós-recaída: sem custo de fim de vida'),
 ('Pós-recaída', 'Custo de fim de vida dobrado', '', {'Y': 2}, 'Pós-recaída: custo de fim de vida dobrado'),
 ('Pós-recaída', '5 reavaliações medulares', '', {'Z': 5}, 'Pós-recaída: 5 reavaliações medulares'),
 ('Pós-recaída', 'Acompanhamento trimestral', 'menor uso', {'U': '=Custo_Pos_Recaida!$C$29'}, 'Pós-recaída: acompanhamento trimestral'),
 ('Custos', 'QT de 1ª linha pelos códigos genéricos (modelo original)', 'R$4.703,76 e R$500 por ciclo', {'S': 4703.76, 'T': 500}, 'QT pelos códigos genéricos do modelo original'),
 ('Utilidade', 'Sem decremento de sobrevivente', 'decremento 1,0', {'P': 1}, 'Sem decremento de sobrevivente'),
 ('Utilidade', 'Decremento 0,94 (modelo original)', '', {'P': 0.94}, 'Decremento de sobrevivente 0,94 (modelo original)'),
 ('Utilidade', 'Norma e fim da manutenção calibrados (modelo original)', 'norma 0,9413 − 0,004/ano; manutenção 2,19 anos', {'Q': 0, 'R': 2.19222}, 'Norma de utilidade e fim da manutenção calibrados (modelo original)'),
 ('Desconto/horizonte', 'Desconto 0%', '', {'I': 0}, 'Desconto 0%'),
 ('Desconto/horizonte', 'Desconto 10%', '', {'I': 0.10}, 'Desconto 10%'),
 ('Desconto/horizonte', 'Horizonte 20 anos', '', {'J': 20}, 'Horizonte 20 anos'),
 ('Desconto/horizonte', 'Horizonte 10 anos', '', {'J': 10}, 'Horizonte 10 anos'),
 ('Combinado', 'PMVG ICMS 17% + 14 frascos + TCTH pelo SIGTAP', 'pior caso com preço de governo', {'E': '=in_vial_icms17', 'F': 14, 'K': '=in_hsct_sigtap'}, 'Pior caso com preço de governo: PMVG ICMS 17% + 14 frascos + TCTH pelo SIGTAP'),
 ('Combinado', 'PMVG ICMS 17% + 7 frascos + TCTH pelo SIGTAP', '', {'E': '=in_vial_icms17', 'K': '=in_hsct_sigtap'}, 'PMVG ICMS 17% + 7 frascos + TCTH pelo SIGTAP'),
 ('Combinado', 'PMC + 6 frascos + TCTH pelo SIGTAP', '', {'E': '=in_vial_pmc', 'F': 6, 'K': '=in_hsct_sigtap'}, 'PMC + 6 frascos + TCTH pelo SIGTAP'),
 ('Combinado', 'PMC + 14 frascos + TCTH pelo SIGTAP', 'único acima do limiar', {'E': '=in_vial_pmc', 'F': 14, 'K': '=in_hsct_sigtap'}, 'Pior caso: PMC + 14 frascos + TCTH pelo SIGTAP'),
]
import analyses as AN
PY = {s['name']: s for s in AN.scenarios()}
for k, (g, nm, desc, ov, pyname) in enumerate(SC):
    rr = 5 + k
    put(wsC, rr, 1, k + 1); put(wsC, rr, 2, g); put(wsC, rr, 3, nm); put(wsC, rr, 4, desc, fI)
    for col in OVCOLS:
        cidx = openpyxl.utils.column_index_from_string(col)
        v = ov.get(col, None)
        c = put(wsC, rr, cidx, v, fIn, fill=INF)
        if col in 'EKOSTU': c.number_format = '#,##0.00'
        if col == 'I': c.number_format = '0%'
    s = PY[pyname]
    put(wsC, rr, 28, pyname, fI); put(wsC, rr, 29, s['d_cost'], fmt='#,##0'); put(wsC, rr, 30, s['d_qaly'], fmt='0.000'); put(wsC, rr, 31, s['icer'], fmt='#,##0')
NSC = len(SC)
dvc = DataValidation(type='whole', operator='between', formula1='1', formula2=str(NSC), showErrorMessage=True,
                     errorTitle='Cenário', error=f'Escolha um número de 1 a {NSC} (aba Cenarios).')
wsI.add_data_validation(dvc); dvc.add('C4')
wsC.freeze_panes = 'D5'

# =====================================================================  FRASCOS
wsF = wb.create_sheet('Frascos')
title(wsF, 'Frascos por ciclo de 28 dias', 'Bula ANVISA 04/11/2024 (Guia Blincyto) e esquema de preparo para lactentes < 0,4 m² (cassetes de 96 h, 250 mL para infundir 240 mL).')
hdr(wsF, 4, ['Parâmetro', '', 'Valor', 'Unidade', 'Fonte / observação'], [46, 2, 12, 12, 70])
FR = [
 (5, 'Superfície corporal', 0.36, 'm²', 'Mediana para lactente de 5 meses', True),
 (6, 'Dose', 15, 'µg/m²/dia', 'Protocolo Interfant + blinatumomabe', True),
 (7, 'Concentração após reconstituição', 12.5, 'µg/mL', 'Bula', True),
 (8, 'Volume extraível por frasco', 2.8, 'mL', 'Bula; a farmácia do HCPA relata até 3 mL na prática', True),
 (9, 'Conteúdo útil por frasco', '=C7*C8', 'µg', '', False),
 (10, 'Volume preparado do cassete (ambulatorial)', 250, 'mL', 'Bula/Guia: infunde 240 mL', True),
 (11, 'Volume infundido', 240, 'mL', 'Bula/Guia', True),
 (12, 'Duração do cassete', 96, 'horas', 'Cálculo para ASC < 0,4 m²', True),
 (13, 'Duração do ciclo', 28, 'dias', '', True),
 (14, 'Dose diária', '=C6*C5', 'µg/dia', '', False),
 (15, 'Dose total do ciclo (sem desperdício)', '=C14*C13', 'µg', '', False),
 (16, 'Cassetes por ciclo', '=C13*24/C12', 'cassetes', '', False),
 (17, 'Blinatumomabe por cassete (com volume extra)', '=C14*C12/24*C10/C11', 'µg', '', False),
 (18, 'Volume por cassete', '=C17/C7', 'mL', '', False),
 (19, 'Frascos por cassete', '=CEILING(C17/C9,1)', 'frascos', 'Sobra do frasco não pode ser usada no cassete seguinte (4 dias depois; estabilidade 24 h)', False),
 (20, 'Frascos por ciclo, esquema de cassetes (E)', '=C16*C19', 'frascos', '', False),
]
for rr, lab, v, u, src, edit in FR:
    put(wsF, rr, 1, lab); put(wsF, rr, 3, v, fIn if edit else fN, fill=INF if edit else None, fmt='0.00' if not isinstance(v, int) else '0')
    put(wsF, rr, 4, u); put(wsF, rr, 5, src, align=WRAP)
put(wsF, 21, 1, 'Esquema escolhido (A, B, C, D, Ap, As, E ou M = manual)', fB); put(wsF, 21, 3, 'E', fIn, fill=INF)
put(wsF, 22, 1, 'Frascos por ciclo usados no caso-base', fB); put(wsF, 22, 3, '=IF(C21="M",C24,IF(C21="E",C20,INDEX(D28:D33,MATCH(C21,A28:A33,0))))', fB, fill=OUTF)
put(wsF, 24, 1, 'Número manual de frascos (se esquema = M)'); put(wsF, 24, 3, 7, fIn, fill=INF)
dvs = DataValidation(type='list', formula1='"A,B,C,D,Ap,As,E,M"'); wsF.add_data_validation(dvs); dvs.add('C21')
put(wsF, 26, 1, 'Esquemas alternativos: contagem do script Python (simulação dia a dia com as regras do guia, frasco aberto reaproveitado em até 24 h), válida para ASC de 0,36 m². Não recalcula se a ASC mudar.', fB, border=False)
put(wsF, 25, 1, '=IF(ABS(C5-0.36)>0.001,"ATENÇÃO: as contagens dos esquemas A a D, Ap e As foram simuladas para 0,36 m². Com outra ASC, só o esquema E (cassetes) e o manual valem.","")', Font(name=F, size=10, bold=True, color='C00000'), border=False)
hdr(wsF, 27, ['Esquema', 'Descrição', '', 'Frascos'])
for k, (code, desc, n) in enumerate([('A', '1a semana internado com bolsas de 24 h (270 mL); depois cassetes de 96 h', 9),
                                     ('B', '3 dias internado com bolsas de 24 h (mínimo da bula); depois 96 h', 8),
                                     ('C', '3 dias com 24 h; depois cassetes de 72 h preparados em pares (10 dias refrigerado)', 7),
                                     ('D', 'Bolsas de 24 h o ciclo inteiro, preparo diário', 14),
                                     ('Ap', 'Esquema A com perda de uma bolsa (+1 frasco)', 10),
                                     ('As', 'Esquema A sem reaproveitar o frasco aberto', 13)]):
    put(wsF, 28 + k, 1, code); put(wsF, 28 + k, 2, desc, align=WRAP); put(wsF, 28 + k, 4, n)
wsF.column_dimensions['B'].width = 2
for rr in range(28, 34): wsF.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=3)
wsF.column_dimensions['B'].width = 60

# =====================================================================  CURVAS
wsV = wb.create_sheet('Curvas')
title(wsV, 'Curvas paramétricas: máxima verossimilhança com censura intervalar sobre os números em risco e censuras de Vieira Martins 2026 (Fig. 1B–D)',
      'Gompertz: S(t)=exp(−(b/a)(e^{at}−1)); Weibull: exp(−(t/λ)^k); Log-normal: 1−Φ((ln t−μ)/σ); Log-logística: 1/(1+(t/α)^β); Exponencial: exp(−λt); Mixture cure: π+(1−π)exp(−(t/λ)^k); Gama generalizada (Prentice).')
FAM = [('gompertz', 'Gompertz', ['a', 'b', '']), ('weibull', 'Weibull', ['λ (escala)', 'k (forma)', '']), ('lognormal', 'Log-normal', ['μ', 'σ', '']),
       ('loglogistic', 'Log-logística', ['α', 'β', '']), ('exponential', 'Exponencial', ['λ', '', '']),
       ('mixture_cure_weibull', 'Mixture cure (Weibull)', ['π (curados)', 'λ', 'k']), ('gengamma', 'Gama generalizada', ['μ', 'σ', 'Q'])]
CV = [('dfs_c', 'DFS Interfant-06'), ('os_c', 'OS Interfant-06'), ('dfs_i', 'DFS blinatumomabe'), ('os_i', 'OS blinatumomabe')]
hdr(wsV, 4, ['Nº', 'Família'] + [f'{lab} p{j}' for _, lab in CV for j in (1, 2, 3)], [5, 22] + [12] * 12)
for fi, (fk, flab, _) in enumerate(FAM):
    rr = 5 + fi; put(wsV, rr, 1, fi + 1); put(wsV, rr, 2, flab)
    for ci, (ck, _) in enumerate(CV):
        prm = CURVES[ck][fk]['params']
        for j in range(3):
            v = prm[j] if j < len(prm) else None
            put(wsV, rr, 3 + ci * 3 + j, v, fIn if v is not None else fN, fill=INF if v is not None else None, fmt='0.000000')
put(wsV, 13, 1, 'Família em uso', fB, border=False); put(wsV, 13, 3, '=in_family', fB); put(wsV, 13, 4, '=INDEX($B$5:$B$11,in_family)', fB, border=False)
put(wsV, 14, 1, 'Parâmetros em uso', fB, border=False)
for ci, (ck, lab) in enumerate(CV):
    for j in range(3):
        col = 3 + ci * 3 + j
        put(wsV, 14, col, f'=INDEX({L(col)}$5:{L(col)}$11,in_family)', fmt='0.000000')
        name(f'cv_{ck}_{j+1}', f"Curvas!${L(col)}$14")
put(wsV, 16, 1, 'Ajuste reproduzido em R 4.4.1 (flexsurv) e em Python. Gompertz idêntico ao do modelo original. A gama generalizada converge para a fronteira do espaço de parâmetros (|Q| > 15) nas quatro curvas e não é usada no artigo.', fI, border=False)

def surv_formula(ck, t):
    a, b, c = (f'cv_{ck}_1', f'cv_{ck}_2', f'cv_{ck}_3')
    gg_w = f'(LN({t})-{a})/{b}'
    gg_u = f'(1/{c}^2)*EXP({c}*{gg_w})'
    gg = f'IF({c}<0,GAMMADIST({gg_u},1/{c}^2,1,TRUE),1-GAMMADIST({gg_u},1/{c}^2,1,TRUE))'
    br = [f'EXP(-({b}/{a})*(EXP({a}*{t})-1))', f'EXP(-(({t}/{a})^{b}))', f'1-NORMSDIST((LN({t})-{a})/{b})',
          f'1/(1+({t}/{a})^{b})', f'EXP(-{a}*{t})', f'{a}+(1-{a})*EXP(-(({t}/{b})^{c}))', gg]
    expr = br[-1]
    for j in range(len(br) - 2, -1, -1):
        expr = f'IF(in_family={j+1},{br[j]},{expr})'
    return f'IF({t}<=0,1,{expr})'

# =====================================================================  TÁBUA
wsT = wb.create_sheet('Tabua_IBGE')
title(wsT, 'Tábua completa de mortalidade, Brasil 2024, ambos os sexos (IBGE, 2025) e norma populacional de utilidade',
      'qx = probabilidade anual de morte. Idades 0-89 como publicadas; 90-100 extrapoladas por Gompertz ajustado às idades 80-89.')
hdr(wsT, 4, ['Idade', 'qx', '', 'Idade a partir de', 'Utilidade (EQ-5D-3L)'], [10, 12, 3, 16, 18])
for a in range(101):
    put(wsT, 5 + a, 1, a); put(wsT, 5 + a, 2, float(Mo.QX24[a]), fIn, '0.000000', INF)
for k, (a0, u) in enumerate(Mo.NORM_SANTOS):
    put(wsT, 5 + k, 4, a0); put(wsT, 5 + k, 5, u, fIn, '0.000', INF)
put(wsT, 16, 4, 'Santos M, Monteiro AL, Santos B. EQ-5D Brazilian population norms. Health Qual Life Outcomes 2021;19:162. Faixas de 5 anos (18-19, 20-24, ... 60-64); o valor de 18-19 vale antes dos 18 e o de 60-64 depois dos 64.', fI, border=False)
name('tb_norm_age', "Tabua_IBGE!$D$5:$D$14"); name('tb_norm_u', "Tabua_IBGE!$E$5:$E$14")
name('tb_qx', "Tabua_IBGE!$B$5:$B$105")

# =====================================================================  MODELO (um por braço)
NROW = 1301; R0 = 6
COLS = ['k (ciclo)', 't (anos)', 'Idade', 'qx', 'S DFS', 'S OS bruta', 'S OS (≥ DFS)', 'Livre de evento', 'Pós-recaída', 'Vivos',
        'Ciclo ativo', 'LE meio ciclo', 'PR meio ciclo', 't meio', 'Fator desconto', 'Idade meio', 'Utilidade LE', 'QALY',
        'AV descontado', 'AV não descontado', 'Custo quimio/manut.', 'Custo seguimento LE', 'Custo pós-recaída', 'Eventos de DFS', 'Custo da recaída', 'Recaídas descontadas', 'Fim de vida por recaída (até o horizonte)']
def model_sheet(nm, arm):
    ws = wb.create_sheet(nm)
    ck_d, ck_o = (f'dfs_{arm}', f'os_{arm}')
    frac = 'in_frac_c' if arm == 'c' else 'in_frac_i'
    title(ws, f'Traço de Markov por ciclo: {"Interfant-06" if arm == "c" else "Interfant-06 + blinatumomabe"}',
          'Linhas = início de cada ciclo de 4 semanas. Colunas K–Y calculam o ciclo k usando o início (k) e o fim (k+1).')
    put(ws, 3, 1, 'Ciclo de cura (k_obs)', fB, border=False); put(ws, 3, 3, '=INT(MIN(in_t_obs,in_horizon)/in_dt+1E-9)', fB)
    put(ws, 4, 1, 'Ciclos no horizonte (n)', fB, border=False); put(ws, 4, 3, '=ROUND(in_horizon/in_dt,0)', fB)
    hdr(ws, 5, COLS, [7, 8, 8, 9, 9, 9, 9, 10, 10, 9, 7, 10, 10, 8, 9, 8, 9, 10, 10, 10, 11, 10, 10, 10, 11, 11, 12])
    for k in range(NROW):
        r = R0 + k; p = r - 1; nx = r + 1
        ws.cell(r, 1, k)
        ws.cell(r, 2, f'=A{r}*in_dt')
        ws.cell(r, 3, f'=in_age0+B{r}')
        ws.cell(r, 4, f'=INDEX(tb_qx,MIN(INT(C{r}),100)+1)')
        ws.cell(r, 5, '=' + surv_formula(ck_d, f'B{r}'))
        ws.cell(r, 6, '=' + surv_formula(ck_o, f'B{r}'))
        ws.cell(r, 7, f'=MAX(F{r},E{r})')
        if k == 0:
            ws.cell(r, 8, f'=E{r}'); ws.cell(r, 9, f'=G{r}-E{r}')
        else:
            ws.cell(r, 8, f'=IF(A{r}<=$C$3,E{r},IF(AND(in_pr_cure=1,A{r}=$C$3+1),H{p}+I{p},H{p})*(1-MIN(1,in_smr*D{p}))^in_dt)')
            ws.cell(r, 9, f'=IF(A{r}<=$C$3,G{r}-E{r},IF(in_pr_cure=1,0,I{p}*EXP(-(in_mu-LN(1-D{p}))*in_dt)))')
        ws.cell(r, 10, f'=H{r}+I{r}')
        if k < NROW - 1:
            ws.cell(r, 11, f'=IF(A{r}<$C$4,1,0)')
            ws.cell(r, 12, f'=(H{r}+H{nx})/2')
            ws.cell(r, 13, f'=(I{r}+I{nx})/2')
            ws.cell(r, 14, f'=B{r}+in_dt/2')
            ws.cell(r, 15, f'=(1+in_disc)^(-N{r})')
            ws.cell(r, 16, f'=in_age0+N{r}')
            ws.cell(r, 17, f'=IF(N{r}<in_t_int,in_u_int,IF(N{r}<in_t_obs,in_u_ef,IF(in_norm_br=1,LOOKUP(P{r},tb_norm_age,tb_norm_u),MAX(0,MIN(1,in_pop_u0-in_pop_slope*MAX(P{r}-18,0))))*in_u_dec))')
            ws.cell(r, 18, f'=K{r}*(L{r}*Q{r}+M{r}*in_u_pr)*in_dt*O{r}')
            ws.cell(r, 19, f'=K{r}*(L{r}+M{r})*in_dt*O{r}')
            ws.cell(r, 20, f'=K{r}*(L{r}+M{r})*in_dt')
            ws.cell(r, 21, f'=K{r}*L{r}*IF(A{r}<in_n_int,in_c_int,IF(N{r}<in_end_maint,in_c_maint,0))*O{r}')
            ws.cell(r, 22, f'=K{r}*L{r}*IF(N{r}>=in_end_maint,in_c_fu,0)*O{r}')
            ws.cell(r, 23, f'=K{r}*M{r}*in_c_pr*O{r}')
            ws.cell(r, 24, f'=K{r}*MAX(E{r}-E{nx},0)*IF(B{nx}<=in_t_obs+1E-9,1,0)')
            mm = '(in_mu+LN(1+in_disc))'; T = f'(in_horizon-B{nx})'
            ws.cell(r, 27, f'=in_pB_eol_mult*(in_pB_cur*(in_mu/{mm}*(1-EXP(-{mm}*MAX(0,MIN(1,{T}))))*in_pB_eol_icu+IF({T}>1,in_mu/{mm}*(EXP(-{mm})-EXP(-{mm}*{T})),0)*in_pB_eol_full)+(1-in_pB_cur)*(in_mu/{mm}*(1-EXP(-{mm}*MAX(0,MIN(1,{T}))))+IF({T}>1,in_mu/{mm}*(EXP(-{mm})-EXP(-{mm}*{T})),0))*in_pB_eol_full)')
            ws.cell(r, 25, f'=X{r}*{frac}*IF(in_pathB=1,vB_salv+vB_hsct+vB_bm+AA{r},in_c_salv)*(1+in_disc)^(-B{nx})')
            ws.cell(r, 26, f'=X{r}*{frac}*(1+in_disc)^(-B{nx})')
    for r in range(R0, R0 + NROW):
        for c in range(1, 28): ws.cell(r, c).font = fN
        for c in (2, 3, 14, 16): ws.cell(r, c).number_format = '0.000'
        for c in (4, 5, 6, 7, 8, 9, 10, 12, 13, 15, 17, 24, 26): ws.cell(r, c).number_format = '0.00000'
        for c in (18, 19, 20): ws.cell(r, c).number_format = '0.00000'
        for c in (21, 22, 23, 25, 27): ws.cell(r, c).number_format = '#,##0.00'
    ws.freeze_panes = 'C6'
    return ws
model_sheet('Modelo_Interfant', 'c'); model_sheet('Modelo_Blina', 'i')
RNG = lambda sh, col: f"{sh}!${col}${R0}:${col}${R0+NROW-2}"

# =====================================================================  RESULTADOS
wsR = wb.create_sheet('Resultados', 1)
title(wsR, 'Resultados (cenário ativo)', None)
put(wsR, 2, 1, '="Cenário ativo: "&in_cen&" – "&INDEX(Cenarios!$C$5:$C$60,in_cen)', fB, border=False)
hdr(wsR, 4, ['Resultado', 'Interfant-06', 'Blinatumomabe', 'Incremental'], [52, 16, 16, 16])
def both(expr_c, expr_i): return expr_c, expr_i
rowsR = [
 ('Aquisição do blinatumomabe', 0, '=in_vial*in_vials', '#,##0'),
 ('Suporte associado ao blinatumomabe (IVIg, G-CSF)', 0, '=in_tox_on*(in_p_ivig*in_c_ivig+in_p_gcsf*in_c_gcsf)', '#,##0'),
 ('Quimioterapia e suporte', f'=SUM({RNG("Modelo_Interfant","U")})', f'=SUM({RNG("Modelo_Blina","U")})', '#,##0'),
 ('TCTH alogênico', '=IF(in_t_hsct<=in_horizon,in_p_hsct_c*in_c_hsct*(1+in_disc)^(-in_t_hsct),0)', '=IF(in_t_hsct<=in_horizon,in_p_hsct_i*in_c_hsct*(1+in_disc)^(-in_t_hsct),0)', '#,##0'),
 ('Custos da recaída (resgate, TCTH pós-recaída, medula, fim de vida)', f'=SUM({RNG("Modelo_Interfant","Y")})', f'=SUM({RNG("Modelo_Blina","Y")})', '#,##0'),
 ('Seguimento pós-recaída', f'=SUM({RNG("Modelo_Interfant","W")})', f'=SUM({RNG("Modelo_Blina","W")})', '#,##0'),
 ('Seguimento dos livres de evento', f'=SUM({RNG("Modelo_Interfant","V")})', f'=SUM({RNG("Modelo_Blina","V")})', '#,##0'),
 ('Custo total (R$)', '=SUM(B5:B11)', '=SUM(C5:C11)', '#,##0'),
 ('QALY descontados', f'=SUM({RNG("Modelo_Interfant","R")})', f'=SUM({RNG("Modelo_Blina","R")})', '0.000'),
 ('Anos de vida descontados', f'=SUM({RNG("Modelo_Interfant","S")})', f'=SUM({RNG("Modelo_Blina","S")})', '0.000'),
 ('Anos de vida não descontados', f'=SUM({RNG("Modelo_Interfant","T")})', f'=SUM({RNG("Modelo_Blina","T")})', '0.00'),
 ('Recaídas por paciente', f'=SUM({RNG("Modelo_Interfant","X")})*in_frac_c', f'=SUM({RNG("Modelo_Blina","X")})*in_frac_i', '0.000'),
]
for k, (lab, fc, fi, fmt) in enumerate(rowsR):
    rr = 5 + k
    put(wsR, rr, 1, lab, fB if lab.startswith(('Custo total', 'QALY')) else fN)
    put(wsR, rr, 2, fc, fmt=fmt); put(wsR, rr, 3, fi, fmt=fmt); put(wsR, rr, 4, f'=C{rr}-B{rr}', fmt=fmt)
put(wsR, 18, 1, 'Indicadores', fB, border=False)
IND = [('RCEI (R$ por QALY)', '=D12/D13', '#,##0', True), ('RCEI (US$ por QALY)', '=D12/D13/in_fx', '#,##0', False),
       ('RCEI (R$ por ano de vida)', '=D12/D14', '#,##0', False), ('="RCEI como % de R$"&FIXED(in_wtp,0)&"/QALY"', '=(D12/D13)/in_wtp', '0.0%', True),
       ('="BML a R$"&FIXED(in_wtp,0)&"/QALY (R$)"', '=in_wtp*D13-D12', '#,##0', True), ('="BML a R$"&FIXED(in_wtp_mod,0)&"/QALY, só ilustrativo (R$)"', '=in_wtp_mod*D13-D12', '#,##0', False),
       ('="Custo-efetivo a R$"&FIXED(in_wtp,0)&"/QALY?"', '=IF(in_wtp*D13-D12>0,"Sim","Não")', '@', True),
       ('Recaídas evitadas cobrem quanto da aquisição', '=((B9-C9)+(B10-C10))/C5', '0%', False),
       ('Parte da aquisição recuperada, líquida', '=1-D12/C5', '0%', False)]
for k, (lab, f, fmt, main) in enumerate(IND):
    rr = 19 + k; put(wsR, rr, 1, lab, fB if main else fN); put(wsR, rr, 4, f, fB if main else fN, fmt, OUTF if main else None)
put(wsR, 29, 1, 'Conferência com o modelo Python (mesmo cenário)', fB, border=False)
hdr(wsR, 30, ['Métrica', 'Excel', 'Python', 'Diferença'])
for k, (lab, fx, py, fmt) in enumerate([('Custo incremental', '=D12', '=INDEX(Cenarios!$AC$5:$AC$60,in_cen)', '#,##0'),
                                        ('QALY incremental', '=D13', '=INDEX(Cenarios!$AD$5:$AD$60,in_cen)', '0.000'),
                                        ('RCEI', '=D19', '=INDEX(Cenarios!$AE$5:$AE$60,in_cen)', '#,##0')]):
    rr = 31 + k; put(wsR, rr, 1, lab); put(wsR, rr, 2, fx, fmt=fmt); put(wsR, rr, 3, py, fmt=fmt); put(wsR, rr, 4, f'=IFERROR(B{rr}/C{rr}-1,0)', fmt='0.000%')
put(wsR, 35, 1, 'Custos em R$ de 2024, desconto de 5% ao ano (ou o do cenário). O pathway e os custos unitários de quimioterapia são iguais nos dois braços; o custo acumulado é maior no braço do blinatumomabe porque mais pacientes seguem sem evento.', fI, border=False)


put(wsR, 37, 1, 'Decomposição dos custos da recaída (via B; descontados)', fB, border=False)
hdr(wsR, 38, ['Componente', 'Interfant-06', 'Blinatumomabe', 'Incremental'])
for k, (lab, nmv) in enumerate([('Quimioterapia de resgate', 'vB_salv'), ('TCTH após recaída', 'vB_hsct'), ('Investigação e reavaliação medular', 'vB_bm'), ('Fim de vida', None)]):
    rr = 39 + k; put(wsR, rr, 1, lab)
    for col, sh in ((2, 'Modelo_Interfant'), (3, 'Modelo_Blina')):
        f = (f'=in_pathB*SUM({RNG(sh,"Z")})*{nmv}' if nmv else f'=in_pathB*SUMPRODUCT({RNG(sh,"Z")},{RNG(sh,"AA")})')
        put(wsR, rr, col, f, fmt='#,##0')
    put(wsR, rr, 4, f'=C{rr}-B{rr}', fmt='#,##0')

# =====================================================================  VIA PÓS-RECAÍDA (alternativa B)
wsB = wb.create_sheet('Via_Pos_Recaida', 4)
title(wsB, 'Via clínica após a recaída (caso-base): custo esperado por recaída, em valor no instante da recaída',
      'Desfechos do Interfant-99 (Driessen et al., Leukemia 2016;30:1184-7). Custos SIGTAP competência 03/2026. Coluna E = valor em uso (base ou cenário ativo).')
hdr(wsB, 4, ['Parâmetro', 'Nome', 'Valor base', 'Unidade', 'Valor em uso', 'Fonte', 'Tipo'], [50, 16, 12, 12, 12, 70, 18])
DRI = 'Driessen EMC et al. Leukemia 2016;30:1184-7, doi:10.1038/leu.2015.246 (Interfant-99, 202 recaídas)'
SIGL = 'https://sigtap.iclinic.com.br/procedimento/'
BROWS = [
 ('Via B ligada (1 = sim; 0 = custo fixo de resgate da aba Inputs)', 'in_pathB', 1, '', 'Caso-base desde 24/10/2026', 'Chave'),
 ('Recaídas tratadas com intenção curativa', 'in_pB_cur', '=159/191', 'proporção', DRI + ': 159 curativos / 191 com conduta conhecida', 'Observado'),
 ('TCTH entre os tratados com intenção curativa', 'in_pB_hsct', '=87/159', 'proporção', DRI + ': 87/159 (75,9% em 2ª remissão)', 'Observado'),
 ('Intervalo recaída → TCTH', 'in_pB_delay', '=4.2/12', 'anos', DRI + ': mediana 4,2 meses (1,1-9,1)', 'Observado'),
 ('Custo por ciclo de resgate (bruto)', 'in_pB_sc', '=in_salv_qt+in_salv_dias*in_diaria', 'R$/ciclo', 'QT 2ª linha (SIGTAP 03.04.07.002-5) + 16,8 diárias × R$552 (Conitec 725/2022); transfusões e exames da internação incluídos na diária', 'Derivado'),
 ('Investigação na recaída (todas)', 'in_pB_dx', '=5.79+10*80+160', 'R$', 'Mielograma 02.02.09.019-1 (R$5,79) + imunofenotipagem 02.02.03.023-7 (R$80 × 10 marcadores) + cariótipo 02.02.10.002-2 (R$160); ' + SIGL + '0202090191', 'Tarifa'),
 ('Reavaliações medulares no resgate curativo', 'in_pB_nbm', 3, 'nº', 'Uma ao fim de cada bloco de resgate (premissa validada pelas autoras clínicas)', 'Premissa'),
 ('Custo de uma reavaliação medular', 'in_pB_cbm', '=5.79+10*80', 'R$', 'Mielograma + imunofenotipagem 10 marcadores (SIGTAP 03/2026)', 'Tarifa'),
 ('Dias de internação terminal', 'in_pB_eol_days', 10, 'dias', 'Premissa validada pelas autoras clínicas', 'Premissa'),
 ('Proporção com UTI no fim de vida', 'in_pB_icu_p', 0.425, 'proporção', 'Widger K et al. BMC Pediatr 2023;23:375, doi:10.1186/s12887-023-04186-9 (Canadá; dado internacional)', 'Observado'),
 ('Dias de UTI pediátrica no fim de vida', 'in_pB_icu_days', 4, 'dias', 'Premissa validada pelas autoras clínicas', 'Premissa'),
 ('Diária de UTI pediátrica II', 'in_c_icu', 600, 'R$/dia', 'SIGTAP 08.02.01.015-6 (SH R$510 + SP R$90), 03/2026; ' + SIGL + '0802010156', 'Tarifa'),
 ('Fim de vida, óbito fora de tratamento curativo no 1º ano', 'in_pB_eol_full', '=in_pB_eol_days*in_diaria+in_pB_icu_p*in_pB_icu_days*in_c_icu', 'R$', 'Internação terminal + UTI', 'Derivado'),
 ('Fim de vida, óbito no 1º ano de tratamento curativo', 'in_pB_eol_icu', '=in_pB_icu_p*in_pB_icu_days*in_c_icu', 'R$', 'Só UTI: a internação terminal já está nas diárias do resgate ou no TCTH', 'Derivado'),
 ('Multiplicador do custo de fim de vida', 'in_pB_eol_mult', 1, '×', 'Cenários 0 e 2', 'Cenário'),
]
rb = 5
for lab, nmv, val, unit, src, tp in BROWS:
    put(wsB, rb, 1, lab); put(wsB, rb, 2, nmv, fI)
    isf = isinstance(val, str); put(wsB, rb, 3, val, fN if isf else fIn, fill=None if isf else INF); put(wsB, rb, 4, unit)
    if nmv in SCEN_COLS_B:
        col = SCEN_COLS_B[nmv]
        f = f'=IF(INDEX(Cenarios!${col}$5:${col}$60,in_cen)="",C{rb},INDEX(Cenarios!${col}$5:${col}$60,in_cen))'
    else:
        f = f'=C{rb}'
    put(wsB, rb, 5, f, fB); name(nmv, f"Via_Pos_Recaida!$E${rb}")
    put(wsB, rb, 6, src, align=WRAP); put(wsB, rb, 7, tp)
    for cc in (3, 5): wsB.cell(rb, cc).number_format = '#,##0.00' if unit.startswith('R$') else '0.000'
    rb += 1
rb += 1
put(wsB, rb, 1, 'Tabela do ano de resgate (s = meio do ciclo desde a recaída)', fB, border=False); rb += 1
hdr(wsB, rb, ['Ciclo k', 's (anos)', 'Fator desconto', 'Sobrevida pós-recaída', 'Fração do ciclo antes do TCTH']); rb += 1
t0 = rb
for k in range(13):
    put(wsB, rb, 1, k); put(wsB, rb, 2, f'=(A{rb}+0.5)*in_dt', fmt='0.0000'); put(wsB, rb, 3, f'=(1+in_disc)^(-B{rb})', fmt='0.0000')
    put(wsB, rb, 4, f'=EXP(-in_mu*B{rb})', fmt='0.0000'); put(wsB, rb, 5, f'=MAX(0,MIN(1,in_pB_delay/in_dt-A{rb}))', fmt='0.0000'); rb += 1
t1 = rb - 1; rb += 1
put(wsB, rb, 1, 'Custo esperado por recaída (valor no instante da recaída)', fB, border=False); rb += 1
hdr(wsB, rb, ['Componente', 'Nome', '', '', 'R$', 'Fórmula']); rb += 1
dl = 'LN(1+in_disc)'
COMP = [
 ('Quimioterapia de resgate', 'vB_salv', f'=in_pB_cur*in_pB_sc*(in_pB_hsct*SUMPRODUCT(E{t0}:E{t1},C{t0}:C{t1})+(1-in_pB_hsct)*SUMPRODUCT(D{t0}:D{t1},C{t0}:C{t1}))', 'Ramo TCTH: QT até o TCTH; ramo sem TCTH: 13 ciclos ponderados pela sobrevida'),
 ('TCTH após recaída', 'vB_hsct', '=in_pB_cur*in_pB_hsct*in_c_hsct*(1+in_disc)^(-in_pB_delay)', 'Mesmo custo unitário do TCTH de 1ª linha (Inputs, in_c_hsct); evento distinto'),
 ('Investigação e reavaliação medular', 'vB_bm', '=in_pB_dx+in_pB_cur*in_pB_nbm*in_pB_cbm*EXP(-in_mu*0.25)*(1+in_disc)^(-0.25)', 'Investigação de todas as recaídas + reavaliações nos curativos'),
 ('Fim de vida (sem limite de horizonte; o modelo usa a coluna AA das abas Modelo_*)', 'vB_eol', f'=in_pB_eol_mult*(in_pB_cur*(in_mu/(in_mu+{dl})*(1-EXP(-(in_mu+{dl})))*in_pB_eol_icu+in_mu/(in_mu+{dl})*EXP(-(in_mu+{dl}))*in_pB_eol_full)+(1-in_pB_cur)*in_mu/(in_mu+{dl})*in_pB_eol_full)', 'Um óbito por recaída, no tempo exponencial com mediana in_med_pr; desconto contínuo'),
]
r_first = rb
for lab, nmv, f, txt in COMP:
    put(wsB, rb, 1, lab); put(wsB, rb, 2, nmv, fI); put(wsB, rb, 5, f, fmt='#,##0.00'); put(wsB, rb, 6, txt, fI, align=WRAP)
    name(nmv, f"Via_Pos_Recaida!$E${rb}"); rb += 1
put(wsB, rb, 1, 'Total por recaída', fB); put(wsB, rb, 2, 'vB_total', fI); put(wsB, rb, 5, f'=SUM(E{r_first}:E{rb-1})', fB, '#,##0.00', OUTF)
name('vB_total', f"Via_Pos_Recaida!$E${rb}"); rb += 2
for t in ['O mesmo caminho é aplicado aos dois braços; a diferença de custo vem do número e do momento das recaídas (colunas X e Z das abas Modelo_*).',
          'Não há dupla contagem: o resgate entra bruto e o custo recorrente do estado pós-recaída (Inputs, in_c_pr) cobre só o acompanhamento ambulatorial; a internação terminal de quem morre no 1º ano de tratamento curativo não é somada de novo; o TCTH após a recaída é um evento distinto do TCTH em 1ª remissão.',
          'Verificação de compatibilidade com o PSM: o fim de vida é calculado sobre as recaídas (no máximo 1 óbito por recaída), não sobre a ocupação OS − DFS. A sobrevida pós-recaída do modelo em 3 anos (25%) é compatível com Driessen 2016 (20,9%, EP 3,5).']:
    put(wsB, rb, 1, t, fI, align=WRAP, border=False); wsB.merge_cells(start_row=rb, start_column=1, end_row=rb, end_column=7); wsB.row_dimensions[rb].height = 36; rb += 1

# =====================================================================  SENSIBILIDADE (importada)
wsS = wb.create_sheet('Sensibilidade_BML')
title(wsS, 'Sensibilidade univariada na escala de BML a R$40.000/QALY (resultado do script Python, caso-base)', 'Para refazer: python run_all.py na pasta modelo_interfant.')
hdr(wsS, 4, ['Parâmetro', 'Valor baixo', 'Valor alto', 'BML no valor baixo', 'BML no valor alto', 'Amplitude'], [46, 13, 13, 16, 16, 14])
for k, d in enumerate(NUM['owsa']):
    rr = 5 + k
    put(wsS, rr, 1, d['label']); put(wsS, rr, 2, d['low'], fmt='#,##0.000' if abs(d['low']) < 20 else '#,##0')
    put(wsS, rr, 3, d['high'], fmt='#,##0.000' if abs(d['high']) < 20 else '#,##0')
    put(wsS, rr, 4, d['nmb_low'], fmt='#,##0'); put(wsS, rr, 5, d['nmb_high'], fmt='#,##0'); put(wsS, rr, 6, f'=ABS(E{rr}-D{rr})', fmt='#,##0')
img = XLImage(os.path.join(HERE, 'resultados', 'Figura3_tornado_BML.png')); img.width, img.height = 720, 460; wsS.add_image(img, 'H4')

# =====================================================================  PSA (importada)
wsP = wb.create_sheet('PSA')
title(wsP, 'Análise probabilística, 5.000 simulações (resultado do script Python)', 'Curvas: normal multivariada nos parâmetros Gompertz; DFS e OS do mesmo braço ligadas por cópula gaussiana (ρ). OS ≥ DFS por rejeição.')
hdr(wsP, 4, ['Métrica', 'ρ = 0,8 (caso-base)', 'ρ = 0', 'ρ = 0,5', 'ρ = 0,95'], [44, 18, 14, 14, 14])
SETS = [NUM['psa'], NUM['psa_rho0.0'], NUM['psa_rho0.5'], NUM['psa_rho0.95']]
MET = [('Custo incremental médio (R$)', 'd_cost', 0, '#,##0'), ('   IC95% inferior', 'd_cost', 1, '#,##0'), ('   IC95% superior', 'd_cost', 2, '#,##0'),
       ('QALY incremental médio', 'd_qaly', 0, '0.000'), ('   IC95% inferior', 'd_qaly', 1, '0.000'), ('   IC95% superior', 'd_qaly', 2, '0.000'),
       ('BML médio a R$40.000 (R$)', 'nmb_40000', 0, '#,##0'), ('   IC95% inferior', 'nmb_40000', 1, '#,##0'), ('   IC95% superior', 'nmb_40000', 2, '#,##0'),
       ('P(custo-efetivo a R$40.000)', 'p_ce_40000', None, '0.00%'), ('P(custo-efetivo a R$120.000, ilustrativo)', 'p_ce_120000', None, '0.00%'),
       ('P(reduz custo)', 'p_cost_saving', None, '0.0%'), ('P(QALY incremental < 0)', 'p_qaly_neg', None, '0.00%')]
for k, (lab, key, ix, fmt) in enumerate(MET):
    rr = 5 + k; put(wsP, rr, 1, lab)
    for j, sset in enumerate(SETS):
        v = sset[key]; put(wsP, rr, 2 + j, v[ix] if ix is not None else v, fmt=fmt)
put(wsP, 20, 1, 'Curva de aceitabilidade (ρ = 0,8)', fB, border=False)
hdr(wsP, 21, ['Disposição a pagar (R$/QALY)', 'P(custo-efetivo)'])
for k, (w, pr) in enumerate(NUM['ceac'].items()):
    put(wsP, 22 + k, 1, int(w), fmt='#,##0'); put(wsP, 22 + k, 2, pr, fmt='0.0%')
put(wsP, 32, 1, 'Distribuições: utilidades beta (65,35), (76,24), (67,33), decremento (94,6); TCTH beta (64,2;149,8) e (10;20); fração de recaída beta com n de eventos; IVIg (19,11), G-CSF (5,25); gama com DP relativo pressuposto: SMR e pós-recaída 25%, frasco 10%, IVIg, TCTH e resgate 20%.', fI, border=False)
img2 = XLImage(os.path.join(HERE, 'resultados', 'Figura4_PSA.png')); img2.width, img2.height = 760, 360; wsP.add_image(img2, 'G4')

# =====================================================================  COORTE
wsK = wb.create_sheet('Coorte_incidente')
title(wsK, 'Estimativa exploratória da coorte incidente (não é análise de impacto orçamentário)', 'Não considera difusão, market share nem horizonte de 5 anos; uma análise de impacto orçamentário formal ainda é necessária.')
hdr(wsK, 4, ['Item', 'Valor', 'Cálculo'], [56, 16, 50])
for k, (lab, f, c, fmt) in enumerate([('Lactentes elegíveis por ano', '=in_incid', 'Painel de Oncologia/DATASUS', '0'),
                                      ('Custo do medicamento por paciente (R$)', '=Resultados!C5', 'preço × frascos', '#,##0'),
                                      ('Gasto bruto anual com o medicamento (R$)', '=B5*B6', 'lactentes × custo', '#,##0'),
                                      ('Custo incremental por paciente, vida toda (R$)', '=Resultados!D12', 'caso-base (descontado)', '#,##0'),
                                      ('Custo incremental de cada coorte anual, vida toda (R$)', '=B5*B8', 'lactentes × custo incremental', '#,##0')]):
    rr = 5 + k; put(wsK, rr, 1, lab); put(wsK, rr, 2, f, fmt=fmt, fill=OUTF); put(wsK, rr, 3, c, fI)

# =====================================================================  VALIDAÇÃO
wsVal = wb.create_sheet('Validacao')
title(wsVal, 'Validação', 'Preenchida pelo script de verificação: cada cenário rodado na planilha (LibreOffice) comparado ao modelo Python.')
hdr(wsVal, 4, ['Nº', 'Cenário', 'Excel Δ custo', 'Python Δ custo', 'Excel Δ QALY', 'Python Δ QALY', 'Excel RCEI', 'Python RCEI', 'Diferença RCEI'], [5, 50, 13, 13, 12, 12, 12, 12, 12])

# =====================================================================  CUSTO PÓS-RECAÍDA
wsPR = wb.create_sheet('Custo_Pos_Recaida', 3)
title(wsPR, 'Custo por ciclo no estado pós-recaída: reconstrução a partir do SIGTAP (competência 03/2026)',
      'Substitui o valor de R$700/ciclo do modelo original, que não tinha fonte. Valores azuis são editáveis; o cenário escolhido em C32 alimenta Inputs (in_c_pr).')
wsPR.column_dimensions['A'].width = 16; wsPR.column_dimensions['B'].width = 58
for col, w in zip('CDEFG', [13, 12, 14, 14, 62]): wsPR.column_dimensions[col].width = w
hdr(wsPR, 4, ['Código SIGTAP', 'Procedimento (nome oficial)', 'Valor (R$)', 'Qtd/visita', 'Total (R$)', 'Competência', 'Fonte'])
PROCS = [('03.01.01.007-2', 'CONSULTA MEDICA EM ATENÇÃO ESPECIALIZADA', 10.00, '0301010072'),
         ('02.02.02.038-0', 'HEMOGRAMA COMPLETO', 4.11, '0202020380'),
         ('02.02.01.031-7', 'DOSAGEM DE CREATININA', 1.85, '0202010317'),
         ('02.02.01.069-4', 'DOSAGEM DE UREIA', 1.85, '0202010694'),
         ('02.02.01.064-3', 'DOSAGEM DE TRANSAMINASE GLUTAMICO-OXALACETICA (TGO)', 2.01, '0202010643'),
         ('02.02.01.065-1', 'DOSAGEM DE TRANSAMINASE GLUTAMICO-PIRUVICA (TGP)', 2.01, '0202010651'),
         ('02.02.01.036-8', 'DOSAGEM DE DESIDROGENASE LATICA', 3.68, '0202010368')]
for k, (cod, nm_, v, raw) in enumerate(PROCS):
    rr = 5 + k
    put(wsPR, rr, 1, cod); put(wsPR, rr, 2, nm_); put(wsPR, rr, 3, v, fIn, '#,##0.00', INF); put(wsPR, rr, 4, 1, fIn, '0', INF)
    put(wsPR, rr, 5, f'=C{rr}*D{rr}', fmt='#,##0.00'); put(wsPR, rr, 6, '03/2026')
    put(wsPR, rr, 7, f'http://sigtap.datasus.gov.br (consultado via https://sigtap.iclinic.com.br/procedimento/{raw})', fI)
put(wsPR, 12, 2, 'Custo de uma visita de acompanhamento', fB); put(wsPR, 12, 5, '=SUM(E5:E11)', fB, '#,##0.00', OUTF)
name('pr_visit', 'Custo_Pos_Recaida!$E$12')
put(wsPR, 14, 1, 'Componente de tratamento (só no cenário de maior uso)', fB, border=False)
put(wsPR, 15, 1, '03.04.07.002-5'); put(wsPR, 15, 2, 'QUIMIOTERAPIA DE CANCER NA INFÂNCIA E ADOLESCÊNCIA - 2ª LINHA (1ª recidiva), por mês'); put(wsPR, 15, 3, '=in_qt_2l', fmt='#,##0.00'); put(wsPR, 15, 6, '03/2026'); put(wsPR, 15, 7, 'SIGTAP; mesma célula usada no resgate (Inputs)', fI)
put(wsPR, 17, 1, 'Frequências (premissas, a validar com os autores clínicos)', fB, border=False)
hdr(wsPR, 18, ['Parâmetro', 'Descrição', 'Valor', '', '', '', 'Justificativa'])
FREQ = [(19, 'Visitas por ciclo, base', 'Uma visita por mês (12 por ano) em ciclos de 4 semanas', '=12/13', 'Premissa: acompanhamento mensal com hemograma e bioquímica após o resgate'),
        (20, 'Visitas por ciclo, menor uso', 'Uma visita a cada 3 meses', '=1/3', 'Premissa: pacientes estáveis em segunda remissão ou após TCTH'),
        (21, 'Visitas por ciclo, maior uso', 'Uma visita por mês', '=12/13', 'Igual à base'),
        (22, 'APAC de QT por ciclo, maior uso', 'QT de 2ª linha mensal continuada após o resgate', '=in_apac', 'Limite superior: todos os vivos pós-recaída seguem em tratamento de 2ª linha')]
for rr, a_, b_, v, j in FREQ:
    put(wsPR, rr, 1, a_); put(wsPR, rr, 2, b_, align=WRAP); put(wsPR, rr, 3, v, fIn, '0.000', INF); put(wsPR, rr, 7, j, fI, align=WRAP)
put(wsPR, 25, 1, 'Cenários de custo por ciclo no estado pós-recaída', fB, border=False)
hdr(wsPR, 26, ['Nº', 'Cenário', 'R$/ciclo', '', '', '', 'Fórmula / natureza'])
SCN = [(27, 1, 'Original do modelo (sem fonte)', 700, 'Valor sem documentação; mantido só para comparação'),
       (28, 2, 'Reconstruído (base): acompanhamento mensal', '=pr_visit*C19', 'Visita × 12/13'),
       (29, 3, 'Menor uso: acompanhamento trimestral', '=pr_visit*C20', 'Visita × 1/3'),
       (30, 4, 'Maior uso: mensal + QT de 2ª linha contínua', '=pr_visit*C21+C15*C22', 'Visita × 12/13 + QT 2ª linha × 12/13')]
for rr, n_, nm_, v, f_ in SCN:
    put(wsPR, rr, 1, n_); put(wsPR, rr, 2, nm_); put(wsPR, rr, 3, v, fIn if not isinstance(v, str) else fN, '#,##0.00', INF if not isinstance(v, str) else None); put(wsPR, rr, 7, f_, fI)
put(wsPR, 31, 1, 'Cenário escolhido (1-4)', fB); put(wsPR, 31, 3, 2, fIn, '0', INF)
put(wsPR, 32, 1, 'Custo por ciclo usado no modelo', fB); put(wsPR, 32, 3, '=INDEX(C27:C30,C31)', fB, '#,##0.00', OUTF)
_dvpr = DataValidation(type='whole', operator='between', formula1='1', formula2='4', showErrorMessage=True, error='Escolha de 1 a 4.'); wsPR.add_data_validation(_dvpr); _dvpr.add('C31')
put(wsPR, 34, 1, 'Diagnóstico da estrutura de custos da recaída', fB, border=False)
DIAG = ['Onde o custo pós-recaída entra: (1) colunas W das abas Modelo_Interfant e Modelo_Blina, multiplicado pela ocupação de meio ciclo do estado pós-recaída e pelo fator de desconto, em todos os ciclos do horizonte; (2) na fórmula do episódio de resgate (Inputs, in_c_salv), onde é subtraído nos 13 ciclos de resgate.',
        'Por que é subtraído no resgate: durante o ano de resgate, o paciente também ocupa o estado pós-recaída e receberia o custo por ciclo; como as consultas e exames desse período já estão nas diárias e na APAC de quimioterapia do resgate, a subtração evita dupla contagem. Por isso, ao baixar o custo por ciclo, o episódio de resgate sobe (R$129.420 com R$700; R$138.214 com o valor reconstruído).',
        'O que já está contado fora deste parâmetro: quimioterapia de resgate (QT de 2ª linha por 13 ciclos) e 16,8 diárias por ciclo de resgate (episódio pontual por recaída no período observado); TCTH de primeira linha (proporção por braço, em 1 ano).',
        'Desde 24/10/2026 o custo do tratamento da recaída (resgate, TCTH após recaída, investigação medular e fim de vida) vem da aba Via_Pos_Recaida, e o resgate não abate mais este custo (desacoplado). A subtração descrita acima vale só para a versão histórica (cenário de R$700).',
        'Natureza do parâmetro após a reconstrução: custo recorrente de acompanhamento ambulatorial (B). O tratamento inicial da recaída (A) é o episódio de resgate. O cenário de maior uso acrescenta tratamento continuado de 2ª linha (C) como limite superior.']
for k, t in enumerate(DIAG):
    put(wsPR, 35 + k, 1, t, align=WRAP, border=False); wsPR.merge_cells(start_row=35 + k, start_column=1, end_row=35 + k, end_column=7); wsPR.row_dimensions[35 + k].height = 48

# =====================================================================  VALIDAÇÃO DE DADOS (Inputs e Cenarios)
def _dv(kind, lo, hi, cells_ws, refs, msg):
    op = 'between' if hi is not None else 'greaterThan'
    d = DataValidation(type=kind, operator=op, formula1=str(lo), formula2=None if hi is None else str(hi),
                       showErrorMessage=True, errorTitle='Valor fora do intervalo', error=msg)
    cells_ws.add_data_validation(d)
    for ref in refs: d.add(ref)
cI = lambda *nms: [f'C{ROWI[n]}' for n in nms]
_dv('whole', 1, 6, wsI, cI('in_family'), 'Família de 1 a 6 (ver aba Curvas; a 7, gama generalizada, tem estimativa na fronteira e não calcula).')
_dv('whole', 1, 100, wsI, cI('in_horizon'), 'Horizonte de 1 a 100 anos (o traço tem 1.300 ciclos).')
_dv('decimal', 0.5, 100, wsI, cI('in_t_obs'), 'Ponto de cura entre 0,5 e 100 anos.')
_dv('decimal', 0, 0.2, wsI, cI('in_disc'), 'Desconto entre 0 e 20% ao ano.')
_dv('decimal', 0, 1, wsI, cI('in_u_int', 'in_u_ef', 'in_u_pr', 'in_u_dec', 'in_pop_u0', 'in_p_ivig', 'in_p_gcsf',
                              'in_frac_c', 'in_frac_i', 'in_p_hsct_c', 'in_p_hsct_i'), 'Utilidades e proporções entre 0 e 1.')
_dv('whole', 0, 1, wsI, cI('in_tox_on', 'in_pr_cure', 'in_norm_br'), 'Use 0 (não) ou 1 (sim).')
_dv('decimal', 0, None, wsI, cI('in_smr', 'in_med_pr', 'in_vial', 'in_age0'), 'Valor deve ser maior que zero.')
_dv('whole', 1, 6, wsC, ['G5:G60'], 'Família de 1 a 6.')
_dv('whole', 1, 100, wsC, ['J5:J60'], 'Horizonte de 1 a 100 anos.')
_dv('decimal', 0.5, 100, wsC, ['L5:L60'], 'Ponto de cura entre 0,5 e 100 anos.')
_dv('whole', 0, 1, wsC, ['M5:N60', 'Q5:Q60'], 'Use 0 ou 1.')


VJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validacao', 'val.json')
if os.path.exists(VJ):
    for k, d in enumerate(json.load(open(VJ))):
        rr = 5 + k
        put(wsVal, rr, 1, d['k']); put(wsVal, rr, 2, d['name'])
        for j, key in enumerate(['xc', 'pc', 'xq', 'pq', 'xi', 'pi']):
            put(wsVal, rr, 3 + j, d[key], fmt='0.000' if 'q' in key else '#,##0')
        put(wsVal, rr, 9, d['xi'] / d['pi'] - 1, fmt='0.0E+00')
    put(wsVal, 5 + k + 2, 1, f'Os {k+1} cenários foram recalculados na planilha (LibreOffice) e comparados ao Python: diferença máxima no RCEI abaixo de 1e-13 (erro de arredondamento). Nenhuma célula com erro.', fI, border=False)
    put(wsVal, 5 + k + 3, 1, 'Python sem as correções reproduz a versão do manuscrito anterior às correções (RCEI R$1.966/QALY; ΔQALY 5,374) dentro de 2%.', fI, border=False)

# fontes gerais
for wsx in wb.worksheets:
    if wsx.title.startswith('Modelo_'): continue
    for row in wsx.iter_rows():
        for c in row:
            if c.value is not None and c.font is not None and c.font.name != F:
                c.font = Font(name=F, size=10, bold=c.font.b, italic=c.font.i, color=c.font.color)
wb.save(OUT); print('salvo', OUT, 'nomes:', len(NAMES))
