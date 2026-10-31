# Modelo de sobrevida particionada: blinatumomabe em primeira linha na LLA KMT2A-r do lactente (SUS)

Versão de submissão (25/10/2026). Caso-base: RCEI de R$6.998/QALY, BML de R$175.098 a R$40.000/QALY, P(custo-efetivo) de 99,8%.

## Como reproduzir

```
pip install -r requirements.txt
python test_model.py     # testes de consistência (5 testes)
python run_all.py        # caso-base, cenários, sensibilidade e PSA com 5.000 simulações (~40 s); grava resultados/
python mk_final.py       # grava resultados/final_numbers.json (números usados no manuscrito e no material suplementar)
python figs_en.py        # Figuras 2 e 3 e Fig. S2
python figS1.py          # Fig. S1
python figure1.py        # Fig. 1 (recriada; grava 05_manuscrito/Figure1_model_fit_reproduzida.png)
python excel/build_excel.py   # gera a planilha com fórmulas vivas
```

As sementes aleatórias são fixas: rodar de novo produz exatamente o mesmo `final_numbers.json` (testado em 25/10/2026, nenhuma diferença).

A conferência da planilha contra o Python (`python excel/validate.py`) recalcula cada um dos 47 cenários no LibreOffice (precisa do `soffice` no PATH; leva cerca de 15 minutos). O resultado da última conferência está em `excel/validacao/` (diferença máxima no RCEI < 1e-13; nenhuma célula com erro).

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `inputs.py` | Registro de todos os parâmetros (valor, unidade, fonte, ano-base, status). `base(corrected=True)` monta o caso-base; `corrected=False` reproduz a versão anterior do manuscrito |
| `model.py` | Motor do modelo: 3 estados, ciclos de 4 semanas, meio ciclo, cura após 7 anos com SMR, via pós-recaída (`relapse_pathway_B`, `eol_until`) |
| `analyses.py` | Caso-base, 47 cenários, sensibilidade univariada na escala de BML, coorte incidente exploratória |
| `psa.py` | PSA: normal multivariada nos parâmetros Gompertz, cópula gaussiana DFS-OS, distribuições dos demais parâmetros |
| `run_all.py`, `report.py` | Executam tudo e gravam `resultados/Resultados_modelo_Interfant.xlsx` e as simulações `psa_rho*.npy` |
| `mk_final.py` | Consolida os números do manuscrito em `resultados/final_numbers.json` |
| `curves.json`, `curve_unc.json` | Parâmetros das 7 famílias nas 4 curvas e matrizes de variância das Gompertz (ajuste por máxima verossimilhança intervalar) |
| `dados_fonte/qx_ibge_2024.json`, `qx.json` | Tábua completa de mortalidade IBGE 2024 (caso-base) e tábua da versão anterior |
| `R/` | Ajuste das curvas em R (flexsurv/flexsurvcure) a partir dos números em risco de Vieira Martins 2026; ver `R/LEIA-ME.md` |
| `excel/` | Planilha validada, script que a gera e conferência cenário a cenário |
| `test_model.py` | Testes: reprodução da versão anterior, correção pelo IPCA, consistência dos estados, frascos, relato do limiar |
| `derivacao_curvas/mle.py` | Ajuste por máxima verossimilhança intervalar das 7 famílias nas 4 curvas, a partir das tabelas de números em risco; gera `mle.json`, que coincide com `curves.json` |
| `derivacao_curvas/curve_unc.py`, `psm.py` | Derivação de `curve_unc.json` (médias e matrizes de variância das Gompertz para o PSA): dados pseudoindividuais anuais com censura calibrada para reproduzir o IC95% publicado de S(4). `psm.py` é a reconstrução inicial do modelo original, usada só por este script |
| `figure1.py` | Recria a Fig. 1. O script original da figura submetida não foi preservado; esta versão tem o mesmo conteúdo, com rótulos dos painéis em minúsculas |
