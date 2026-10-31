# Glossary (Portuguese → English)

## Folders and files

| Portuguese | English |
|---|---|
| `resultados/` | results |
| `derivacao_curvas/` | curve derivation |
| `dados_fonte/` | source data |
| `excel/validacao/` | spreadsheet validation |
| `ajuste_curvas.R` | curve fitting |
| `dados/reais/`, `dados/exemplo_teste/` | real data, test example |

## Spreadsheet sheets

| Sheet | Content |
|---|---|
| Leia-me | Read me: how to use the spreadsheet |
| Inputs | All parameters, with source, price year, IPCA factor and status. Cell C4 selects the scenario |
| Resultados | Results: costs, QALYs, life-years, ICER, net monetary benefit, cost breakdown |
| Custo_Pos_Recaida | Post-relapse follow-up cost (SIGTAP procedures) |
| Via_Pos_Recaida | Post-relapse pathway: curative intent, salvage cycles, HSCT, marrow assessments, end-of-life care |
| Cenarios | Scenarios (one row per scenario; number used in Inputs!C4) |
| Frascos | Vials: number of vials per cycle by preparation schedule and body surface area |
| Curvas | Survival curves: parameters of the 7 families for the 4 curves |
| Tabua_IBGE | IBGE 2024 life table |
| Modelo_Interfant, Modelo_Blina | Cycle-by-cycle traces for Interfant-06 and Interfant-06 + blinatumomab |
| Sensibilidade_BML | One-way sensitivity analysis on the net monetary benefit scale (imported from Python) |
| PSA | Probabilistic results (imported from Python) |
| Coorte_incidente | Exploratory annual incident cohort (not a budget impact analysis) |
| Validacao | Validation: spreadsheet vs Python in every scenario |

Cell colours: blue = editable input; black = formula; green = main result; yellow = assumption (`premissa`).

## Terms used in code and labels

| Portuguese | English |
|---|---|
| caso-base | base case |
| cenário | scenario |
| sobrevida livre de doença (DFS) / global (OS) | disease-free / overall survival |
| livre de evento; pós-recaída; morte | event-free; post-relapse; death |
| recaída; resgate | relapse; salvage treatment |
| intenção curativa | curative intent |
| TCTH | haematopoietic stem cell transplantation (HSCT) |
| reavaliação medular / mielograma | bone marrow assessment |
| fim de vida | end-of-life care |
| diária hospitalar; UTI | hospital day; intensive care unit |
| acompanhamento ambulatorial; consulta | outpatient follow-up; visit |
| frasco; bolsa; cassete | vial; infusion bag; cassette |
| esquema de preparo | bag preparation schedule |
| ASC | body surface area (BSA) |
| fase intensiva; manutenção | intensive phase; maintenance |
| custos de toxicidade (IVIg, G-CSF) | toxicity costs |
| taxa de desconto | discount rate |
| horizonte | time horizon |
| ciclo | cycle (4 weeks) |
| cura; ponto de cura | cure; cure time point |
| fração curada | cure fraction |
| SMR (excesso de mortalidade) | standardised mortality ratio |
| utilidade; norma populacional; decremento de sobrevivente | utility; population norm; survivor utility decrement |
| anos de vida | life-years |
| RCEI | ICER |
| BML (benefício monetário líquido) | net monetary benefit (NMB) |
| limiar | willingness-to-pay threshold |
| custo-efetivo | cost-effective |
| PMVG | maximum government sale price (CMED list) |
| PMC | maximum consumer price (CMED list) |
| ICMS | state value-added tax |
| compra pública (BPS) | public procurement price (Banco de Preços em Saúde) |
| microcusteio | micro-costing |
| IPCA | Brazilian consumer price index (used to inflate costs to 2024) |
| SIGTAP | SUS procedure and price table |
| pior caso combinado | combined worst case |
| premissa | assumption (value assumed or calibrated, varied in sensitivity analysis) |
| fonte; ano-base; status; observação | source; price year; status; note |

## Scenario groups (`analyses.py`)

| Portuguese | English |
|---|---|
| Preço e dose | Price and dose |
| Prática da farmácia | Pharmacy practice (vial use under different bag schedules) |
| Extrapolação | Extrapolation |
| Mortalidade e utilidade | Mortality and utility |
| Custos | Costs |
| Desconto e horizonte | Discounting and horizon |
| Pós-recaída | Post-relapse |
| Combinado | Combined |
