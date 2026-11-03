.validate_counts <- function(counts, n = 4L) {
  if (!is.numeric(counts) || length(counts) != n || any(!is.finite(counts)) ||
      any(counts < 0) || any(counts != floor(counts))) {
    stop("counts must contain ", n, " nonnegative integer cell counts", call. = FALSE)
  }
  as.numeric(counts)
}

e_value <- function(estimate, confidence_interval = NULL) {
  if (length(estimate) != 1L || !is.numeric(estimate) || !is.finite(estimate) || estimate <= 0)
    stop("estimate must be finite and positive", call. = FALSE)
  ev <- function(rr) { rr <- if (rr < 1) 1 / rr else rr; rr + sqrt(rr * (rr - 1)) }
  ci_ev <- NULL
  if (!is.null(confidence_interval)) {
    if (length(confidence_interval) != 2L || !is.numeric(confidence_interval) || any(!is.finite(confidence_interval)) ||
        any(confidence_interval <= 0) || confidence_interval[1] > confidence_interval[2] ||
        estimate < confidence_interval[1] || estimate > confidence_interval[2])
      stop("confidence_interval must be an ordered positive pair containing estimate", call. = FALSE)
    ci_ev <- if (confidence_interval[1] <= 1 && confidence_interval[2] >= 1) 1 else
      ev(if (estimate >= 1) confidence_interval[1] else confidence_interval[2])
  }
  list(e_value = ev(estimate), confidence_limit_e_value = ci_ev)
}

epi_evalue <- function(estimate, confidence_interval = NULL, scale = c("RR", "OR"),
                   or_method = NULL, baseline_risk = NULL) {
  scale <- match.arg(scale)
  if (length(estimate) != 1L || !is.numeric(estimate) || !is.finite(estimate) || estimate <= 0)
    stop("estimate must be finite and positive")
  convert <- function(x) {
    if (scale == "RR") {
      if (!is.null(or_method) || !is.null(baseline_risk)) stop("OR conversion options require scale='OR'")
      return(x)
    }
    if (identical(or_method, "sqrt_approximation") && is.null(baseline_risk)) return(sqrt(x))
    if (identical(or_method, "baseline_risk") && length(baseline_risk) == 1L &&
        is.numeric(baseline_risk) && is.finite(baseline_risk) && baseline_risk > 0 && baseline_risk < 1)
      return(x / (1 - baseline_risk + baseline_risk * x))
    stop("OR requires or_method='sqrt_approximation' or 'baseline_risk' with baseline_risk in (0,1)")
  }
  rr <- convert(estimate)
  if (!is.null(confidence_interval) && (!is.numeric(confidence_interval) || length(confidence_interval)!=2L))
    stop("confidence_interval must be a numeric pair", call.=FALSE)
  ci <- if (is.null(confidence_interval)) NULL else vapply(confidence_interval, convert, numeric(1))
  result <- e_value(rr, ci)
  result$estimate <- estimate; result$input_scale <- scale
  result$risk_ratio_estimate <- rr
  result$risk_ratio_confidence_interval <- ci
  result$confidence_interval_includes_null <- if (is.null(ci)) NULL else ci[1] <= 1 && ci[2] >= 1
  result$conversion_method <- if (scale == "RR") "none (risk ratio input)" else or_method
  result$baseline_risk <- baseline_risk
  .new_result("evalue", result, list(estimate=estimate, confidence_interval=confidence_interval))
}

.additive_interaction_counts <- function(counts, alpha = 0.05) {
  if (!is.matrix(counts)) counts <- as.matrix(counts)
  if (!identical(dim(counts), c(4L, 2L))) stop("counts must be a 4x2 matrix: cases, non-cases for groups 00,10,01,11")
  if (!is.numeric(counts) || any(!is.finite(counts)) || any(counts <= 0) || any(counts != floor(counts)))
    stop("all four groups require positive integer case and non-case counts")
  if (length(alpha) != 1L || !is.numeric(alpha) || !is.finite(alpha) || alpha <= 0 || alpha >= 1 || 1-alpha/2 >= 1)
    stop("alpha must be finite and in (0,1)", call. = FALSE)
  logits <- log(counts[,1] / counts[,2])
  variances <- 1/counts[,1] + 1/counts[,2]
  contrast <- rbind(c(-1,1,0,0), c(-1,0,1,0), c(1,-1,-1,1))
  beta <- as.vector(contrast %*% logits)
  covariance <- contrast %*% diag(variances) %*% t(contrast)
  calc <- function(b) {
    or10 <- exp(b[1]); or01 <- exp(b[2]); or11 <- exp(sum(b))
    reri <- or11-or10-or01+1; ap <- reri/or11
    denominator <- (or10-1)+(or01-1)
    if (abs(denominator) <= 1e-12) stop("RERI/AP/SI are not all estimable: synergy-index denominator is zero", call. = FALSE)
    si <- (or11-1)/denominator
    c(reri=reri, attributable_proportion=ap, synergy_index=si)
  }
  est <- calc(beta); gradient <- matrix(0, 3, 3)
  for (j in 1:3) { step <- 1e-5*max(1,abs(beta[j])); hi <- lo <- beta; hi[j] <- hi[j]+step; lo[j] <- lo[j]-step; gradient[,j] <- (calc(hi)-calc(lo))/(2*step) }
  se <- sqrt(pmax(0, diag(gradient %*% covariance %*% t(gradient))))
  z <- qnorm(1-alpha/2); ci <- cbind(est-z*se, est+z*se)
  .new_result("additive_interaction", list(odds_ratio_10=exp(beta[1]), odds_ratio_01=exp(beta[2]),
    odds_ratio_11=exp(sum(beta)), reri=est[1], reri_ci=ci[1,], attributable_proportion=est[2],
    ap_ci=ci[2,], synergy_index=est[3], si_ci=ci[3,], covariance_beta=covariance),
    list(counts=counts, alpha=alpha))
}
