# Survival-curve fit in R

`ajuste_curvas.R` refits the four survival curves (DFS and OS, Interfant-06 historical controls n = 214, and Interfant-06 + blinatumomab n = 30) from the numbers at risk published by Vieira Martins et al. 2026.

## Method (`MODO <- "tabela"`, used in the paper)

1. Reads, for each curve, the number at risk and the cumulative number censored at each year (`dados/reais/*_tabela.csv`; columns `tempo_anos`, `n_risco`, `censurados_acumulados`).
2. Recovers events and censorings in each annual interval: events = at risk at start − at risk at end − censored in the interval.
3. Fits 7 families by maximum likelihood with interval censoring: exponential, Weibull, log-normal, log-logistic, Gompertz, generalised gamma (`flexsurv`) and Weibull mixture cure (`flexsurvcure`).
4. Reports AIC, BIC, S(t) at 1 to 7 years, a comparison with the published survival values, and the parameters in the same format as the `Curvas` sheet of the spreadsheet.

An alternative mode (`MODO <- "km"`) reconstructs individual data from digitised Kaplan–Meier curves with the Guyot algorithm (`IPDfromKM`). It was not used in the paper, and no digitised curves are included.

## Running

R 4.1 or later (the paper used R 4.4.1). The script installs missing packages. With the `R/` folder as working directory:

```
Rscript ajuste_curvas.R
```

Results go to `saida/`. `dados/exemplo_teste/` contains simulated data to check that the script runs (`PASTA_DADOS <- "dados/exemplo_teste"`).

## Expected behaviour

For OS in the blinatumomab arm there are very few deaths, so some families converge to extreme values or fail. The script records the failure and continues. The AIC values of the other fits match the Python fit in `derivacao_curvas/mle.py`.

Labels and comments in the script are in Portuguese (see `GLOSSARY.md` at the top level).
