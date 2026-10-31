import numpy as np, csv, json, itertools, os
from scipy.optimize import minimize
from scipy.stats import norm, gamma as G
from scipy.special import expit
def surv(f,p,t):
    t=np.maximum(np.asarray(t,float),1e-10)
    if f=='gompertz': return np.exp(-(p[1]/p[0])*(np.exp(p[0]*t)-1)) if p[0]!=0 else np.exp(-p[1]*t)
    if f=='weibull': return np.exp(-(t/p[0])**p[1])
    if f=='lognormal': return norm.sf((np.log(t)-p[0])/p[1])
    if f=='loglogistic': return 1/(1+(t/p[0])**p[1])
    if f=='exponential': return np.exp(-p[0]*t)
    if f=='mixture_cure_weibull': return p[0]+(1-p[0])*np.exp(-(t/p[1])**p[2])
    if f=='gengamma':
        mu,s,Q=p; w=(np.log(t)-mu)/s
        if abs(Q)<1e-6: return norm.sf(w)
        u=np.exp(Q*w)/Q**2
        return G.cdf(u,1/Q**2) if Q<0 else G.sf(u,1/Q**2)
tr={'gompertz':lambda x:(x[0],np.exp(x[1])),'weibull':lambda x:(np.exp(x[0]),np.exp(x[1])),'lognormal':lambda x:(x[0],np.exp(x[1])),
    'loglogistic':lambda x:(np.exp(x[0]),np.exp(x[1])),'exponential':lambda x:(np.exp(x[0]),),
    'mixture_cure_weibull':lambda x:(expit(x[0]),np.exp(x[1]),np.exp(x[2])),'gengamma':lambda x:(x[0],np.exp(x[1]),x[2])}
starts={'gompertz':[[a,np.log(b)] for a in (-0.3,-1,-3,-10) for b in (0.05,0.3,1,3)],
 'weibull':[[l,k] for l in (0,1,2,4,8,13) for k in (-2,-1.2,-0.7,-0.2)],
 'lognormal':[[m,s] for m in (0,1,3,6,10,16) for s in (0,0.7,1.5,2.3)],
 'loglogistic':[[l,k] for l in (0,1,2,4,8,13) for k in (-2,-1.2,-0.7,-0.2)],
 'exponential':[[-3],[-1],[0]],
 'mixture_cure_weibull':[[c,l,k] for c in (-1,0,1,2,3) for l in (-2,-1,0,1) for k in (-1,0,0.7)],
 'gengamma':[[m,s,q] for m in (-2,0,2,5) for s in (0,0.7,1.5,2.3) for q in (-15,-8,-4,-1.5,0.5,1.5)]}
def nll_fn(f,t,n,ev,cens,tc):
    def nll(x):
        p=tr[f](x)
        with np.errstate(all='ignore'):
            pr=surv(f,p,t[:-1])-surv(f,p,t[1:]); sc=surv(f,p,tc); se=surv(f,p,t[-1])
        m=ev>0
        if np.any(~np.isfinite(pr)) or np.any(pr[m]<=1e-300) or np.any(sc[cens>0]<=1e-300) or (n[-1]>0 and se<=1e-300): return 1e12
        return -(np.sum(ev[m]*np.log(pr[m]))+np.sum(cens[cens>0]*np.log(sc[cens>0]))+(n[-1]*np.log(se) if n[-1]>0 else 0))
    return nll
def fit_all(path):
    tb=np.array([[float(x) for x in r] for r in list(csv.reader(open(path)))[1:]])
    t,n,ca=tb.T; cens=np.diff(ca); ev=n[:-1]-n[1:]-cens; tc=t[:-1]+0.5; N=n[0]
    out={}
    for f in tr:
        nll=nll_fn(f,t,n,ev,cens,tc); best=None
        for s0 in starts[f]:
            r=minimize(nll,s0,method='Nelder-Mead',options=dict(xatol=1e-10,fatol=1e-12,maxiter=40000,maxfev=40000))
            if best is None or r.fun<best.fun: best=r
        r=minimize(nll,best.x,method='Nelder-Mead',options=dict(xatol=1e-12,fatol=1e-14,maxiter=40000))
        if r.fun<best.fun: best=r
        k=len(best.x); p=[float(v) for v in tr[f](best.x)]
        out[f]=dict(params=p,aic=2*k+2*best.fun,bic=k*np.log(N)+2*best.fun,ll=-best.fun,S4=float(surv(f,p,4.0)),S7=float(surv(f,p,7.0)),S20=float(surv(f,p,20.0)))
    return out
if __name__=='__main__':
    R={ck:fit_all(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','R','dados','reais',f'{ck}_tabela.csv')) for ck in ['dfs_c','os_c','dfs_i','os_i']}
    json.dump(R,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'mle.json'),'w'),indent=1)
