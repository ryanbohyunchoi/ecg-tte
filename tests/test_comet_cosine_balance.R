source('scripts/comet_exploratory_psm.R')
set.seed(481)
root<-tempfile();dir.create(root);on.exit<-NULL
n<-300;keys<-sprintf('synthetic_%03d',1:n)
d<-data.frame(treatment_arm=rep(c('carvedilol_candidate','metoprolol_tartrate_candidate'),each=n/2),age_at_index=rnorm(n,65,10),recorded_sex=rep(c('Female','Male'),n/2),lvef=runif(n,15,65))
spec<-list(m=1,columns=names(d),numeric=c('age_at_index','lvef'),binary=character())
jsonlite::write_json(spec,file.path(root,'model_spec.json'))
jsonlite::write_json(keys,file.path(root,'restricted_row_keys.json'))
mask<-list(age_at_index=rep(FALSE,n),recorded_sex=rep(FALSE,n),lvef=seq_len(n)%%3==0)
jsonlite::write_json(mask,file.path(root,'restricted_missingness_mask.json'))
saveRDS(list(mean=array(rnorm(100),dim=c(1,50,2),dimnames=list('lvef',NULL,NULL))),file.path(root,'chain_traces.rds'))
write.csv(d,file.path(root,'restricted_completed_01.csv'),row.names=FALSE)
pairfile<-file.path(root,'pairs.csv');write.csv(data.frame(carvedilol_key=keys[1:100],metoprolol_key=keys[151:250]),pairfile,row.names=FALSE)
for(method in c('original','refined','cosine')) {
 out<-file.path(root,method);dir.create(out)
 main(root,out,method=='refined',if(method=='cosine') pairfile else NULL)
 tab<-read.csv(file.path(out,'balance_by_imputation.csv'))
 if(method=='cosine') {
  s<-fixed_smd(d$lvef[1:150],d$lvef[151:300],d$lvef[1:100],d$lvef[151:250])
  stopifnot(abs(tab$smd_post[tab$feature=='lvef']-s['post'])<1e-12)
  stopifnot(nrow(read.csv(file.path(out,'restricted_pairs_01.csv')))==100)
  observed<-read.csv(file.path(out,'observed_balance_by_imputation.csv'))
  stopifnot(observed$post_observed_carvedilol[observed$feature=='lvef']==67)
 }
}
unlink(root,recursive=TRUE)
cat('Synthetic original/refined/external-pair and observed-balance integration passed\n')
