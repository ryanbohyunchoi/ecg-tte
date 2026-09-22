# Versioned constrained PMM: retain normal PMM draws when ordered; otherwise
# refit PMM on eligible observed donors for that recipient. Never clip or swap.
bp_pmm <- function(y, ry, x, wy=NULL, counterpart, systolic, ...) {
  if(is.null(wy)) wy <- !ry
  if(!counterpart %in% colnames(x)) stop('bp_counterpart_predictor_unavailable')
  limits <- x[wy,counterpart]
  if(any(!is.finite(limits))) stop('bp_counterpart_nonfinite')
  draws <- mice::mice.impute.pmm(y,ry,x,wy=wy,...)
  bad <- if(systolic) draws<=limits else draws>=limits
  recipients <- which(wy)
  for(j in which(bad)) {
    eligible <- ry & if(systolic) y>limits[j] else y<limits[j]
    if(sum(eligible)<5L) stop('insufficient_ordered_bp_donors')
    one <- rep(FALSE,length(y)); one[recipients[j]] <- TRUE
    draws[j] <- mice::mice.impute.pmm(y,eligible,x,wy=one,...)
  }
  if(any(if(systolic) draws<=limits else draws>=limits)) stop('bp_constraint_failed')
  draws
}
mice.impute.sbp_ordered <- function(y,ry,x,wy=NULL,...) bp_pmm(y,ry,x,wy,'dbp',TRUE,...)
mice.impute.dbp_ordered <- function(y,ry,x,wy=NULL,...) bp_pmm(y,ry,x,wy,'sbp',FALSE,...)
