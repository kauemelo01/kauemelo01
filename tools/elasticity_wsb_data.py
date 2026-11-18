"""Compute the data behind the elasticity-wsb card from that repo's Parquet files.

Needs pandas + pyarrow. Usage: python tools/elasticity_wsb_data.py <elasticity-wsb>/Data tools/elasticity_wsb.json
Simplified from docs/methodology.md: Pearson-based Elasticity % vs. plain Spearman rho (no zero-deflation).
"""
import sys, json, math, numpy as np, pandas as pd
D = sys.argv[1]
lanes = pd.read_parquet(f"{D}/dim_lane.parquet", columns=["sk_lane", "lane_kma"])
L = pd.read_parquet(f"{D}/Loads (Main Set).parquet").merge(lanes, on="sk_lane", how="left")
Q = pd.read_parquet(f"{D}/Quotes.parquet").merge(lanes, on="sk_lane", how="left")
L["yw"] = L.year * 100 + L.week; Q["yw"] = Q.year * 100 + Q.week
k = ["lane_kma", "equip_type", "yw"]
ok = L[L.original_ecoh >= 300]
m = ok.groupby(k)[["markup_ecoh", "original_ecoh"]].sum()
m["mk"] = m.markup_ecoh / m.original_ecoh
# global fences over (week, KMA lane) points
p20, p80 = m.mk.quantile([.2, .8]); ipr = p80 - p20
lo, hi = p20 - 1.25 * ipr, p80 + 1.75 * ipr
m.loc[(m.mk < lo) | (m.mk > hi), "mk"] = np.nan
loads = L.groupby(k).loads.sum(); quotes = Q.groupby(k).quotes.sum()
w = pd.concat([m.mk, loads, quotes], axis=1)
w["cv"] = (w.loads / w.quotes).clip(upper=1)
nweeks = L.yw.nunique(); thr = round(nweeks / 10)
rows = []
for (lane, eq), g in w.groupby(level=[0, 1]):
    both = g.dropna(subset=["mk", "cv"])
    if len(both) < thr or both.mk.std() == 0 or both.cv.std() == 0: continue
    r = np.corrcoef(both.mk, both.cv)[0, 1]
    rho = both.mk.rank().corr(both.cv.rank())
    rows.append(dict(lane=lane, eq=eq, C=len(both), N=int(g.loads.notna().sum()), loads=int(g.loads.sum()),
                     el=math.tanh(r / 2), rho=rho, pts=both[["mk", "cv"]].round(4).values.tolist()))
df = pd.DataFrame(rows)
nc = -df.el.median()
def cl(a, b):
    if abs(a) < nc and abs(b) < nc: return 3
    if a < 0 and b < 0: return 1
    if a > 0 and b > 0: return 5
    return 2 if a < 0 else 4
df["cl"] = [cl(a, b) for a, b in zip(df.el, df.rho)]
print("weeks", nweeks, "thr", thr, "fences", round(lo, 3), round(hi, 3), "NC", round(nc, 4), "lanes", len(df))
print(df.cl.value_counts().sort_index().to_dict())
ex = df[df.cl == 1].sort_values(["C", "el"], ascending=[False, True]).head(8)
print(ex[["lane", "eq", "C", "loads", "el", "rho"]])
pick = df[(df.cl == 1) & (df.C >= 60) & df.lane.str.match(r"^\w+ -> \w+$")].sort_values("el").iloc[0]
json.dump(dict(nc=nc, counts={int(a): int(b) for a, b in df.cl.value_counts().items()},
               dots=df[["el", "rho", "cl", "loads"]].round(4).values.tolist(),
               pick=dict(lane=pick.lane, eq=pick["eq"], el=pick.el, rho=pick.rho, C=int(pick.C), pts=pick.pts)),
          open(sys.argv[2], "w"))
print("pick", pick.lane, pick["eq"], round(pick.el, 3), round(pick.rho, 3), pick.C)
