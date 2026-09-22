source('scripts/comet_bp_imputation.R')
set.seed(42)
n <- 150
# Overlapping marginals deliberately allow invalid unconstrained draws.
d <- data.frame(sbp=runif(n,110,180),dbp=runif(n,60,109),z=rnorm(n),w=rnorm(n))
d$sbp[1:50] <- NA; d$dbp[30:80] <- NA
original <- d
method <- c(sbp='sbp_ordered',dbp='dbp_ordered',z='',w='')
fit <- mice::mice(d,m=2,maxit=3,method=method,printFlag=FALSE,seed=1)
for(i in 1:2) {
 c <- mice::complete(fit,i)
 stopifnot(all(c$sbp>c$dbp))
 for(f in c('sbp','dbp')) stopifnot(identical(c[[f]][!is.na(original[[f]])],original[[f]][!is.na(original[[f]])]))
}
# Lack of ordered donors must fail rather than clip or fabricate values.
bad <- d; bad$dbp[1:20] <- 1000
failed <- tryCatch({mice::mice(bad,m=1,maxit=1,method=method,printFlag=FALSE);FALSE},error=function(e) grepl('insufficient_ordered_bp_donors',conditionMessage(e)))
stopifnot(failed)
cat('Ordered BP preservation and donor failure tests passed\n')
