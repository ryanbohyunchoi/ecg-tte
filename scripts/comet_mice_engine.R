# Diagnostic pilot only. All files are private cluster artifacts.
args <- commandArgs(trailingOnly=TRUE)
main <- function(args) {
  if (!requireNamespace('mice', quietly=TRUE) || !requireNamespace('jsonlite', quietly=TRUE)) stop('missing_mice_or_jsonlite')
  input <- args[1]; out <- args[2]
  spec <- jsonlite::read_json(file.path(out,'model_spec.json'), simplifyVector=TRUE)
  d <- read.csv(input, na.strings='__MISSING__', check.names=FALSE, colClasses='character')
  if (!identical(names(d), spec$columns)) stop('model_columns_mismatch')
  for (f in spec$numeric) d[[f]] <- as.numeric(d[[f]])
  for (f in spec$binary) d[[f]] <- factor(d[[f]], levels=c('0','1'))
  d$recorded_sex <- factor(d$recorded_sex)
  d$treatment_arm <- factor(d$treatment_arm)
  method <- setNames(rep('',ncol(d)),names(d))
  for (f in names(d)[colSums(is.na(d))>0]) method[f] <- if(f %in% spec$binary) 'logreg' else 'pmm'
  pred <- matrix(1L,ncol(d),ncol(d),dimnames=list(names(d),names(d))); diag(pred)<-0L
  pred[method=='',] <- 0L
  # Constant complete variables remain in outputs but cannot predict another variable.
  constants <- names(d)[vapply(d,function(x) length(unique(x[!is.na(x)]))<2,logical(1))]
  pred[,constants] <- 0L
  warnings <- character()
  fit <- withCallingHandlers(mice::mice(d,m=spec$m,maxit=spec$iterations,seed=spec$seed,
         method=method,predictorMatrix=pred,donors=5,printFlag=FALSE),
         warning=function(w){warnings <<- c(warnings,conditionMessage(w));invokeRestart('muffleWarning')})
  saveRDS(fit,file.path(out,'restricted_mice.rds'))
  writeLines(capture.output(sessionInfo()),file.path(out,'session_info.txt'))
  writeLines(warnings,file.path(out,'restricted_warnings.txt'))
  jsonlite::write_json(list(requested_method=as.list(method),actual_method=as.list(fit$method),
    constant_predictors=constants,requested_predictors=pred,actual_predictors=fit$predictorMatrix,
    events=fit$loggedEvents),file.path(out,'restricted_model_diagnostics.json'),auto_unbox=TRUE,pretty=TRUE)
  for(i in seq_len(spec$m)) {
    completed <- mice::complete(fit,i)
    for(f in spec$numeric) completed[[f]] <- sprintf('%.17g',completed[[f]])
    write.csv(completed,file.path(out,sprintf('restricted_completed_%02d.csv',i)),row.names=FALSE,na='__MISSING__')
  }
  conv <- tryCatch(mice::convergence(fit, diagnostic="ac"),error=function(e) NULL)
  if(!is.null(conv)) write.csv(conv,file.path(out,'convergence.csv'),row.names=FALSE)
  saveRDS(list(mean=fit$chainMean,variance=fit$chainVar),file.path(out,'chain_traces.rds'))
  pdf(file.path(out,'chain_traces.pdf')); tryCatch(print(plot(fit)),error=function(e) plot.new()); dev.off()
  jsonlite::write_json(list(mice_version=as.character(packageVersion('mice')),r_version=R.version.string,
    warning_count=length(warnings),logged_event_count=if(is.null(fit$loggedEvents)) 0L else nrow(fit$loggedEvents),
    predictor_matrix_changed=!isTRUE(all.equal(pred,fit$predictorMatrix)),method_changed=!identical(method,fit$method),
    convergence_available=!is.null(conv)),file.path(out,'engine_summary.json'),auto_unbox=TRUE,pretty=TRUE)
}
tryCatch(main(args),error=function(e) {cat('MICE engine stopped: ', conditionMessage(e), '\n'); quit(status=1)})
