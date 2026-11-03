epi_fagan <- function(pretest_probability, likelihood_ratio) {
  if (length(pretest_probability)!=1L || !is.numeric(pretest_probability) ||
      !is.finite(pretest_probability) || pretest_probability<=0 || pretest_probability>=1)
    stop("pretest_probability must be finite and in (0,1)", call.=FALSE)
  if (length(likelihood_ratio)!=1L || !is.numeric(likelihood_ratio) ||
      is.na(likelihood_ratio) || likelihood_ratio<0)
    stop("likelihood_ratio must be nonnegative and not NaN", call.=FALSE)
  if (is.infinite(likelihood_ratio)) return(1)
  if (likelihood_ratio==0) return(0)
  log_odds <- log(pretest_probability)-log1p(-pretest_probability)+log(likelihood_ratio)
  if (log_odds >= 0) 1/(1+exp(-log_odds)) else {
    odds <- exp(log_odds); odds/(1+odds)
  }
}

epi_diagnostic <- function(tp, fp, fn, tn, alpha=0.05, conf_level=NULL) {
  x <- .validate_counts(c(tp,fp,fn,tn)); if (sum(x)==0) stop("at least one observation is required")
  if (!is.null(conf_level)) {
    if (length(conf_level)!=1L || !is.numeric(conf_level) || !is.finite(conf_level) || conf_level<=0 || conf_level>=1 || 1-(1-conf_level)/2 >= 1)
      stop("conf_level must be in (0,1)")
    alpha <- 1-conf_level
  }
  if (length(alpha)!=1L || !is.numeric(alpha) || !is.finite(alpha) || alpha<=0 || alpha>=1 || 1-alpha/2>=1)
    stop("alpha must be finite and in (0,1)", call.=FALSE)
  z <- qnorm(1-alpha/2)
  wilson <- function(k,n) { if(n==0) return(NULL); p<-k/n; den<-1+z^2/n; mid<-(p+z^2/(2*n))/den; half<-z*sqrt(p*(1-p)/n+z^2/(4*n^2))/den; c(max(0,mid-half),min(1,mid+half)) }
  wald <- function(k,n) { if(n==0) return(NULL); p<-k/n; se<-sqrt(p*(1-p)/n); c(max(0,p-z*se),min(1,p+z*se)) }
  sens <- if(tp+fn>0) tp/(tp+fn) else NA_real_; spec <- if(tn+fp>0) tn/(tn+fp) else NA_real_
  ppv <- if(tp+fp>0) tp/(tp+fp) else NA_real_; npv <- if(tn+fn>0) tn/(tn+fn) else NA_real_
  lr_pos <- if(!is.finite(sens)||!is.finite(spec)||spec==1) NA_real_ else sens/(1-spec)
  lr_neg <- if(!is.finite(sens)||!is.finite(spec)||spec==0) NA_real_ else (1-sens)/spec
  dor <- if(fp*fn>0) tp*tn/(fp*fn) else if(tp*tn>0) Inf else NA_real_
  accuracy <- (tp+tn)/sum(x)
  balanced_accuracy <- if(is.finite(sens)&&is.finite(spec)) (sens+spec)/2 else NA_real_
  f1 <- if(2*tp+fp+fn>0) 2*tp/(2*tp+fp+fn) else NA_real_
  fpr <- if(is.finite(spec)) 1-spec else NA_real_
  fnr <- if(is.finite(sens)) 1-sens else NA_real_
  lr_pos_var <- if(tp>0 && fp>0 && tp+fn>0 && fp+tn>0) 1/tp-1/(tp+fn)+1/fp-1/(fp+tn) else NA_real_
  lr_neg_var <- if(fn>0 && tn>0 && tp+fn>0 && fp+tn>0) 1/fn-1/(tp+fn)+1/tn-1/(fp+tn) else NA_real_
  dor_var <- if(all(x>0)) sum(1/x) else NA_real_
  log_ci <- function(value, variance) if(is.finite(value)&&value>0&&is.finite(variance)&&variance>=0)
    exp(log(value)+c(-1,1)*z*sqrt(variance)) else NULL
  .new_result("diagnostic_accuracy", list(counts=x, sensitivity=sens, specificity=spec,
    ppv=ppv, npv=npv, lr_positive=lr_pos, lr_negative=lr_neg, diagnostic_odds_ratio=dor,
    false_positive_rate=fpr, false_negative_rate=fnr, accuracy=accuracy,
    balanced_accuracy=balanced_accuracy, f1=f1, prevalence=(tp+fn)/sum(x),
    intervals=list(sensitivity=wilson(tp,tp+fn), specificity=wilson(tn,tn+fp),
      ppv=wilson(tp,tp+fp), npv=wilson(tn,tn+fn),
      sensitivity_wald=wald(tp,tp+fn), specificity_wald=wald(tn,tn+fp),
      ppv_wald=wald(tp,tp+fp), npv_wald=wald(tn,tn+fn),
      lr_positive=log_ci(lr_pos,lr_pos_var), lr_negative=log_ci(lr_neg,lr_neg_var),
      diagnostic_odds_ratio=log_ci(dor,dor_var)), alpha=alpha),
    list(tp=tp,fp=fp,fn=fn,tn=tn,alpha=alpha))
}

epi_mcnemar <- function(a,b,c,d,alpha=0.05) {
  x <- .validate_counts(c(a,b,c,d)); if(length(alpha)!=1L || !is.numeric(alpha) || !is.finite(alpha) || alpha<=0 || alpha>=1) stop("alpha must be finite and in (0,1)")
  tab <- matrix(c(a,b,c,d), nrow=2, byrow=TRUE)
  asym <- suppressWarnings(stats::mcnemar.test(tab, correct=TRUE))
  discordant <- b+c
  exact <- if(discordant>0) stats::binom.test(b, discordant, p=.5, alternative="two.sided", conf.level=1-alpha) else NULL
  .new_result("paired_mcnemar", list(statistic=unname(asym$statistic), p_value=unname(asym$p.value),
    exact_p_value=if(is.null(exact)) 1 else exact$p.value, discordant_pairs=discordant,
    matched_odds_ratio=if(c>0) b/c else if(b>0) Inf else NA_real_), list(counts=x,alpha=alpha))
}

epi_dca <- function(predicted_probabilities, outcomes, threshold_probabilities=seq(.01,.99,.01)) {
  if(!is.numeric(predicted_probabilities)||!is.numeric(outcomes)||!is.numeric(threshold_probabilities))
    stop("probabilities, outcomes and thresholds must be numeric",call.=FALSE)
  p <- as.numeric(predicted_probabilities); y <- as.numeric(outcomes); t <- as.numeric(threshold_probabilities)
  if(length(p)!=length(y)||length(p)<1||any(!is.finite(p))||any(p<0|p>1)||anyNA(y)||any(!y%in%c(0,1))) stop("probabilities and binary outcomes must have equal valid lengths")
  if(length(t)<1L||any(!is.finite(t))||any(t<=0|t>=1)) stop("threshold probabilities must be a non-empty vector in (0,1)")
  prevalence <- mean(y)
  rows <- lapply(t,function(th) { pred<-p>=th; tp<-sum(pred&y==1); fp<-sum(pred&y==0); w<-th/(1-th)
    c(threshold=th, model_net_benefit=tp/length(y)-fp/length(y)*w,
      treat_all_net_benefit=prevalence-(1-prevalence)*w,treat_none_net_benefit=0) })
  .new_result("decision_curve", list(points=do.call(rbind,rows)), list(predicted_probabilities=p,outcomes=y,threshold_probabilities=t))
}

epi_roc_compare <- function(scores1,scores2,outcomes,paired=TRUE,alpha=.05,outcomes2=NULL) {
  auc_parts <- function(scores,y) {
    pos<-scores[y==1]; neg<-scores[y==0]
    if(!length(pos)||!length(neg)) stop("both outcome classes are required")
    v10<-vapply(pos,function(p) mean(ifelse(p>neg,1,ifelse(p==neg,.5,0))),numeric(1))
    v01<-vapply(neg,function(n) mean(ifelse(pos>n,1,ifelse(pos==n,.5,0))),numeric(1))
    v10var<-if(length(v10)>1)var(v10)/length(v10) else 0
    v01var<-if(length(v01)>1)var(v01)/length(v01) else 0
    list(auc=mean(v10),var=v10var+v01var,v10=v10,v01=v01)
  }
  if (length(paired)!=1L || !is.logical(paired) || is.na(paired)) stop("paired must be TRUE or FALSE")
  if (length(alpha)!=1L || !is.numeric(alpha) || !is.finite(alpha) || alpha<=0 || alpha>=1 || 1-alpha/2>=1) stop("alpha must be finite and in (0,1)")
  if (!is.numeric(scores1) || !is.numeric(scores2) || any(!is.finite(scores1)) || any(!is.finite(scores2)))
    stop("scores must be finite numeric vectors")
  if (!is.numeric(outcomes) || anyNA(outcomes) || any(!outcomes%in%c(0,1)))
    stop("outcomes must be a complete binary 0/1 vector")
  y1 <- as.numeric(outcomes)
  if (paired) {
    if (length(scores1)!=length(y1) || length(scores2)!=length(y1)) stop("paired scores and outcomes must have equal lengths")
    if (!is.null(outcomes2) && (!is.numeric(outcomes2) || anyNA(outcomes2) || !identical(as.numeric(outcomes2),y1))) stop("paired comparison outcomes must match subject-for-subject")
    y2 <- y1
  } else {
    if (is.null(outcomes2) || !is.numeric(outcomes2) || anyNA(outcomes2) || any(!outcomes2%in%c(0,1)) || length(scores2)!=length(outcomes2))
      stop("independent comparison requires a matching binary outcomes2 vector")
    if (length(scores1)!=length(y1)) stop("scores1 and outcomes must have equal lengths")
    y2 <- as.numeric(outcomes2)
  }
  one<-auc_parts(scores1,y1); two<-auc_parts(scores2,y2); covar<-0
  if(paired) covar<-(if(length(one$v10)>1) cov(one$v10,two$v10)/length(one$v10) else 0)+
    (if(length(one$v01)>1) cov(one$v01,two$v01)/length(one$v01) else 0)
  se<-sqrt(max(0,one$var+two$var-2*covar)); delta<-one$auc-two$auc
  z<-if(se>0) delta/se else if(delta==0) 0 else sign(delta)*Inf
  .new_result("delong_comparison",list(auc1=one$auc,auc2=two$auc,delta_auc=delta,standard_error=se,
    delta_auc_ci=delta+c(-1,1)*qnorm(1-alpha/2)*se,z_statistic=z,
    p_value=if(se>0) 2*pnorm(-abs(z)) else if(delta==0) 1 else 0,
    covariance=covar,paired=paired),
    list(scores1=scores1,scores2=scores2,outcomes=y1,outcomes2=y2,paired=paired,alpha=alpha))
}
