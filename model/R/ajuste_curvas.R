# =============================================================================
# Ajuste das curvas de sobrevida: blinatumomabe + Interfant-06 em lactentes
# com LLA KMT2A-rearranjada
#
# Dois modos de reconstrução dos dados:
#   "tabela": método descrito no manuscrito. Eventos e censuras de cada intervalo
#             anual são recuperados dos números em risco e das censuras acumuladas
#             publicados; o ajuste usa máxima verossimilhança com censura intervalar.
#   "km":     alternativa por digitalização das curvas de Kaplan-Meier e algoritmo
#             de Guyot (pacote IPDfromKM), com tempos de evento individuais.
#
# Depois: ajuste de 7 famílias (flexsurv e flexsurvcure), AIC/BIC, S(t) em 1 a 7
# anos, conferência com os valores publicados e parâmetros no mesmo formato da
# aba "Curvas" da planilha.
#
# Uso: abrir no RStudio com a pasta R/ como diretório de trabalho e rodar tudo
# (Ctrl+Shift+Enter), ou no terminal: Rscript ajuste_curvas.R
# =============================================================================

# ---------------------------------------------------------------- CONFIGURAÇÃO
MODO        <- "tabela"                # "tabela" (método do manuscrito) ou "km"
PASTA_DADOS <- "dados/reais"   # tabelas de Vieira Martins 2026 (Fig. 1B-D); "dados/exemplo_teste" para o teste
PASTA_SAIDA <- file.path("saida", paste0(basename(PASTA_DADOS), "_", MODO))

CURVAS <- data.frame(
  id        = c("dfs_c", "os_c", "dfs_i", "os_i"),
  rotulo    = c("DFS Interfant-06", "OS Interfant-06",
                "DFS Interfant-06 + blinatumomabe", "OS Interfant-06 + blinatumomabe"),
  n_total   = c(214, 214, 30, 30),          # controles históricos e estudo de fase 2
  s4_public = c(0.440, 0.602, 0.833, 0.933), # valores publicados aos 4 anos (Vieira Martins 2026)
  eventos   = c(NA, NA, NA, NA),             # modo "km": total de eventos, se publicado
  stringsAsFactors = FALSE
)
CENSURA_NO_INTERVALO <- 0.5  # modo "tabela": censuras de cada intervalo ficam no meio dele (0 = início, 1 = fim)
T_OBS     <- 7    # fim do período observado no modelo (anos)
T_GRAFICO <- 30   # horizonte dos gráficos de extrapolação (anos)

# ---------------------------------------------------------------- PACOTES
pacotes <- c("flexsurv", "flexsurvcure", "survival", "ggplot2", "scales", "jsonlite")
if (MODO == "km") pacotes <- c("IPDfromKM", pacotes)
faltando <- pacotes[!vapply(pacotes, requireNamespace, logical(1), quietly = TRUE)]
if (length(faltando) > 0) install.packages(faltando)
suppressPackageStartupMessages({
  library(flexsurv); library(flexsurvcure); library(survival); library(ggplot2)
  if (MODO == "km") library(IPDfromKM)
})
dir.create(PASTA_SAIDA, recursive = TRUE, showWarnings = FALSE)
set.seed(2026)

# ---------------------------------------------------------------- FAMÍLIAS
# Mesma ordem e mesma parametrização da aba "Curvas" da planilha:
#   1 Gompertz      p1 = a (shape), p2 = b (rate)          S = exp(-(b/a)(e^{at} - 1))
#   2 Weibull       p1 = lambda (scale), p2 = k (shape)    S = exp(-(t/lambda)^k)
#   3 Log-normal    p1 = mu (meanlog), p2 = sigma (sdlog)
#   4 Log-logística p1 = alfa (scale), p2 = beta (shape)   S = 1/(1+(t/alfa)^beta)
#   5 Exponencial   p1 = lambda (rate)
#   6 Mixture cure  p1 = pi (curados), p2 = lambda (scale), p3 = k (shape), Weibull
#   7 Gama generalizada (Prentice) p1 = mu, p2 = sigma, p3 = Q
FAMILIAS <- data.frame(
  n      = 1:7,
  nome   = c("gompertz", "weibull", "lognormal", "loglogistic", "exponential",
             "mixture_cure_weibull", "gengamma"),
  rotulo = c("Gompertz", "Weibull", "Log-normal", "Log-logística", "Exponencial",
             "Mixture cure (Weibull)", "Gama generalizada"),
  dist   = c("gompertz", "weibull", "lnorm", "llogis", "exp", "weibull", "gengamma"),
  stringsAsFactors = FALSE
)
PARAMS <- list(gompertz = c("shape", "rate"), weibull = c("scale", "shape"),
               lognormal = c("meanlog", "sdlog"), loglogistic = c("scale", "shape"),
               exponential = c("rate"), mixture_cure_weibull = c("theta", "scale", "shape"),
               gengamma = c("mu", "sigma", "Q"))
np_fam <- function(fm) length(PARAMS[[fm]])

# Sobrevida com os parâmetros no formato da planilha
surv_planilha <- function(familia, p, t) {
  t <- pmax(t, 1e-10)
  switch(familia,
    gompertz    = exp(-(p[2] / p[1]) * (exp(p[1] * t) - 1)),
    weibull     = exp(-((t / p[1])^p[2])),
    lognormal   = 1 - pnorm((log(t) - p[1]) / p[2]),
    loglogistic = 1 / (1 + (t / p[1])^p[2]),
    exponential = exp(-p[1] * t),
    mixture_cure_weibull = p[1] + (1 - p[1]) * exp(-((t / p[2])^p[3])),
    gengamma    = flexsurv::pgengamma(t, mu = p[1], sigma = p[2], Q = p[3], lower.tail = FALSE))
}
tem_params <- function(fm, p) !anyNA(p[seq_len(np_fam(fm))])

# Lê CSV com vírgula ou com ponto e vírgula (Excel em português salva com ";" e decimal com vírgula)
ler_csv <- function(arq) {
  if (!file.exists(arq)) stop("Arquivo não encontrado: ", arq, ". Confira se o diretório de trabalho é a pasta R/.")
  l1 <- readLines(arq, n = 1, warn = FALSE)
  if (grepl(";", l1)) read.csv2(arq) else read.csv(arq)
}

# ---------------------------------------------------------------- 1. RECONSTRUÇÃO
# Ambos os modos devolvem: dados (L, R; R = NA para censura à direita, L = R para
# evento com tempo exato, L < R para evento dentro do intervalo), uma curva de
# referência para os gráficos (tempo, sobrevida) e S(4) de referência.

# Modo "tabela": números em risco e censuras acumuladas por tempo
reconstruir_tabela <- function(id, n_total) {
  arq <- file.path(PASTA_DADOS, paste0(id, "_tabela.csv"))
  tb <- ler_csv(arq)
  if (nrow(tb) < 2) stop("Arquivo ", basename(arq), " vazio: preencha a tabela antes (ver LEIA-ME).")
  names(tb) <- c("tempo", "n_risco", "cens_acum")
  tb <- tb[order(tb$tempo), ]
  if (tb$tempo[1] != 0 || tb$n_risco[1] != n_total)
    warning(id, ": a primeira linha deveria ser tempo 0 com n = ", n_total)
  J <- nrow(tb)
  t0 <- tb$tempo[-J]; t1 <- tb$tempo[-1]
  cens <- diff(tb$cens_acum)
  ev   <- tb$n_risco[-J] - tb$n_risco[-1] - cens
  if (any(ev < 0) || any(cens < 0))
    stop(id, ": eventos ou censuras negativos em algum intervalo. Confira os números em risco e as censuras acumuladas.")
  tc <- t0 + CENSURA_NO_INTERVALO * (t1 - t0)
  dados <- rbind(
    data.frame(L = rep(t0, ev),   R = rep(t1, ev)),          # eventos dentro do intervalo
    data.frame(L = rep(tc, cens), R = rep(NA_real_, sum(cens))),  # censuras no intervalo
    data.frame(L = rep(tb$tempo[J], tb$n_risco[J]), R = rep(NA_real_, tb$n_risco[J]))  # vivos sem evento no fim
  )
  dados$L <- pmax(dados$L, 1e-10)  # limite mínimo desprezível; 1e-4 distorcia famílias com risco alto perto de zero
  # estimativa atuarial (censuras contam meio intervalo em risco)
  s_at <- cumprod(1 - ev / (tb$n_risco[-J] - cens / 2))
  ref <- data.frame(tempo = tb$tempo, sobrevida = c(1, s_at))
  s4 <- approx(ref$tempo, ref$sobrevida, xout = 4, rule = 2)$y
  message(sprintf("  tabela: %d pacientes, %d eventos, %d censuras no seguimento, %d em risco no fim",
                  nrow(dados), sum(ev), sum(cens), tb$n_risco[J]))
  list(dados = dados, ref = ref, s4_ref = s4, rotulo_ref = "estimativa atuarial")
}

# Modo "km": curva digitalizada + números em risco, algoritmo de Guyot
reconstruir_km <- function(id, n_total, eventos) {
  km <- ler_csv(file.path(PASTA_DADOS, paste0(id, "_km.csv")))
  rk <- ler_csv(file.path(PASTA_DADOS, paste0(id, "_risco.csv")))
  if (nrow(km) < 3) stop("Arquivo ", id, "_km.csv vazio: digitalize a curva antes (ver LEIA-ME).")
  names(km) <- c("tempo", "sobrevida"); names(rk) <- c("tempo", "n_risco")
  if (max(km$sobrevida, na.rm = TRUE) > 1.5) km$sobrevida <- km$sobrevida / 100  # aceita %
  km <- km[order(km$tempo), ]
  km$sobrevida <- pmin(1, cummin(km$sobrevida))           # força curva não crescente
  if (km$tempo[1] > 0) km <- rbind(data.frame(tempo = 0, sobrevida = 1), km)
  rk <- rk[rk$tempo <= max(km$tempo), ]
  prep <- preprocess(dat = km, trisk = rk$tempo, nrisk = rk$n_risco, totalpts = n_total, maxy = 1)
  ev <- if (is.na(eventos)) NULL else eventos
  ipd <- getIPD(prep = prep, armID = 1, tot.events = ev)$IPD
  tm <- pmax(as.numeric(ipd[[1]]), 1e-4); st <- as.integer(ipd[[2]])
  dados <- data.frame(L = tm, R = ifelse(st == 1, tm, NA_real_))
  s4_dig <- approx(km$tempo, km$sobrevida, xout = 4, method = "constant", f = 0, rule = 2, ties = min)$y
  fit_km <- survfit(Surv(tm, st) ~ 1)
  s4_rec <- summary(fit_km, times = 4, extend = TRUE)$surv
  message(sprintf("  Guyot: %d pacientes, %d eventos; S(4) reconstruído %.3f, digitalizado %.3f",
                  length(tm), sum(st), s4_rec, s4_dig))
  if (abs(s4_rec - s4_dig) > 0.01)
    warning(id, ": a reconstrução difere da curva digitalizada em mais de 1 ponto aos 4 anos. Confira os números em risco.")
  ref <- data.frame(tempo = c(0, fit_km$time), sobrevida = c(1, fit_km$surv))
  list(dados = dados, ref = ref, s4_ref = s4_rec, rotulo_ref = "KM reconstruído", km_digit = km)
}

# ---------------------------------------------------------------- 2. AJUSTES
# Valores iniciais (escala natural, na ordem do flexsurv). O otimizador padrão para
# cedo em algumas famílias com platô; por isso cada família é ajustada a partir de
# vários pontos e fica o de maior verossimilhança, refinado depois por Nelder-Mead.
grade <- function(...) as.matrix(expand.grid(..., KEEP.OUT.ATTRS = FALSE))
INITS <- list(
  gompertz    = grade(shape = c(-0.3, -1, -3, -10), rate = c(0.05, 0.3, 1, 3)),
  weibull     = grade(shape = c(0.15, 0.3, 0.5, 0.8), scale = c(1, 3, 8, 30, 300, 1e4)),
  lognormal   = grade(meanlog = c(0, 1, 3, 6, 10, 16), sdlog = c(1, 2, 4.5, 10)),
  loglogistic = grade(shape = c(0.15, 0.3, 0.5, 0.8), scale = c(1, 3, 8, 30, 300, 1e4)),
  exponential = grade(rate = c(0.02, 0.1, 0.3)),
  mixture_cure_weibull = grade(theta = c(0.3, 0.6, 0.85), shape = c(0.4, 1, 3, 8), scale = c(0.2, 1, 3)),
  gengamma    = grade(mu = c(-2, 0, 2, 5), sigma = c(0.2, 1, 2, 5), Q = c(-15, -4, -1, 0.5))
)
ajuste_unico <- function(fm, dados, inits = NULL, ...) {
  tryCatch(suppressWarnings({
    if (fm$nome == "mixture_cure_weibull") {
      if (is.null(inits)) flexsurvcure(Surv(L, R, type = "interval2") ~ 1, data = dados, dist = "weibull", mixture = TRUE, ...)
      else flexsurvcure(Surv(L, R, type = "interval2") ~ 1, data = dados, dist = "weibull", mixture = TRUE, inits = inits, ...)
    } else {
      if (is.null(inits)) flexsurvreg(Surv(L, R, type = "interval2") ~ 1, data = dados, dist = fm$dist, ...)
      else flexsurvreg(Surv(L, R, type = "interval2") ~ 1, data = dados, dist = fm$dist, inits = inits, ...)
    }
  }), error = function(e) NULL)
}
ajustar <- function(dados) {
  lapply(seq_len(nrow(FAMILIAS)), function(j) {
    fm <- FAMILIAS[j, ]
    ini <- INITS[[fm$nome]]
    cand <- c(list(ajuste_unico(fm, dados)),
              lapply(seq_len(nrow(ini)), function(r) ajuste_unico(fm, dados, inits = unname(ini[r, ]))))
    cand <- Filter(function(f) !is.null(f) && is.finite(f$loglik), cand)
    if (length(cand) == 0) {
      message("  falhou ", fm$rotulo)
      return(list(familia = fm$nome, fit = NULL, p = rep(NA, 3), aic = NA, bic = NA))
    }
    fit <- cand[[which.max(vapply(cand, function(f) f$loglik, numeric(1)))]]
    nm <- ajuste_unico(fm, dados, inits = unname(fit$res[, "est"]), method = "Nelder-Mead",
                       control = list(maxit = 20000, reltol = 1e-12))
    if (!is.null(nm) && is.finite(nm$loglik) && nm$loglik > fit$loglik) fit <- nm
    est <- setNames(fit$res[, "est"], rownames(fit$res))   # mantém o nome mesmo com 1 parâmetro
    p <- unname(est[PARAMS[[fm$nome]]])
    k <- length(est); n <- nrow(dados)
    list(familia = fm$nome, fit = fit, p = c(p, rep(NA, 3 - length(p))),
         aic = fit$AIC, bic = -2 * fit$loglik + k * log(n))
  })
}

# ---------------------------------------------------------------- EXECUÇÃO
res <- list(); linhas_tab <- list()
for (i in seq_len(nrow(CURVAS))) {
  cv <- CURVAS[i, ]
  message("\n== ", cv$rotulo)
  r <- if (MODO == "tabela") reconstruir_tabela(cv$id, cv$n_total)
       else reconstruir_km(cv$id, cv$n_total, cv$eventos)
  message(sprintf("  S(4): %s %.3f; publicado %.3f", r$rotulo_ref, r$s4_ref, cv$s4_public))
  if (!grepl("exemplo", PASTA_DADOS) && abs(r$s4_ref - cv$s4_public) > 0.02)
    warning(cv$id, ": S(4) dos dados reconstruídos difere do publicado em mais de 2 pontos. Revise a entrada de dados.")
  fits <- ajustar(r$dados)
  res[[cv$id]] <- list(rec = r, fits = fits)
  write.csv(r$dados, file.path(PASTA_SAIDA, paste0("dados_reconstruidos_", cv$id, ".csv")), row.names = FALSE)
  for (j in seq_along(fits)) {
    f <- fits[[j]]; ok <- tem_params(f$familia, f$p)
    s_t <- if (ok) surv_planilha(f$familia, f$p, c(1:T_OBS, 20)) else rep(NA, T_OBS + 1)
    linhas_tab[[length(linhas_tab) + 1]] <- data.frame(
      curva = cv$id, familia = f$familia, rotulo = FAMILIAS$rotulo[j],
      AIC = f$aic, BIC = f$bic, p1 = f$p[1], p2 = f$p[2], p3 = f$p[3],
      S4_modelo = s_t[4], S4_dados = r$s4_ref, S4_publicado = cv$s4_public,
      S7_modelo = s_t[7], S20_modelo = s_t[T_OBS + 1])
  }
}
tab <- do.call(rbind, linhas_tab)
tab <- do.call(rbind, lapply(split(tab, tab$curva), function(d) {
  d$dAIC <- d$AIC - min(d$AIC, na.rm = TRUE); d$dBIC <- d$BIC - min(d$BIC, na.rm = TRUE); d
}))
tab <- tab[order(match(tab$curva, CURVAS$id), match(tab$familia, FAMILIAS$nome)), ]
write.csv(tab, file.path(PASTA_SAIDA, "tabela_ajuste_AIC_BIC.csv"), row.names = FALSE)

# ---------------------------------------------------------------- 3. PARÂMETROS PARA A PLANILHA
# Mesma disposição da aba Curvas (linhas 5 a 11, colunas C a N): copiar e colar valores.
plan <- data.frame(n = FAMILIAS$n, familia = FAMILIAS$rotulo)
for (id in CURVAS$id) {
  d <- tab[tab$curva == id, ]
  for (k in 1:3) plan[[paste0(id, "_p", k)]] <- d[[paste0("p", k)]][match(FAMILIAS$nome, d$familia)]
}
write.csv(plan, file.path(PASTA_SAIDA, "parametros_para_aba_Curvas.csv"), row.names = FALSE, na = "")

# ---------------------------------------------------------------- 4. COMPARAÇÃO COM OS PARÂMETROS ATUAIS
atuais <- ler_csv("dados/parametros_atuais.csv")
tt_c <- c(1, 2, 4, 7, 20)
comp <- do.call(rbind, lapply(seq_len(nrow(atuais)), function(i) {
  a <- atuais[i, ]; pa <- as.numeric(a[c("p1", "p2", "p3")])
  pn <- as.numeric(tab[tab$curva == a$curva & tab$familia == a$familia, c("p1", "p2", "p3")])
  sa <- surv_planilha(a$familia, pa, tt_c)
  sn <- if (tem_params(a$familia, pn)) surv_planilha(a$familia, pn, tt_c) else rep(NA, 5)
  data.frame(curva = a$curva, familia = a$familia,
             S1_atual = sa[1], S1_novo = sn[1], S4_atual = sa[3], S4_novo = sn[3],
             S7_atual = sa[4], S7_novo = sn[4], S20_atual = sa[5], S20_novo = sn[5],
             max_dif_pp = 100 * max(abs(sa - sn)))
}))
write.csv(comp, file.path(PASTA_SAIDA, "comparacao_com_parametros_atuais.csv"), row.names = FALSE)

# Coerência OS >= DFS (o modelo corta a OS na DFS; diferenças grandes merecem atenção)
coer <- do.call(rbind, lapply(c("c", "i"), function(b) do.call(rbind, lapply(FAMILIAS$nome, function(fm) {
  pd <- as.numeric(tab[tab$curva == paste0("dfs_", b) & tab$familia == fm, c("p1", "p2", "p3")])
  po <- as.numeric(tab[tab$curva == paste0("os_", b) & tab$familia == fm, c("p1", "p2", "p3")])
  if (!tem_params(fm, pd) || !tem_params(fm, po)) return(NULL)
  tt <- seq(0.1, T_OBS, by = 0.1)
  gap <- surv_planilha(fm, pd, tt) - surv_planilha(fm, po, tt)
  data.frame(braco = b, familia = fm, max_DFS_acima_OS_pp = round(100 * max(0, gap), 2),
             anos_com_DFS_acima_OS = round(sum(gap > 1e-6) * 0.1, 1))
}))))
write.csv(coer, file.path(PASTA_SAIDA, "coerencia_OS_maior_que_DFS.csv"), row.names = FALSE)

# Matriz de variância do Gompertz (para atualizar a PSA no Python)
vc <- lapply(res, function(x) {
  f <- x$fits[[which(FAMILIAS$nome == "gompertz")]]$fit
  if (is.null(f)) return(NULL)
  list(est = as.list(f$res[, "est"]), vcov_escala_ajuste = unname(vcov(f)), nomes = rownames(f$res))
})
writeLines(jsonlite::toJSON(vc, auto_unbox = TRUE, digits = 10, pretty = TRUE),
           file.path(PASTA_SAIDA, "gompertz_vcov.json"))

# ---------------------------------------------------------------- 5. GRÁFICOS
cores <- c("#1F4E79", "#C55A11", "#548235", "#7030A0", "#BF9000", "#2E75B6", "#A50021")
for (id in CURVAS$id) {
  r <- res[[id]]$rec; rot <- CURVAS$rotulo[CURVAS$id == id]
  for (h in c(T_OBS + 1, T_GRAFICO)) {
    tt <- seq(0.01, h, length.out = 400)
    linhas <- do.call(rbind, lapply(res[[id]]$fits, function(f) {
      if (!tem_params(f$familia, f$p)) return(NULL)
      data.frame(t = tt, s = surv_planilha(f$familia, f$p, tt),
                 familia = FAMILIAS$rotulo[FAMILIAS$nome == f$familia])
    }))
    linhas$familia <- factor(linhas$familia, levels = FAMILIAS$rotulo)
    g <- ggplot() +
      geom_step(data = r$ref, aes(tempo, sobrevida), linewidth = 0.8, colour = "black") +
      geom_line(data = linhas, aes(t, s, colour = familia), linewidth = 0.6) +
      geom_vline(xintercept = T_OBS, linetype = 2, colour = "grey60") +
      scale_colour_manual(values = cores, name = NULL) +
      scale_y_continuous(limits = c(0, 1), labels = scales::percent) +
      labs(title = rot,
           subtitle = if (h > T_OBS + 1) "Extrapolação das curvas (antes da cura e da tábua de vida aplicadas no modelo)"
                      else paste0("Preto: ", r$rotulo_ref, "; cores: famílias ajustadas"),
           x = "Anos", y = "Sobrevida") +
      theme_minimal(base_size = 11) + theme(legend.position = "bottom")
    if (!is.null(r$km_digit))
      g <- g + geom_point(data = r$km_digit, aes(tempo, sobrevida), size = 0.7, colour = "grey50")
    ggsave(file.path(PASTA_SAIDA, sprintf("fig_%s_%dy.png", id, h)), g, width = 8, height = 5.5, dpi = 200)
  }
}

# ---------------------------------------------------------------- RESUMO
message("\n================ RESUMO ================")
ref <- atuais[, c("curva", "familia", "AIC_referencia")]
resumo <- merge(tab, ref, by = c("curva", "familia"), sort = FALSE)
resumo$dif_AIC_ref <- round(resumo$AIC - resumo$AIC_referencia, 2)
resumo <- resumo[order(match(resumo$curva, CURVAS$id), match(resumo$familia, FAMILIAS$nome)), ]
write.csv(resumo, file.path(PASTA_SAIDA, "tabela_ajuste_AIC_BIC.csv"), row.names = FALSE)
print(resumo[, c("curva", "rotulo", "AIC", "AIC_referencia", "dif_AIC_ref", "dAIC", "S4_modelo", "S4_publicado", "S7_modelo")],
      digits = 4, row.names = FALSE)
message("\ndif_AIC_ref perto de 0 (até ~0,1) = o R chegou ao mesmo ajuste do modelo. Gama generalizada pode diferir: a estimativa fica na fronteira.")
message("\nGompertz: parâmetros atuais x novos (S em 4, 7 e 20 anos; maior diferença em pontos percentuais)")
print(comp[comp$familia == "gompertz", c("curva", "S4_atual", "S4_novo", "S7_atual", "S7_novo", "S20_atual", "S20_novo", "max_dif_pp")],
      digits = 3, row.names = FALSE)
message("\nArquivos gravados em: ", normalizePath(PASTA_SAIDA))
writeLines(capture.output(sessionInfo()), file.path(PASTA_SAIDA, "sessionInfo.txt"))
