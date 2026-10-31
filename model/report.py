"""Planilha de resultados e figuras."""
import os
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import inputs, model, psa

F = 'Arial'
H = Font(name=F, bold=True, color='FFFFFF'); HF = PatternFill('solid', fgColor='1F4E79')
B = Font(name=F); BB = Font(name=F, bold=True); T = Font(name=F, bold=True, size=13); IT = Font(name=F, italic=True, size=9)
YEL = PatternFill('solid', fgColor='FFF2CC'); RED = PatternFill('solid', fgColor='F8CBAD')


def _hdr(ws, r, vals, widths=None):
    for j, v in enumerate(vals, 1):
        c = ws.cell(r, j, v); c.font = H; c.fill = HF; c.alignment = Alignment(wrap_text=True, vertical='center')
    if widths:
        for j, w in enumerate(widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = w


def _title(ws, text, sub=None):
    ws['A1'] = text; ws['A1'].font = T
    if sub: ws['A2'] = sub; ws['A2'].font = IT


def _fmt(c, f):
    c.number_format = f


def write_xlsx(R, path, MS, APPROX):
    wb = openpyxl.Workbook()
    pb = R['base_corr']['p']; sb = R['base_corr']['s']; so = R['base_orig']['s']

    # ------------ LEIA-ME
    ws = wb.active; ws.title = 'Leia-me'
    ws.column_dimensions['A'].width = 125
    lines = [
        ('Modelo de sobrevida particionada: blinatumomabe em primeira linha na LLA do lactente KMT2A-r (perspectiva SUS)', T),
        ('Resultados do modelo em Python (caso-base, cenários, sensibilidade univariada e PSA).', B),
        ('', B),
        ('Abas', BB),
        ('Inputs: todos os parâmetros, fonte, ano de valoração, fator IPCA e status (amarelo = premissa testada em cenário).', B),
        ('Caso_base: resultado corrigido, comparação com o manuscrito e custos desagregados (equivalente à tabela 5).', B),
        ('Cenarios: equivalente à tabela 4, já com as correções, mais os cenários novos.', B),
        ('Sensibilidade_BML: análise univariada na escala de benefício monetário líquido (figura 3).', B),
        ('PSA e CEAC: resultados probabilísticos (figura 4).', B),
        ('Coorte_incidente: estimativa exploratória.', B),
        ('Validacao: reconstrução sem as correções comparada à tabela 4 do manuscrito.', B),
        ('', B),
        ('Observação', BB),
        ('A aba Validacao compara a versão sem as correções com uma versão anterior do manuscrito; não faz parte dos resultados publicados.', B),
    ]
    for k, (t, f) in enumerate(lines, 1):
        c = ws.cell(k, 1, t); c.font = f; c.alignment = Alignment(wrap_text=True, vertical='top')

    # ------------ Inputs
    ws = wb.create_sheet('Inputs'); _title(ws, 'Inputs do modelo, fontes e status')
    _hdr(ws, 3, ['Parâmetro', 'Valor na fonte', 'Unidade', 'Ano de valoração', 'Fator IPCA até 2024', 'Valor usado (R$ 2024)', 'Fonte', 'Status', 'Observação'],
         [22, 14, 14, 11, 11, 16, 70, 11, 70])
    r = 4
    for k, d in inputs.P.items():
        ws.cell(r, 1, k); ws.cell(r, 2, d['value'] if not isinstance(d['value'], str) else d['value']); ws.cell(r, 3, d['unit'])
        if d['year'] is not None:
            ws.cell(r, 4, d['year']); f = inputs.ipca_factor(d['year'])
            ws.cell(r, 5, f); _fmt(ws.cell(r, 5), '0.0000')
            if d['year'] != 2024: ws.cell(r, 6, f'=B{r}*E{r}'); _fmt(ws.cell(r, 6), '#,##0.00')
        ws.cell(r, 7, d['source']); ws.cell(r, 8, d['status']); ws.cell(r, 9, d['note'])
        if d['status'] == 'premissa': ws.cell(r, 8).fill = YEL
        if d['status'] == 'pendente': ws.cell(r, 8).fill = RED
        for j in (7, 9): ws.cell(r, j).alignment = Alignment(wrap_text=True, vertical='top')
        r += 1
    r += 1
    ws.cell(r, 1, 'IPCA anual (dez/dez), IBGE').font = BB; r += 1
    for y, v in inputs.IPCA.items():
        ws.cell(r, 1, y); ws.cell(r, 2, v); _fmt(ws.cell(r, 2), '0.00%'); r += 1

    # ------------ Caso-base
    ws = wb.create_sheet('Caso_base'); _title(ws, 'Caso-base corrigido (R$ de 2024, desconto de 5%)')
    _hdr(ws, 3, ['Resultado', 'Interfant-06', 'Blinatumomabe', 'Incremental'], [44, 16, 16, 16])
    c = R['base_corr']['c']; i = R['base_corr']['i']
    rows = [('Custo total (R$)', 'cost', '#,##0'), ('QALY descontados', 'qaly', '0.000'), ('Anos de vida descontados', 'ly_d', '0.000'),
            ('Anos de vida não descontados', 'ly_u', '0.000')]
    r = 4
    for lab, k, f in rows:
        ws.cell(r, 1, lab); ws.cell(r, 2, c[k]); ws.cell(r, 3, i[k]); ws.cell(r, 4, f'=C{r}-B{r}')
        for j in (2, 3, 4): _fmt(ws.cell(r, j), f)
        r += 1
    ws.cell(r, 1, 'RCEI (R$/QALY)'); ws.cell(r, 4, '=D4/D5'); _fmt(ws.cell(r, 4), '#,##0'); r += 1
    ws.cell(r, 1, 'RCEI (R$/ano de vida)'); ws.cell(r, 4, '=D4/D6'); _fmt(ws.cell(r, 4), '#,##0'); r += 1
    ws.cell(r, 1, 'RCEI como % de R$40.000/QALY'); ws.cell(r, 4, f'=D{r-2}/{pb["wtp"]}'); _fmt(ws.cell(r, 4), '0.0%'); r += 1
    ws.cell(r, 1, 'BML a R$40.000/QALY (R$)'); ws.cell(r, 4, f'={pb["wtp"]}*D5-D4'); _fmt(ws.cell(r, 4), '#,##0'); r += 1
    ws.cell(r, 1, 'BML a R$120.000/QALY, só ilustrativo (R$)'); ws.cell(r, 4, f'={pb["wtp_mod"]}*D5-D4'); _fmt(ws.cell(r, 4), '#,##0'); r += 2

    ws.cell(r, 1, 'Custos desagregados, descontados (equivalente à tabela 5)').font = BB; r += 1
    _hdr(ws, r, ['Categoria', 'Interfant-06', 'Blinatumomabe', 'Incremental']); r += 1
    r0 = r
    for lab, k in [('Aquisição do blinatumomabe', 'drug'), ('Suporte associado ao blinatumomabe', 'tox'), ('Quimioterapia e suporte', 'chemo'),
                   ('TCTH alogênico', 'hsct'), ('Episódios de resgate na recaída', 'salv'), ('Seguimento pós-recaída', 'pr'),
                   ('Seguimento dos livres de evento', 'fu')]:
        ws.cell(r, 1, lab); ws.cell(r, 2, c[k]); ws.cell(r, 3, i[k]); ws.cell(r, 4, f'=C{r}-B{r}')
        for j in (2, 3, 4): _fmt(ws.cell(r, j), '#,##0')
        r += 1
    ws.cell(r, 1, 'Total').font = BB
    for j, col in ((2, 'B'), (3, 'C'), (4, 'D')):
        ws.cell(r, j, f'=SUM({col}{r0}:{col}{r-1})'); _fmt(ws.cell(r, j), '#,##0')
    r += 1
    ws.cell(r, 1, 'Recaídas por paciente'); ws.cell(r, 2, c['n_rel']); ws.cell(r, 3, i['n_rel']); ws.cell(r, 4, f'=C{r}-B{r}')
    for j in (2, 3, 4): _fmt(ws.cell(r, j), '0.000')
    r += 1
    ws.cell(r, 1, 'O pathway e os custos unitários de quimioterapia são iguais nos dois braços; o custo acumulado é maior no braço do blinatumomabe porque mais pacientes seguem sem evento e recebem os blocos seguintes e a manutenção.').font = IT
    r += 2
    ws.cell(r, 1, 'Comparação com o manuscrito').font = BB; r += 1
    _hdr(ws, r, ['Resultado', 'Manuscrito', 'Reconstrução sem correções', 'Reconstrução corrigida']); r += 1
    so = R['base_orig']['s']
    for lab, ms, k, f in [('Custo incremental (R$)', 10566, 'd_cost', '#,##0'), ('QALY incremental', 5.374, 'd_qaly', '0.000'),
                          ('RCEI (R$/QALY)', 1966, 'icer', '#,##0'), ('BML a R$40.000 (R$)', 204405, 'nmb', '#,##0')]:
        ws.cell(r, 1, lab); ws.cell(r, 2, ms); ws.cell(r, 3, so[k]); ws.cell(r, 4, sb[k])
        for j in (2, 3, 4): _fmt(ws.cell(r, j), f)
        r += 1
    ws.cell(r, 1, 'A diferença entre as duas reconstruções vem só da correção do TCTH pelo IPCA (R$94.254 de 2021 para R$109.357 de 2024).').font = IT

    # ------------ Cenários
    ws = wb.create_sheet('Cenarios'); _title(ws, 'Análise de cenários (corrigida)', 'Equivalente à tabela 4. "NOVO" = cenário acrescentado nesta revisão.')
    _hdr(ws, 3, ['Grupo', 'Cenário', 'Frascos', 'Custo incremental (R$)', 'QALY incremental', 'RCEI (R$/QALY)', '% de R$40.000', 'BML a R$40.000 (R$)'],
         [22, 58, 9, 16, 12, 14, 12, 16])
    r = 4
    for s in R['scen_corr']:
        vals = [s['group'], s['name'], s['vials'], s['d_cost'], s['d_qaly'], s['icer'], s['pct_ref'], s['nmb']]
        for j, (v, f) in enumerate(zip(vals, [None, None, '0.00', '#,##0', '0.000', '#,##0', '0.0%', '#,##0']), 1):
            cc = ws.cell(r, j, v)
            if f: _fmt(cc, f)
        if s['name'] in APPROX: ws.cell(r, 2).fill = YEL
        r += 1
    ws.cell(r + 1, 1, 'Amarelo: cenário reconstruído de forma aproximada (ver Validacao).').font = IT

    # ------------ Sensibilidade univariada
    ws = wb.create_sheet('Sensibilidade_BML'); _title(ws, 'Sensibilidade univariada na escala de BML (R$40.000/QALY)',
                                                       'Ordenado pela amplitude; o BML positivo indica custo-efetividade.')
    _hdr(ws, 3, ['Parâmetro', 'Valor baixo', 'Valor alto', 'BML no valor baixo (R$)', 'BML no valor alto (R$)', 'BML caso-base (R$)', 'Amplitude (R$)'],
         [44, 13, 13, 18, 18, 16, 14])
    r = 4
    for d in R['owsa']:
        vals = [d['label'], d['low'], d['high'], d['nmb_low'], d['nmb_high'], d['base'], f'=ABS(E{r}-D{r})']
        for j, v in enumerate(vals, 1):
            cc = ws.cell(r, j, v)
            if j in (2, 3): _fmt(cc, '#,##0.000' if abs(v) < 20 else '#,##0')
            if j >= 4: _fmt(cc, '#,##0')
        r += 1

    # ------------ PSA
    ws = wb.create_sheet('PSA'); _title(ws, f'Análise probabilística ({len(R["psa"][0.8]["res"]):,} simulações)'.replace(',', '.'),
                                        'ρ = correlação entre os sorteios de DFS e OS no mesmo braço (cópula gaussiana). Caso-base: ρ = 0,8.')
    _hdr(ws, 3, ['Métrica', 'ρ = 0,8 (caso-base)', 'ρ = 0', 'ρ = 0,5', 'ρ = 0,95', 'Manuscrito (método anterior)'], [42, 18, 14, 14, 14, 20])
    ms = {'d_cost': (13787, -18338, 45320), 'd_qaly': (5.284, 3.442, 6.854), 'nmb_40000': (197564, 100157, 279027),
          'p_ce_40000': 0.999, 'p_qaly_neg': 0.0}
    metr = [('Custo incremental médio (R$)', 'd_cost', 0, '#,##0'), ('   IC95% inferior', 'd_cost', 1, '#,##0'), ('   IC95% superior', 'd_cost', 2, '#,##0'),
            ('QALY incremental médio', 'd_qaly', 0, '0.000'), ('   IC95% inferior', 'd_qaly', 1, '0.000'), ('   IC95% superior', 'd_qaly', 2, '0.000'),
            ('BML médio a R$40.000/QALY (R$)', 'nmb_40000', 0, '#,##0'), ('   IC95% inferior', 'nmb_40000', 1, '#,##0'), ('   IC95% superior', 'nmb_40000', 2, '#,##0'),
            ('P(custo-efetivo a R$40.000/QALY)', 'p_ce_40000', None, '0.00%'), ('P(custo-efetivo a R$120.000/QALY, ilustrativo)', 'p_ce_120000', None, '0.00%'),
            ('P(reduz custo)', 'p_cost_saving', None, '0.0%'), ('P(QALY incremental < 0)', 'p_qaly_neg', None, '0.00%')]
    r = 4
    for lab, k, ix, f in metr:
        ws.cell(r, 1, lab)
        for j, rho in enumerate((0.8, 0.0, 0.5, 0.95), 2):
            v = R['psa'][rho]['sum'][k]; ws.cell(r, j, v[ix] if ix is not None else v); _fmt(ws.cell(r, j), f)
        m = ms.get(k)
        if m is not None:
            ws.cell(r, 6, m[ix] if (ix is not None and isinstance(m, tuple)) else m); _fmt(ws.cell(r, 6), f)
        r += 1
    r += 1
    ws.cell(r, 1, 'Distribuições').font = BB; r += 1
    for t in ['Curvas: normal multivariada (Cholesky) em logit(fração curada) e log(−a); variância da informação observada de dados pseudoindividuais calibrados ao IC95% publicado de S(4).',
              'OS do blinatumomabe (2 óbitos): variância da fração curada tirada diretamente do IC95% publicado (75,9–98,3%).',
              'Utilidades: beta (65,35), (76,24), (67,33), decremento (94,6). TCTH: beta (64,2; 149,8) e (10; 20). Fração de recaída: beta com n de eventos. IVIg e G-CSF: beta (19,11) e (5,25).',
              'Gama com DP relativo pressuposto: SMR e sobrevida pós-recaída 25%; frasco 10%; IVIg, TCTH e resgate 20%.']:
        ws.cell(r, 1, t).font = B; r += 1

    # ------------ CEAC
    ws = wb.create_sheet('CEAC'); _title(ws, 'Curva de aceitabilidade de custo-efetividade')
    _hdr(ws, 3, ['Disposição a pagar (R$/QALY)', 'ρ = 0,8 (caso-base)', 'ρ = 0', 'ρ = 0,5', 'ρ = 0,95'], [28, 18, 12, 12, 12])
    grid = list(range(0, 20001, 1000)) + list(range(25000, 150001, 5000))
    cols = {rho: psa.ceac(R['psa'][rho]['res'], grid) for rho in (0.8, 0.0, 0.5, 0.95)}
    for k, w in enumerate(grid):
        ws.cell(4 + k, 1, w); _fmt(ws.cell(4 + k, 1), '#,##0')
        for j, rho in enumerate((0.8, 0.0, 0.5, 0.95), 2):
            ws.cell(4 + k, j, cols[rho][k]); _fmt(ws.cell(4 + k, j), '0.0%')

    # ------------ Coorte incidente
    ws = wb.create_sheet('Coorte_incidente'); _title(ws, 'Estimativa exploratória da coorte incidente',
                                                     'Não é análise de impacto orçamentário: não considera difusão, market share nem horizonte de 5 anos.')
    _hdr(ws, 3, ['Item', 'Valor', 'Cálculo'], [52, 18, 60])
    co = R['cohort']
    rows = [('Lactentes elegíveis por ano', co['infants'], 'Painel de Oncologia/DATASUS ', '0'),
            ('Custo do fármaco por paciente (R$)', co['drug_per_patient'], 'preço do frasco × frascos por curso', '#,##0'),
            ('Gasto bruto anual com o fármaco (R$)', '=B4*B5', 'lactentes × custo do fármaco', '#,##0'),
            ('Custo incremental por paciente, vida toda, descontado (R$)', sb['d_cost'], 'caso-base corrigido', '#,##0'),
            ('Custo incremental de cada coorte anual, vida toda (R$)', '=B4*B7', 'lactentes × custo incremental', '#,##0')]
    for k, (a, v, cmt, f) in enumerate(rows, 4):
        ws.cell(k, 1, a); ws.cell(k, 2, v); ws.cell(k, 3, cmt); _fmt(ws.cell(k, 2), f)

    # ------------ Validação
    ws = wb.create_sheet('Validacao'); _title(ws, 'Validação: reconstrução sem correções vs tabela 4 do manuscrito')
    _hdr(ws, 3, ['Cenário', 'Manuscrito Δ custo', 'Reconstrução Δ custo', 'Manuscrito Δ QALY', 'Reconstrução Δ QALY',
                 'Manuscrito RCEI', 'Reconstrução RCEI', 'Diferença RCEI'], [52, 14, 14, 13, 13, 13, 13, 12])
    r = 4
    for s in R['scen_orig']:
        if s['name'] not in MS: continue
        m = MS[s['name']]
        vals = [s['name'], m[0], s['d_cost'], m[1], s['d_qaly'], m[2], s['icer'], f'=G{r}/F{r}-1']
        for j, (v, f) in enumerate(zip(vals, [None, '#,##0', '#,##0', '0.000', '0.000', '#,##0', '#,##0', '0.0%']), 1):
            cc = ws.cell(r, j, v)
            if f: _fmt(cc, f)
        if s['name'] in APPROX: ws.cell(r, 1).fill = YEL
        r += 1
    ws.cell(r + 1, 1, 'Amarelo: forma das curvas de 3 parâmetros dentro do período observado (ou definição do cenário) não documentada; reprodução aproximada.').font = IT

    for wsx in wb:
        for row in wsx.iter_rows():
            for cc in row:
                if cc.value is not None and (cc.font is None or cc.font.name != F):
                    cc.font = Font(name=F, bold=cc.font.b, italic=cc.font.i, size=cc.font.sz, color=cc.font.color)
    wb.save(path)


# ---------------- figuras
INK = '#0b0b0b'; INK2 = '#52514e'; GRID = '#e4e3df'; BLUE = '#2a78d6'; ORANGE = '#eb6834'


def _style(ax):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(color=GRID, linewidth=0.6); ax.set_axisbelow(True)


def figures(R, out):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8})
    brl = FuncFormatter(lambda x, _: f'{x/1000:,.0f}'.replace(',', '.'))

    # Figura 3: tornado em BML
    d = R['owsa'][:12][::-1]
    base = d[0]['base']
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
    for k, row in enumerate(d):
        lo, hi = row['nmb_low'], row['nmb_high']
        ax.barh(k, lo - base, left=base, height=0.62, color=BLUE, edgecolor='white', linewidth=1)
        ax.barh(k, hi - base, left=base, height=0.62, color=ORANGE, edgecolor='white', linewidth=1)
        fl = lambda v: (f'{v:.0f}' if float(v).is_integer() else f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')) if abs(v) < 20 else f'{v:,.0f}'.replace(',', '.')
        ax.text(min(lo, hi) - 6000, k, fl(row['low'] if lo < hi else row['high']), va='center', ha='right', fontsize=6.5, color=INK2)
        ax.text(max(lo, hi) + 6000, k, fl(row['high'] if lo < hi else row['low']), va='center', ha='left', fontsize=6.5, color=INK2)
    ax.set_yticks(range(len(d))); ax.set_yticklabels([x['label'] for x in d], fontsize=7.5, color=INK)
    ax.axvline(base, color=INK, linewidth=0.8)
    ax.axvline(0, color='#c0392b', linewidth=1.2)
    ax.text(0, len(d) - 0.3, ' BML = 0', color='#c0392b', fontsize=6.5, va='bottom')
    ax.xaxis.set_major_formatter(brl); ax.set_xlabel('Benefício monetário líquido incremental a R\\$40.000/QALY (R\\$ mil)', color=INK2, fontsize=8)
    lo_all = min(min(x['nmb_low'], x['nmb_high']) for x in d); hi_all = max(max(x['nmb_low'], x['nmb_high']) for x in d)
    ax.set_xlim(min(-20000, lo_all - 60000), hi_all + 60000)
    _style(ax); ax.grid(axis='y', visible=False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label='Valor baixo do parâmetro'), Patch(color=ORANGE, label='Valor alto do parâmetro')],
              loc='lower right', fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(out, 'Figura3_tornado_BML.png')); plt.close(fig)

    # Figura 4: plano CE (A) e CEAC (B)
    res = R['psa'][0.8]['res']; dc = res[:, 1] - res[:, 0]; dq = res[:, 3] - res[:, 2]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.4), dpi=300)
    a1.scatter(dq, dc, s=3, color=BLUE, alpha=0.35, linewidths=0)
    xs = np.array([0, max(7.5, dq.max() * 1.05)])
    a1.plot(xs, 40000 * xs, color=INK, linewidth=1.2, label='R\\$40.000/QALY')
    a1.plot(xs, 120000 * xs, color=INK2, linewidth=1.0, linestyle=(0, (4, 3)), label='R\\$120.000/QALY (ilustrativo)')
    a1.axhline(0, color=INK2, linewidth=0.6); a1.axvline(0, color=INK2, linewidth=0.6)
    a1.set_xlim(0, xs[1]); lim = max(abs(dc).max() * 1.15, 60000); a1.set_ylim(-lim, lim)
    a1.yaxis.set_major_formatter(brl)
    a1.set_xlabel('QALY incremental', color=INK2); a1.set_ylabel('Custo incremental (R\\$ mil)', color=INK2)
    a1.legend(fontsize=6.5, frameon=False, loc='upper right'); _style(a1)
    a1.set_title('A', loc='left', fontweight='bold', fontsize=9)
    grid = np.linspace(0, 150000, 151)
    for rho, col, ls, lab in [(0.8, BLUE, '-', 'ρ = 0,8 (caso-base)'), (0.0, ORANGE, (0, (4, 3)), 'ρ = 0')]:
        a2.plot(grid, psa.ceac(R['psa'][rho]['res'], grid), color=col, linewidth=2 if rho == 0.8 else 1.4, linestyle=ls, label=lab)
    a2.axvline(40000, color=INK2, linewidth=0.8, linestyle=':')
    a2.text(41500, 0.08, 'R\\$40.000', fontsize=6.5, color=INK2)
    a2.set_ylim(0, 1.02); a2.xaxis.set_major_formatter(brl)
    a2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0%}'))
    a2.set_xlabel('Disposição a pagar (R\\$ mil por QALY)', color=INK2); a2.set_ylabel('Probabilidade de ser custo-efetivo', color=INK2)
    a2.legend(fontsize=6.5, frameon=False, loc='lower right'); _style(a2)
    a2.set_title('B', loc='left', fontweight='bold', fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(out, 'Figura4_PSA.png')); plt.close(fig)
