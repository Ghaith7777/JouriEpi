epi_clean_linelist <- function(df, date_cols=character(), categorical_cols=character(), id_col=NULL) {
  if(!is.data.frame(df)||!nrow(df)) stop("df must be a non-empty data.frame")
  if(anyDuplicated(names(df))) stop("column names must be unique")
  requested<-unique(c(date_cols,categorical_cols,id_col)); requested<-requested[!is.na(requested)]
  missing<-setdiff(requested,names(df)); if(length(missing)) stop(paste("columns not found:",paste(missing,collapse=", ")))
  if(length(intersect(date_cols,categorical_cols))) stop("date and categorical columns must be disjoint")
  out<-df; invalid<-list()
  for(nm in date_cols) { raw<-out[[nm]]; parsed<-suppressWarnings(as.POSIXct(raw,tz="UTC",tryFormats=c("%Y-%m-%dT%H:%M:%OS%z","%Y-%m-%d %H:%M:%S","%Y-%m-%d"))); invalid[[nm]]<-sum(!is.na(raw)&is.na(parsed)); out[[nm]]<-parsed }
  for(nm in categorical_cols) if(is.character(out[[nm]])) { out[[nm]]<-trimws(out[[nm]]); out[[nm]][out[[nm]]==""]<-NA_character_ }
  received<-nrow(out); duplicate_rows<-duplicated(out); out<-out[!duplicate_rows,,drop=FALSE]
  duplicate_ids<-character(); duplicate_id_rows<-0L
  if(!is.null(id_col)) { ids<-out[[id_col]]; dup<-!is.na(ids)&(duplicated(ids)|duplicated(ids,fromLast=TRUE)); duplicate_id_rows<-sum(dup); duplicate_ids<-unique(as.character(ids[dup])) }
  outliers<-list()
  for(nm in names(out)[vapply(out,is.numeric,logical(1))]) { x<-out[[nm]]; if(all(is.na(x))) next; q<-quantile(x, c(.25,.75),na.rm=TRUE,names=FALSE); spread<-q[2]-q[1]; if(is.finite(spread)&&spread>0) { ix<-which(!is.na(x)&(x<q[1]-1.5*spread|x>q[2]+1.5*spread)); if(length(ix)) outliers[[nm]]<-data.frame(row=ix,value=x[ix]) } }
  summary<-structure(list(rows_received=received,rows_returned=nrow(out),exact_duplicate_rows_removed=sum(duplicate_rows),
    duplicate_id_rows=duplicate_id_rows,duplicate_ids=duplicate_ids,invalid_dates=invalid,
    numeric_outliers=outliers,missing_values=colSums(is.na(out))),class="jouriepi_data_health")
  list(data=out,health=summary)
}

epi_curve <- function(df,date_col,interval=c("day","iso_week")) {
  interval<-match.arg(interval)
  if(!is.data.frame(df) || !nrow(df)) stop("df must be a non-empty data.frame", call.=FALSE)
  if(length(date_col)!=1L || !is.character(date_col) || is.na(date_col) || !nzchar(date_col)) stop("date_col must be one non-empty column name", call.=FALSE)
  if(!date_col%in%names(df)) stop("date_col not found")
  dates<-as.Date(df[[date_col]]); if(anyNA(dates)) stop("date column contains invalid values")
  daily<-table(factor(dates,levels=seq(min(dates),max(dates),by="day")))
  days<-seq(min(dates),max(dates),by="day"); frame<-data.frame(date=days,cases=as.integer(daily))
  if(interval=="day") return(frame)
  frame$iso_week<-strftime(frame$date,"%G-W%V"); aggregate(cases~iso_week,frame,sum)
}

epi_rt <- function(df,date_col,window=7,mean_si=4.7,std_si=2.9,prior_shape=1,prior_rate=.2,credible_level=.95) {
  curve<-epi_curve(df,date_col,"day"); n<-nrow(curve)
  if(length(window)!=1L||!is.numeric(window)||!is.finite(window)||window<1||window!=as.integer(window)||n<window) stop("window must be a positive integer not exceeding the observed date range")
  pars<-c(mean_si,std_si,prior_shape,prior_rate,credible_level)
  if(!is.numeric(pars)||any(!is.finite(pars))||any(pars[1:4]<=0)||credible_level<=0||credible_level>=1) stop("invalid serial interval, prior, or credible level")
  shape<-(mean_si/std_si)^2; scale<-std_si^2/mean_si
  max_lag<-max(1L,ceiling(mean_si+6*std_si))
  w<-diff(pgamma(0:max_lag,shape=shape,scale=scale)); w<-w/sum(w)
  incidence<-curve$cases; lambda<-numeric(n)
  for(t in seq_len(n)) if(t>1) { lags<-seq_len(min(t-1,length(w))); lambda[t]<-sum(incidence[t-lags]*w[lags]) }
  alpha<-(1-credible_level)/2; rows<-lapply(seq.int(window,n),function(t) {
    ix<-seq.int(t-window+1,t); sh<-prior_shape+sum(incidence[ix]); rt<-prior_rate+sum(lambda[ix])
    data.frame(window_start=curve$date[min(ix)],date=curve$date[t],cases_in_window=sum(incidence[ix]),infectiousness=sum(lambda[ix]),
      rt_mean=sh/rt,rt_median=qgamma(.5,shape=sh,rate=rt),rt_lower=qgamma(alpha,shape=sh,rate=rt),
      rt_upper=qgamma(1-alpha,shape=sh,rate=rt),posterior_shape=sh,posterior_rate=rt) })
  .new_result("epi_rt", do.call(rbind,rows),
    list(window=window,mean_si=mean_si,std_si=std_si,prior_shape=prior_shape,
         prior_rate=prior_rate,serial_interval_weights=w,
         method="Cori et al. (2013) Poisson-Gamma sliding-window estimator"))
}
