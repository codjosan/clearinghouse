"""Transparent reference pricing. Numerical greeks are intentional, not production quality."""
from math import exp, log, sqrt, erf, pi, isfinite

def normal_cdf(x): return 0.5*(1+erf(x/sqrt(2)))
def normal_pdf(x): return exp(-0.5*x*x)/sqrt(2*pi)

def bs_price(spot, strike, tau, vol, call=True, rate=0.0):
    spot=float(spot); strike=float(strike); tau=float(tau); vol=float(vol)
    if spot<=0 or strike<=0: raise ValueError('spot and strike must be >0')
    if vol<0 or tau<0: raise ValueError('vol and tau must be nonnegative')
    if tau == 0: return max(spot-strike,0) if call else max(strike-spot,0)
    if vol == 0:
        forward=spot*exp(rate*tau)
        return exp(-rate*tau)*max(forward-strike,0) if call else exp(-rate*tau)*max(strike-forward,0)
    s=vol*sqrt(tau)
    d1=(log(spot/strike)+(rate+0.5*vol*vol)*tau)/s
    d2=d1-s
    if call: return spot*normal_cdf(d1)-strike*exp(-rate*tau)*normal_cdf(d2)
    return strike*exp(-rate*tau)*normal_cdf(-d2)-spot*normal_cdf(-d1)

def bs_greeks(spot,strike,tau,vol,call=True,rate=0.0):
    spot=float(spot); strike=float(strike); tau=float(tau); vol=float(vol)
    if tau<=0 or vol<=0:
        intrinsic_delta=(1 if spot>strike else 0) if call else (-1 if spot<strike else 0)
        return {'delta':float(intrinsic_delta),'gamma':0.,'vega':0.,'theta':0.}
    d1=(log(spot/strike)+(rate+0.5*vol*vol)*tau)/(vol*sqrt(tau))
    d2=d1-vol*sqrt(tau)
    pdf=normal_pdf(d1)
    delta=normal_cdf(d1) if call else normal_cdf(d1)-1
    gamma=pdf/(spot*vol*sqrt(tau))
    vega=spot*pdf*sqrt(tau)
    if call: theta=-spot*pdf*vol/(2*sqrt(tau))-rate*strike*exp(-rate*tau)*normal_cdf(d2)
    else: theta=-spot*pdf*vol/(2*sqrt(tau))+rate*strike*exp(-rate*tau)*normal_cdf(-d2)
    return {'delta':delta,'gamma':gamma,'vega':vega,'theta':theta}

def implied_vol(option_price,spot,strike,tau,call=True):
    option_price=float(option_price); spot=float(spot); strike=float(strike)
    intrinsic=max(spot-strike,0) if call else max(strike-spot,0)
    if option_price < intrinsic-1e-6: raise ValueError('below intrinsic')
    if tau<=0: return 0.0
    lo,hi=1e-6,5.0
    if option_price>bs_price(spot,strike,tau,hi,call)+1e-6: raise ValueError('above volatility search range')
    for _ in range(90):
        mid=(lo+hi)/2
        if bs_price(spot,strike,tau,mid,call)<option_price: lo=mid
        else: hi=mid
    return (lo+hi)/2
