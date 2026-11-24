"""Reproducible synthetic data generator. Candidates may use this for mechanics,
not to inspect future sample paths in their decisions."""
from pathlib import Path
from random import Random
import csv,json,math,argparse

UNDERLYINGS={'BTC':65000.,'ETH':3400.,'SOL':165.,'AVAX':40.}

def emit(path,fields,rows):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)

def generate(out,seed=20261124,days=180,accounts=120):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rng=Random(seed)
    inst=[]
    for sym in UNDERLYINGS:
        inst.append(dict(instrument_id=f'{sym}-PERP',underlying=sym,kind='PERP',strike=0,expiry_day=0,multiplier=1,tick_size=.01))
        for expiry in [60,120,210,300]:
            for m in [.7,.85,1,1.15,1.3]:
                for kind in ('CALL','PUT'):
                    inst.append(dict(instrument_id=f'{sym}-{expiry}-{int(m*100)}-{kind}',underlying=sym,kind=kind,
                                     strike=round(UNDERLYINGS[sym]*m,2),expiry_day=expiry,multiplier=1,tick_size=.01))
    emit(out/'instruments.csv',list(inst[0]),inst)
    index=[];marks=[];price=dict(UNDERLYINGS)
    from math import erf,exp,log,sqrt
    def n(x):return .5*(1+erf(x/sqrt(2)))
    def bs(s,k,t,v,c):
        if t<=0:return max((s-k if c else k-s),0)
        d1=(log(s/k)+v*v*t/2)/(v*sqrt(t));d2=d1-v*sqrt(t)
        return max(0,s*n(d1)-k*n(d2)) if c else max(0,k*n(-d2)-s*n(-d1))
    for day in range(days):
        market=rng.gauss(0,.015)
        if day in [38,39,88,89,140,141]:market += {38:-.11,39:-.07,88:.14,89:.08,140:-.13,141:.06}[day]
        if day in [110,111,112]: market*=2
        for sym in UNDERLYINGS:
            vol={'BTC':.038,'ETH':.051,'SOL':.075,'AVAX':.09}[sym]
            price[sym]*=max(.5,1+market*.7+rng.gauss(0,vol))
            index.append(dict(day=day,underlying=sym,index_price=f'{price[sym]:.8f}',source='consolidated'))
        for row in inst:
            sym=row['underlying'];s=price[sym]
            base_vol={'BTC':.58,'ETH':.68,'SOL':.85,'AVAX':.98}[sym]
            smile=abs(math.log(s/max(1,float(row['strike']))))*.20 if row['strike'] else 0
            iv=max(.15,base_vol+smile+.12*math.sin(day/19)+rng.gauss(0,.018))
            if row['kind']=='PERP':mid=s*(1+rng.gauss(0,.00025))
            else:mid=bs(s,float(row['strike']),max(0,(row['expiry_day']-day)/365),iv,row['kind']=='CALL')
            width=max(.01,mid*(.0015+.006*rng.random()))
            stale=int(rng.random()<(.045 if day in (38,88,140) else .005))
            marks.append(dict(day=day,instrument_id=row['instrument_id'],mid=f'{mid:.8f}',
                              bid=f'{max(0,mid-width/2):.8f}',ask=f'{mid+width/2:.8f}',
                              iv=f'{iv:.6f}',stale=stale,source=rng.choice(['BINANCE','OKX','KRAKEN','HYPERLIQUID'])))
    emit(out/'index.csv',list(index[0]),index)
    emit(out/'marks.csv',list(marks[0]),marks)
    mark_lookup={(m['day'],m['instrument_id']):m for m in marks}
    events=[]; seq=0
    account_names=[f'ACC{i:04d}' for i in range(accounts)]
    for name in account_names:
        seq+=1;events.append(dict(event_id=f'EV{seq:08d}',day=0,account_id=name,
                               operation='deposit',instrument_id='',quantity='',price='',amount=str(rng.randint(25000,300000)),fee='0',rate='0'))
    options=[i['instrument_id'] for i in inst if i['kind']!='PERP']
    for day in range(days):
        for _ in range(24):
            name=rng.choice(account_names)
            iid=rng.choice(options) if rng.random()<.52 else rng.choice([f'{sym}-PERP' for sym in UNDERLYINGS])
            kind=next(i['kind'] for i in inst if i['instrument_id']==iid)
            sym=iid.split('-')[0]
            matching=mark_lookup[(day,iid)]
            mid=float(matching['mid'])
            if mid<.1:continue
            qty=rng.choice([-1,1])*round(rng.uniform(.03,.7) if kind=='PERP' else rng.uniform(.5,8),3)
            px=max(.01,mid*(1+rng.gauss(0,.0005)))
            fee=round(abs(qty)*px*.0005,6)
            seq+=1;events.append(dict(event_id=f'EV{seq:08d}',day=day,account_id=name,
                                   operation='fill',instrument_id=iid,quantity=qty,price=f'{px:.6f}',amount='',fee=fee,rate='0'))
        if day%7==0:
            for _ in range(24):
                name=rng.choice(account_names);sym=rng.choice(list(UNDERLYINGS))
                seq+=1;events.append(dict(event_id=f'EV{seq:08d}',day=day,account_id=name,
                                       operation='funding',instrument_id=f'{sym}-PERP',quantity='',
                                       price=f'{price[sym]:.6f}',amount='',fee='0',rate=f'{rng.gauss(.00008,.00014):.8f}'))
    events.sort(key=lambda e:(int(e['day']),int(e['event_id'][2:])))
    emit(out/'events.csv',list(events[0]),events)
    meta={'seed':seed,'days':days,'accounts':accounts,'instruments':len(inst),'index_rows':len(index),
          'mark_rows':len(marks),'event_rows':len(events),'simulation_only':True,
          'splits':{'train':[0,89],'validation':[90,134],'test':[135,179]}}
    (out/'manifest.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps(meta,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default='data');p.add_argument('--seed',type=int,default=20261124)
    a=p.parse_args();generate(a.out,a.seed)
