"""Confere a planilha contra o Python, cenário a cenário.
Para cada cenário, grava o número em Inputs!C4, recalcula no LibreOffice (conversão headless, que recalcula as
fórmulas) e compara Δ custo, Δ QALY e RCEI da aba Resultados com as colunas do script Python na aba Cenarios.
Requer LibreOffice (soffice no PATH). Uso: python excel/validate.py"""
import openpyxl, subprocess, json, os, shutil, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'Modelo_PSM_Blinatumomabe_Lactentes.xlsx')
SP = os.path.join(HERE, 'validacao'); os.makedirs(SP, exist_ok=True)
n = openpyxl.load_workbook(SRC)['Cenarios'].max_row - 4
res = []; tmp = tempfile.mkdtemp()
for k in range(1, n + 1):
    f = os.path.join(tmp, f'c{k}.xlsx'); wb = openpyxl.load_workbook(SRC); wb['Inputs']['C4'] = k; wb.save(f)
    out = os.path.join(tmp, 'out'); shutil.rmtree(out, ignore_errors=True)
    subprocess.run(['soffice', '--headless', '--calc', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', out, f],
                   capture_output=True, timeout=300)
    w = openpyxl.load_workbook(os.path.join(out, f'c{k}.xlsx'), data_only=True)
    ERR = {'#DIV/0!', '#N/A', '#VALUE!', '#REF!', '#NAME?', '#NUM!', '#NULL!'}
    err = sum(1 for ws in w.worksheets for row in ws.iter_rows(values_only=True) for v in row if isinstance(v, str) and v in ERR)
    R = w['Resultados']; C = w['Cenarios']
    row = dict(k=k, name=C.cell(4 + k, 3).value, xc=R['D12'].value, pc=C.cell(4 + k, 29).value, xq=R['D13'].value,
               pq=C.cell(4 + k, 30).value, xi=R['D19'].value, pi=C.cell(4 + k, 31).value, err=err)
    res.append(row)
    d = row['xi'] / row['pi'] - 1 if isinstance(row['xi'], (int, float)) else float('nan')
    print(k, str(row['name'])[:45], round(row['xi']) if isinstance(row['xi'], (int, float)) else row['xi'], round(row['pi']), f'{d:+.2e}', err, flush=True)
json.dump(res, open(os.path.join(SP, 'val.json'), 'w'))
print('máx |dif| RCEI:', max(abs(r['xi'] / r['pi'] - 1) for r in res), '| células com erro:', sum(r['err'] for r in res))
