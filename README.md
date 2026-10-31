# Blinatumomab added to Interfant-06 for infants with KMT2A-rearranged ALL: cost-effectiveness model (Brazil, SUS perspective)

Model code and data for the manuscript:

> Monte GG, Rechenmacher C, Pinto LZ, Lopes VP, Pinhatti A, Daudt LE, Michalowski MB. *Cost-Effectiveness of Adding Blinatumomab to First-Line Chemotherapy for Infants with KMT2A-Rearranged Acute Lymphoblastic Leukaemia in Brazil: A Partitioned Survival Analysis.* Submitted to PharmacoEconomics – Open (PECO-D-26-00122).

The model is written in Python. A spreadsheet version with live formulas reproduces the deterministic results, and an R script refits the survival curves with `flexsurv`. All inputs come from published sources or public Brazilian price tables (SIGTAP, CMED, Banco de Preços em Saúde, IBGE).

## Model in brief

| Item | Choice |
|---|---|
| Structure | Three-state partitioned survival model (event-free, post-relapse, dead). Event-free = DFS; post-relapse = OS − DFS |
| Cycle and horizon | 4-week cycles; lifetime (100 years; 1,300 cycles); half-cycle correction |
| Population | Infants with KMT2A-rearranged ALL; model entry at 0.42 years of age |
| Comparators | Interfant-06 chemotherapy vs Interfant-06 + blinatumomab |
| Survival | Gompertz curves fitted by interval-censored maximum likelihood to the published numbers at risk (Vieira Martins et al. 2026); 7 parametric families compared |
| Extrapolation | Event-free patients considered cured at 7 years, with IBGE 2024 life-table mortality × SMR 8. Post-relapse median survival 1.5 years |
| Post-relapse pathway | Curative-intent salvage and HSCT proportions from Interfant-99 (Driessen et al. 2016); marrow assessments, end-of-life care and outpatient follow-up costed from SIGTAP |
| Discounting | 5% per year for costs and outcomes |
| Threshold | R$40,000 per QALY |
| PSA | 5,000 simulations; multivariate normal on the Gompertz parameters; Gaussian copula between DFS and OS (ρ = 0.8, range 0 to 0.95); seed 2026 |

Base case: incremental cost R$37,132, incremental QALYs 5.306, ICER R$6,998 per QALY, probability cost-effective 99.8%.

## How to run

Requires Python 3.11 (tested on 3.11.15).

```
cd model
pip install -r requirements.txt
python test_model.py          # consistency tests
python run_all.py             # base case, 47 scenarios, one-way analysis and PSA (about 40 s)
python mk_final.py            # writes resultados/final_numbers.json (all numbers reported in the paper)
python figure1.py             # Fig. 1 (survival fits)
python figs_en.py             # Figs. 2 and 3 and Fig. S2
python figS1.py               # Fig. S1
python excel/build_excel.py   # rebuilds the spreadsheet with live formulas
```

Random seeds are fixed, so a re-run gives an identical `final_numbers.json`.

`python excel/validate.py` recalculates each of the 47 scenarios in the spreadsheet through LibreOffice (`soffice` must be on the PATH; about 15 minutes) and compares them with Python. The last check is in `model/excel/validacao/`: maximum difference in the ICER below 1e-13 and no cell errors.

The survival-curve fit in R is described in `model/R/README.md`.

## Contents

| Path | Content |
|---|---|
| `model/inputs.py` | Every parameter with value, unit, source, price year and status. `base()` builds the base case |
| `model/model.py` | Model engine: state occupancy, cure point, post-relapse pathway, vial counts, costs and QALYs |
| `model/analyses.py` | Base case, 47 scenarios, one-way sensitivity analysis on the net monetary benefit scale, exploratory incident cohort |
| `model/psa.py` | Probabilistic sensitivity analysis |
| `model/run_all.py`, `report.py`, `mk_final.py` | Run everything and write the results workbook and `final_numbers.json` |
| `model/curves.json`, `curve_unc.json` | Parameters of the 7 families for the 4 curves; means and variance–covariance matrices of the Gompertz parameters used in the PSA |
| `model/derivacao_curvas/` | Scripts that derive `curves.json` (`mle.py`) and `curve_unc.json` (`curve_unc.py`, which uses `psm.py`) from the numbers-at-risk tables |
| `model/dados_fonte/qx_ibge_2024.json` | IBGE 2024 complete life table, both sexes |
| `model/excel/` | Spreadsheet version, the script that builds it, and the cell-by-cell validation against Python |
| `model/R/` | Survival-curve fit in R (`flexsurv`, `flexsurvcure`) |
| `model/resultados/` | Results produced by the scripts |
| `data_sources/` | Public source documents: SIGTAP procedure records, CMED price list, Banco de Preços em Saúde extracts, CONITEC report 725/2022, numbers-at-risk tables from Vieira Martins et al. 2026, IBGE life table |

## Language

Code comments, parameter descriptions, scenario names and spreadsheet labels are in Portuguese. `GLOSSARY.md` translates the terms needed to read the code and the spreadsheet.

## Notes on methods for reviewers

- The variance–covariance matrices for the PSA (`curve_unc.json`) were obtained from annual pseudo-individual data generated from the fitted curves, with censoring calibrated so that the published 95% CI of 4-year survival is reproduced. For OS in the blinatumomab arm (two deaths), the variance of the cure fraction was taken directly from the published 95% CI.
- In the blinatumomab OS curve the likelihood is flat, because there are very few events. Different optimiser starting points give different Gompertz (a, b) pairs with the same plateau (0.933) and the same AIC.
- `inputs.py` flags with status `premissa` the values that are assumed or calibrated rather than taken from a specific source. Each of them is varied in the scenario or one-way analyses.
- `base(corrected=False)` and the `Validacao` sheet reproduce an earlier internal version of the analysis. They are kept for traceability and are not part of the reported results.

## Licence

Code: MIT licence (see `LICENSE`). The documents in `data_sources/` are public documents of the Brazilian government and of CONITEC, reproduced for convenience. The numbers-at-risk tables were transcribed from Vieira Martins et al. 2026; please cite the original publication.

## Citation

See `CITATION.cff`. Please cite the article once published.

## Contact

Gutemberg Guedes Monte, Hospital de Clínicas de Porto Alegre, Brazil (corresponding author).
