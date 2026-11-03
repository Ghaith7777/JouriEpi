.bd_tarone <- function(tables, common_or) {
  if (length(tables) < 2L || !is.finite(common_or) || common_or <= 0) return(NULL)
  expected <- variance <- numeric(length(tables))
  for (i in seq_along(tables)) {
    x <- tables[[i]]; apb <- x[1] + x[2]; apc <- x[1] + x[3]; dma <- x[4] - x[1]
    qa <- 1 - common_or; qb <- common_or * (apb + apc) + dma; qc <- -common_or * apb * apc
    disc <- qb^2 - 4 * qa * qc
    if (!is.finite(disc) || disc < 0) return(NULL)
    expected[i] <- if (abs(qa) < 1e-12) {
      if (qb == 0) return(NULL)
      -qc / qb
    } else (-qb + sqrt(disc)) / (2 * qa)
    cells <- c(expected[i], apc-expected[i], apb-expected[i], dma+expected[i])
    if (any(!is.finite(cells)) || any(cells <= 0)) return(NULL)
    variance[i] <- 1 / sum(1 / cells)
  }
  residual <- vapply(seq_along(tables), function(i) tables[[i]][1] - expected[i], numeric(1))
  stat <- sum(residual^2 / variance)
  tarone <- max(0, stat - sum(residual)^2 / sum(variance))
  list(statistic=stat, tarone_statistic=tarone,
       p_value=stats::pchisq(stat, df=length(tables)-1L, lower.tail=FALSE),
       tarone_p_value=stats::pchisq(tarone, df=length(tables)-1L, lower.tail=FALSE))
}

epi_stratified <- function(strata, conf_level=0.95) {
  if (!is.list(strata) || length(strata) < 1L) stop("strata must be a non-empty named list")
  if (is.null(names(strata))) names(strata) <- paste0("Stratum ", seq_along(strata))
  if (anyNA(names(strata)) || any(!nzchar(trimws(names(strata)))) || anyDuplicated(names(strata)))
    stop("stratum labels must be non-empty and unique", call.=FALSE)
  if (length(conf_level)!=1L || !is.numeric(conf_level) || !is.finite(conf_level) || conf_level<=0 || conf_level>=1 || 1-(1-conf_level)/2 >= 1)
    stop("conf_level must be in (0,1)")
  tables <- lapply(strata, .validate_counts)
  if (any(vapply(tables, function(x) x[1]+x[2]==0 || x[3]+x[4]==0, logical(1))))
    stop("each stratum must contain exposed and unexposed participants")
  totals <- vapply(tables, sum, numeric(1))
  mh_num <- sum(vapply(seq_along(tables), function(i) tables[[i]][1]*tables[[i]][4]/totals[i], numeric(1)))
  mh_den <- sum(vapply(seq_along(tables), function(i) tables[[i]][2]*tables[[i]][3]/totals[i], numeric(1)))
  mh_or <- if (mh_den>0) mh_num/mh_den else if (mh_num>0) Inf else NA_real_
  mh_rr_num <- sum(vapply(seq_along(tables), function(i) tables[[i]][1] *
    (tables[[i]][3] + tables[[i]][4]) / totals[i], numeric(1)))
  mh_rr_den <- sum(vapply(seq_along(tables), function(i) tables[[i]][3] *
    (tables[[i]][1] + tables[[i]][2]) / totals[i], numeric(1)))
  mh_rr <- if (mh_rr_den>0) mh_rr_num/mh_rr_den else if (mh_rr_num>0) Inf else NA_real_
  rbg_var <- mh_ci <- NULL
  if (is.finite(mh_or) && mh_or>0 && mh_num>0 && mh_den>0) {
    rbg_a <- sum(vapply(seq_along(tables), function(i) { x<-tables[[i]]; (x[1]+x[4])*x[1]*x[4]/totals[i]^2 }, numeric(1)))
    rbg_b <- sum(vapply(seq_along(tables), function(i) { x<-tables[[i]]; (x[2]+x[3])*x[2]*x[3]/totals[i]^2 }, numeric(1)))
    rbg_cross <- sum(vapply(seq_along(tables), function(i) { x<-tables[[i]]; ((x[1]+x[4])*x[2]*x[3]+(x[2]+x[3])*x[1]*x[4])/totals[i]^2 }, numeric(1)))
    if (rbg_a>0 && rbg_b>0) {
      rbg_var <- .5*rbg_a/mh_num^2 + .5*rbg_b/mh_den^2 + .5*rbg_cross/(mh_num*mh_den)
      if (is.finite(rbg_var) && rbg_var>=0) {
        z <- stats::qnorm(1-(1-conf_level)/2)
        mh_ci <- exp(log(mh_or)+c(-1,1)*z*sqrt(rbg_var))
      } else rbg_var <- NULL
    }
  }
  crude <- Reduce(`+`, tables)
  crude_or <- if (crude[2]*crude[3]>0) crude[1]*crude[4]/(crude[2]*crude[3]) else if (crude[1]*crude[4]>0) Inf else NA_real_
  details <- lapply(seq_along(tables), function(i) {
    x<-tables[[i]]; n1<-x[1]+x[2]; n0<-x[3]+x[4]
    stratum_or <- if (x[2]*x[3]>0) x[1]*x[4]/(x[2]*x[3]) else if (x[1]*x[4]>0) Inf else NA_real_
    stratum_rr <- if (x[3]>0) (x[1]/n1)/(x[3]/n0) else if (x[1]>0) Inf else NA_real_
    or_ci <- if (all(x>0) && is.finite(stratum_or) && stratum_or>0)
      exp(log(stratum_or)+c(-1,1)*stats::qnorm(1-(1-conf_level)/2)*sqrt(sum(1/x))) else NULL
    rr_var <- if (x[1]>0 && x[3]>0 && stratum_rr>0 && is.finite(stratum_rr))
      1/x[1]-1/n1+1/x[3]-1/n0 else NA_real_
    rr_ci <- if (is.finite(rr_var) && rr_var>=0)
      exp(log(stratum_rr)+c(-1,1)*stats::qnorm(1-(1-conf_level)/2)*sqrt(rr_var)) else NULL
    corrected <- x + if (any(x==0)) .5 else 0
    list(label=names(tables)[i], counts=x,
      risk_ratio=stratum_rr, risk_ratio_ci=rr_ci, odds_ratio=stratum_or,
      odds_ratio_ci=or_ci,
      odds_ratio_haldane_anscombe=corrected[1]*corrected[4]/(corrected[2]*corrected[3]))
  })
  ors <- vapply(details, `[[`, numeric(1), "odds_ratio")
  crude_side <- if (is.na(crude_or) || crude_or==1) 0 else if (crude_or<1) -1 else 1
  stratum_sides <- ifelse(is.na(ors) | ors==1, 0, ifelse(ors<1,-1,1))
  directional_reversal <- crude_side!=0 && all(stratum_sides == -crude_side)
  outside_hull <- is.finite(crude_or) && all(is.finite(ors)) &&
    (crude_or < min(ors) || crude_or > max(ors))
  # A pooled estimate outside the range of stratum estimates alone is not
  # sufficient to label Simpson's paradox (odds-ratio non-collapsibility can
  # produce that pattern). Match the Python core: every stratum must reverse
  # the crude direction relative to the null.
  simpson <- directional_reversal
  bd <- .bd_tarone(tables, mh_or)
  pct <- if (is.finite(crude_or) && crude_or!=0 && is.finite(mh_or)) abs(crude_or-mh_or)/abs(crude_or) else NA_real_
  warnings <- character()
  if (is.finite(pct) && pct>=.1) warnings <- c(warnings,"Crude and Mantel-Haenszel odds ratios differ by at least 10%.")
  if (simpson) warnings <- c(warnings,"Simpson's paradox: stratum-specific odds ratios reverse the crude direction.")
  if (!is.null(bd) && bd$p_value<.05) warnings <- c(warnings,"Evidence of odds-ratio heterogeneity (Breslow-Day test).")
  .new_result("stratified", list(strata=details, crude_odds_ratio=crude_or,
    mantel_haenszel_odds_ratio=mh_or, mantel_haenszel_odds_ratio_ci=mh_ci,
    mantel_haenszel_risk_ratio=mh_rr,
    mantel_haenszel_odds_ratio_log_variance=rbg_var,
    breslow_day_statistic=if(is.null(bd)) NA_real_ else bd$statistic,
    breslow_day_tarone_statistic=if(is.null(bd)) NA_real_ else bd$tarone_statistic,
    breslow_day_df=length(tables)-1L,
    breslow_day_p_value=if(is.null(bd)) NA_real_ else bd$p_value,
    tarone_corrected_p_value=if(is.null(bd)) NA_real_ else bd$tarone_p_value,
    effect_measure_modification=!is.null(bd) && bd$p_value<.05,
    percent_change=pct, meaningful_confounding=is.finite(pct)&&pct>=.1,
    simpsons_paradox_detected=simpson, simpsons_paradox_outside_stratum_or_range=outside_hull,
    simpsons_paradox_directional_reversal=directional_reversal, warnings=warnings),
    list(strata=strata,conf_level=conf_level))
}



epi_interaction <- function(counts=NULL, alpha=0.05, rr11=NULL, rr10=NULL,
                                 rr01=NULL, cov_matrix=NULL, conf_level=NULL) {
  rr_mode <- !is.null(rr11) || !is.null(rr10) || !is.null(rr01)
  if (!rr_mode) return(.additive_interaction_counts(counts, alpha=alpha))
  rr <- unname(c(rr11=rr11, rr10=rr10, rr01=rr01))
  if (length(rr)!=3L || any(lengths(as.list(rr)) != 1L) || !is.numeric(rr) || any(!is.finite(rr)) || any(rr<=0))
    stop("rr11, rr10 and rr01 must be finite positive scalar risk ratios")
  if (is.null(conf_level)) conf_level <- 1-alpha
  if (length(conf_level)!=1L || !is.numeric(conf_level) || !is.finite(conf_level) || conf_level<=0 || conf_level>=1 || 1-(1-conf_level)/2 >= 1)
    stop("conf_level must be in (0,1)")
  reri <- rr[1]-rr[2]-rr[3]+1
  ap <- reri/rr[1]
  denominator <- rr[2]+rr[3]-2
  si <- if (abs(denominator)>1e-12) (rr[1]-1)/denominator else NA_real_
  estimates <- c(RERI=reri, AP=ap, SI=si)
  gradient <- rbind(c(1,-1,-1),
    c((rr[2]+rr[3]-1)/rr[1]^2, -1/rr[1], -1/rr[1]),
    c(if(abs(denominator)>1e-12) 1/denominator else NA_real_,
      if(abs(denominator)>1e-12) -(rr[1]-1)/denominator^2 else NA_real_,
      if(abs(denominator)>1e-12) -(rr[1]-1)/denominator^2 else NA_real_))
  intervals <- NULL
  if (!is.null(cov_matrix)) {
    cov_matrix <- as.matrix(cov_matrix)
    if (!is.numeric(cov_matrix) || !identical(dim(cov_matrix), c(3L,3L)) || any(!is.finite(cov_matrix)) ||
        !isTRUE(all.equal(cov_matrix, t(cov_matrix), tolerance=1e-10)))
      stop("cov_matrix must be a finite symmetric 3x3 covariance matrix in rr11, rr10, rr01 order")
    if (min(eigen(cov_matrix, symmetric=TRUE, only.values=TRUE)$values) < -1e-10)
      stop("cov_matrix must be positive semidefinite")
    if (any(!is.finite(gradient))) stop("the synergy index is undefined for this input")
    variances <- diag(gradient %*% cov_matrix %*% t(gradient))
    if (any(variances < -1e-10)) stop("cov_matrix produces a negative delta-method variance")
    z <- stats::qnorm(1-(1-conf_level)/2)
    se <- sqrt(pmax(0,variances))
    intervals <- cbind(lower=estimates-z*se, upper=estimates+z*se)
  }
  if (any(!is.finite(estimates))) stop("RERI/AP/SI are not all finite for these risk ratios")
  .new_result("additive_interaction_rr", list(risk_ratios=rr, reri=reri,
    attributable_proportion=ap, synergy_index=si, covariance=cov_matrix,
    confidence_intervals=intervals, method="Multivariate delta method on risk-ratio measures"),
    list(rr11=rr11,rr10=rr10,rr01=rr01,conf_level=conf_level))
}
