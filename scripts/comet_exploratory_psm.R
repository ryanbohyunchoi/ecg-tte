# Outcome-blind exploratory matching; effect estimation is deliberately absent.
args <- commandArgs(trailingOnly=TRUE)
fixed_smd <- function(a,b,am,bm,binary=FALSE) {
  denom <- if(binary) sqrt((mean(a)*(1-mean(a))+mean(b)*(1-mean(b)))/2) else sqrt((var(a)+var(b))/2)
  c(pre=if(denom>0) (mean(a)-mean(b))/denom else NA_real_,post=if(denom>0) (mean(am)-mean(bm))/denom else NA_real_)
}
main <- function(report,out,refined=FALSE) {
  if(!requireNamespace('jsonlite',quietly=TRUE)) stop('jsonlite_required')
  spec <- jsonlite::read_json(file.path(report,'model_spec.json'),simplifyVector=TRUE)
  keys <- jsonlite::read_json(file.path(report,'restricted_row_keys.json'),simplifyVector=TRUE)
  mask <- jsonlite::read_json(file.path(report,'restricted_missingness_mask.json'),simplifyVector=TRUE)
  traces <- readRDS(file.path(report,'chain_traces.rds'))
  trace_rows <- list()
  for(kind in names(traces)) {
    a <- traces[[kind]]
    for(f in dimnames(a)[[1]]) for(chain in seq_len(dim(a)[3])) {
      v <- a[f,,chain]; n <- length(v); h <- floor(n/2)
      early <- v[seq.int(max(1,h-9),h)]; late <- tail(v,10)
      if(all(is.finite(c(early,late)))) trace_rows[[length(trace_rows)+1L]] <- data.frame(feature=f,statistic=kind,chain=chain,
        midpoint10_mean=mean(early),last10_mean=mean(late),difference=mean(late)-mean(early))
    }
  }
  write.csv(do.call(rbind,trace_rows),file.path(out,'trace_drift_summary.csv'),row.names=FALSE)
  all_balance <- list(); summaries <- list()
  for(i in seq_len(spec$m)) {
    d <- read.csv(file.path(report,sprintf('restricted_completed_%02d.csv',i)),check.names=FALSE)
    d$recorded_sex <- factor(d$recorded_sex)
    for(f in c(spec$numeric,spec$binary)) d[[f]] <- as.numeric(d[[f]])
    z <- as.integer(d$treatment_arm=='carvedilol_candidate')
    predictors <- setdiff(spec$columns,'treatment_arm')
    # Dummy coding is explicit; complete constant variables retained in balance report.
    sex_levels <- levels(d$recorded_sex)
    x <- as.matrix(d[setdiff(predictors,'recorded_sex')])
    for(level in sex_levels) x <- cbind(x,as.integer(d$recorded_sex==level))
    colnames(x) <- c(setdiff(predictors,'recorded_sex'),paste0('recorded_sex=',sex_levels))
    eval <- x
    for(f in predictors) eval <- cbind(eval,as.integer(mask[[f]]))
    colnames(eval) <- c(colnames(x),paste0('missing:',predictors))
    aliases <- character()
    if(refined) {
      # Keep the common clinical/missingness evaluation set unchanged.
      x <- eval
      ef_basis <- splines::ns(d$lvef,knots=c(30,50),Boundary.knots=c(1,100))
      colnames(ef_basis) <- paste0('lvef_spline_',1:3)
      x <- cbind(x[,setdiff(colnames(x),'lvef'),drop=FALSE],ef_basis)
    }
    # Reference category removed only from fitting, not evaluation.
    fitcols <- setdiff(colnames(x),paste0('recorded_sex=',sex_levels[1]))
    constant <- fitcols[vapply(fitcols,function(f) sd(x[,f])==0,logical(1))]
    fitcols <- setdiff(fitcols,constant)
    design <- scale(x[,fitcols,drop=FALSE])
    if(refined) {
      q <- qr(cbind(intercept=1,design),tol=1e-10)
      if(q$rank<ncol(design)+1L) {
        dropped <- q$pivot[seq.int(q$rank+1L,ncol(design)+1L)]
        if(1L %in% dropped) stop('intercept_alias_unexpected')
        aliases <- colnames(design)[dropped-1L]
        design <- design[,setdiff(colnames(design),aliases),drop=FALSE]
      }
    }
    warnings <- character()
    fit <- withCallingHandlers(glm.fit(cbind(1,design),z,family=binomial()),warning=function(w){warnings<<-c(warnings,conditionMessage(w));invokeRestart('muffleWarning')})
    if(!fit$converged || any(!is.finite(fit$coefficients))) stop('ps_model_nonconvergence_or_rank_deficiency')
    logits <- fit$linear.predictors
    if(any(!is.finite(logits))) stop('nonfinite_ps')
    caliper <- .2*sqrt((var(logits[z==1])+var(logits[z==0]))/2)
    if(!is.finite(caliper)||caliper<=0) stop('degenerate_caliper')
    treated <- which(z==1); treated <- treated[order(-logits[treated],treated)]
    available <- which(z==0); pairs <- matrix(integer(),ncol=2)
    for(t in treated) {
      if(!length(available)) break
      distances <- abs(logits[available]-logits[t]); k <- which.min(distances)
      if(distances[k]<=caliper) {pairs<-rbind(pairs,c(t,available[k])); available<-available[-k]}
    }
    if(nrow(pairs)<2) stop('insufficient_matches')
    write.csv(data.frame(carvedilol_key=keys[pairs[,1]],metoprolol_key=keys[pairs[,2]]),file.path(out,sprintf('restricted_pairs_%02d.csv',i)),row.names=FALSE)
    write.csv(data.frame(patient_key=keys,propensity=sprintf("%.17g",fit$fitted.values),logit=sprintf("%.17g",logits)),file.path(out,sprintf('restricted_scores_%02d.csv',i)),row.names=FALSE)
    balance <- list()
    for(f in colnames(eval)) {
      a <- eval[z==1,f]; b <- eval[z==0,f]; am <- eval[pairs[,1],f]; bm <- eval[pairs[,2],f]
      binary <- all(eval[,f] %in% c(0,1))
      denom <- if(binary) sqrt((mean(a)*(1-mean(a))+mean(b)*(1-mean(b)))/2) else sqrt((var(a)+var(b))/2)
      smds <- fixed_smd(a,b,am,bm,binary)
      balance[[length(balance)+1L]] <- data.frame(imputation=i,feature=f,pre_carvedilol_mean=mean(a),pre_metoprolol_mean=mean(b),post_carvedilol_mean=mean(am),post_metoprolol_mean=mean(bm),
        smd_pre=unname(smds['pre']),smd_post=unname(smds['post']),
        zero_denominator=denom==0,variance_ratio_post=if(!binary&&var(bm)>0) var(am)/var(bm) else NA_real_,
        ecdf_distance_post=max(abs(ecdf(am)(sort(unique(c(am,bm))))-ecdf(bm)(sort(unique(c(am,bm)))))))
    }
    tab <- do.call(rbind,balance); all_balance[[i]] <- tab
    writeLines(warnings,file.path(out,sprintf('restricted_ps_warnings_%02d.txt',i)))
    pdf(file.path(out,sprintf('balance_%02d.pdf',i)),width=9,height=12)
    par(mar=c(4,15,2,1)); ord<-order(abs(tab$smd_pre),na.last=TRUE)
    plot(abs(tab$smd_pre[ord]),seq_len(nrow(tab)),yaxt='n',ylab='',xlab='Absolute SMD',pch=1,xlim=c(0,max(c(abs(tab$smd_pre),abs(tab$smd_post),.1),na.rm=TRUE)))
    points(abs(tab$smd_post[ord]),seq_len(nrow(tab)),pch=16,col='blue');axis(2,at=seq_len(nrow(tab)),labels=tab$feature[ord],las=2,cex.axis=.5);abline(v=.1,lty=2);dev.off()
    pdf(file.path(out,sprintf('propensity_overlap_%02d.pdf',i)))
    hist(fit$fitted.values[z==1],breaks=seq(0,1,length.out=21),col=rgb(1,0,0,.4),xlab='Propensity score',main='Pre-match overlap',xlim=c(0,1));hist(fit$fitted.values[z==0],breaks=seq(0,1,length.out=21),col=rgb(0,0,1,.4),add=TRUE);dev.off()
    summaries[[i]] <- list(imputation=i,pairs=nrow(pairs),carvedilol_retention=nrow(pairs)/sum(z==1),metoprolol_retention=nrow(pairs)/sum(z==0),caliper=caliper,
      max_abs_smd=max(abs(tab$smd_post),na.rm=TRUE),mean_abs_smd=mean(abs(tab$smd_post),na.rm=TRUE),features_ge_0_1=sum(abs(tab$smd_post)>=.1,na.rm=TRUE),undefined_smd=sum(is.na(tab$smd_post)),constant_predictors=constant,aliased_predictors=aliases,
      warning_count=length(warnings),ps_range_carvedilol=range(fit$fitted.values[z==1]),ps_range_metoprolol=range(fit$fitted.values[z==0]))
  }
  all <- do.call(rbind,all_balance);write.csv(all,file.path(out,'balance_by_imputation.csv'),row.names=FALSE)
  aggregate <- lapply(split(all,all$feature),function(d) data.frame(feature=d$feature[1],median_abs_smd=if(all(is.na(d$smd_post))) NA_real_ else median(abs(d$smd_post),na.rm=TRUE),worst_abs_smd=if(all(is.na(d$smd_post))) NA_real_ else max(abs(d$smd_post),na.rm=TRUE),imputations_ge_0_1=sum(abs(d$smd_post)>=.1,na.rm=TRUE),undefined=sum(is.na(d$smd_post))))
  write.csv(do.call(rbind,aggregate),file.path(out,'balance_across_imputations.csv'),row.names=FALSE)
  jsonlite::write_json(list(imputations=summaries,interpretation='Exploratory matching only. Trace review remains pending; no effects or convergence approval. Carvedilol is the treated/reference arm; matched subset targets may differ across imputations.'),file.path(out,'psm_summary.json'),auto_unbox=TRUE,pretty=TRUE,digits=NA)
}
if(sys.nframe()==0L) tryCatch(main(args[1],args[2],length(args)>=3L && args[3]=='refined'),error=function(e){cat(conditionMessage(e),'\n');quit(status=1)})
