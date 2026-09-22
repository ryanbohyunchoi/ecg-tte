source('scripts/comet_exploratory_psm.R')
a<-c(0,2,4);b<-c(1,3,5);am<-c(0,2);bm<-c(1,3)
s<-fixed_smd(a,b,am,bm)
stopifnot(abs(s['pre']+.5)<1e-12,abs(s['post']+.5)<1e-12)
# Zero denominator must be explicit undefined, not zero balance.
stopifnot(all(is.na(fixed_smd(rep(1,3),rep(1,3),1,1,TRUE))))
binary<-fixed_smd(c(0,0,1,1),c(0,0,0,1),c(0,1),c(0,1),TRUE)
stopifnot(binary['post']==0,binary['pre']>0)
cat('Fixed denominator and binary balance tests passed\n')
