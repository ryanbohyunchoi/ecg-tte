a<-commandArgs(trailingOnly=TRUE);root<-a[1]
destination<-root
if(length(a)>=2) {
 destination<-a[2]
 if(file.exists(destination))stop('New plot destination must not exist')
 if(!dir.create(destination,recursive=TRUE))stop('Cannot create plot destination')
}
contract_path<-file.path(root,'contract.json')
contract<-if(file.exists(contract_path))jsonlite::read_json(contract_path) else list()
is_bcl<-identical(contract$representation,'BCL_backbone_before_projection_256D')
embedding_label<-if(is_bcl)'ECG BCL cosine' else 'CLMBR cosine'

d<-read.csv(file.path(root,'comparison_balance.csv'))
methods<-c('original','refined','cosine');colors<-c('#0072B2','#009E73','#D55E00')
summary<-do.call(rbind,lapply(split(d,list(d$method,d$imputation)),function(x){
 if(!nrow(x))return(NULL)
 data.frame(method=x$method[1],imputation=x$imputation[1],mean_abs_smd=mean(abs(x$smd_post),na.rm=TRUE),max_abs_smd=max(abs(x$smd_post),na.rm=TRUE),features_ge_0_1=sum(abs(x$smd_post)>=.1,na.rm=TRUE),undefined=sum(is.na(x$smd_post)))
}))
write.csv(summary,file.path(destination,'comparison_metrics.csv'),row.names=FALSE)
pdf(file.path(destination,'comparison_love_plots.pdf'),width=10,height=13)
for(i in sort(unique(d$imputation))) {
 x<-d[d$imputation==i,];base<-x[x$method=='original',];ord<-order(abs(base$smd_pre),na.last=TRUE);features<-base$feature[ord]
 par(mar=c(4,15,4,1));plot(abs(base$smd_pre[ord]),seq_along(features),xlim=c(0,max(c(.1,abs(x$smd_pre),abs(x$smd_post)),na.rm=TRUE)),yaxt='n',ylab='',xlab='Absolute SMD; fixed common-population denominator',pch=1,main=paste(embedding_label,'— saved imputation',i,'— balance and retention must be reviewed together'))
 for(j in seq_along(methods)) {z<-x[x$method==methods[j],];points(abs(z$smd_post[match(features,z$feature)]),seq_along(features),pch=15+j,col=colors[j])}
 axis(2,at=seq_along(features),labels=features,las=2,cex.axis=.55);abline(v=.1,lty=2,col='gray50')
 legend('topright',c('Unadjusted','Original PSM','Previously refined PSM',embedding_label),pch=c(1,16,17,18),col=c('black',colors),cex=.7,bg='white')
}
dev.off()
