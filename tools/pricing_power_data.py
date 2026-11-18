"""Compute the data behind the Pricing-Power card from that repo's Parquet files.

Needs pandas + pyarrow. Usage: python tools/pricing_power_data.py <Pricing-Power>/Data tools/pricing_power.json
Follows docs/methodology.md: company-wide KPI (Account + Enterprise sales), KMA-lane quadrants with a 0.2% dead-band,
Upgrade loads split by row-level sourcing spread, months under $1M bookings dropped.
"""
import sys, json, pandas as pd
D = sys.argv[1]
M = pd.read_parquet(f"{D}/Main.parquet").merge(pd.read_parquet(f"{D}/Shippers.parquet")[["sk_shipper", "sales_team"]], on="sk_shipper", how="left")
M = M[M.sales_team.isin(["Account Sales", "Enterprise Sales"])]
M = M.merge(pd.read_parquet(f"{D}/List.parquet")[["lane_kma", "equip_type"]].drop_duplicates(), on=["lane_kma", "equip_type"])
M["p"] = M.year * 12 + M.month - 1
per = M.groupby("p").bookings.sum()
keep = set(per[per >= 1e6].index)
g = M.groupby(["lane_kma", "p"])[["bookings", "mileage"]].sum()
g["rpm"] = g.bookings / g.mileage
prev = g.copy(); prev.index = prev.index.set_levels(prev.index.levels[1] + 1, level=1)
j = g.join(prev.add_suffix("_p"), how="inner")
dp = j.rpm / j.rpm_p - 1; dv = j.mileage / j.mileage_p - 1
dp[dp.abs() < .002] = 0; dv[dv.abs() < .002] = 0
# DAX: IF(DPm > 0, IF(DVm > 0, "1", "2"), IF(DVm < 0, "3", "4"))
q = pd.Series("4", index=j.index)
q[(dp > 0) & (dv > 0)] = "1"; q[(dp > 0) & (dv <= 0)] = "2"; q[(dp <= 0) & (dv < 0)] = "3"
rows = M.merge(q.rename("q").reset_index(), on=["lane_kma", "p"])
rows.loc[(rows.q == "1") & (rows.ss_base > 0), "q"] = "1a"; rows.loc[rows.q == "1", "q"] = "1b"
W = {"1a": 2, "1b": 1.5, "2": 1, "4": 1, "3": -1}
k = rows.groupby(["p", "q"]).loads.sum().unstack(fill_value=0)
kpi = (sum(k[c] * w for c, w in W.items() if c in k) / k.sum(axis=1))
kpi = kpi[kpi.index.isin(keep)]
share = k[k.index.isin(keep)].sum(); share = (share / share.sum()).round(4)
lab = lambda p: f"{p // 12}-{p % 12 + 1:02d}"
out = dict(months=[lab(p) for p in kpi.index], kpi=kpi.round(4).tolist(), share=share.to_dict(),
           lanes=int(rows.lane_kma.nunique()), loads=int(rows[rows.p.isin(keep)].loads.sum()))
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(out["months"][0], "->", out["months"][-1], len(out["months"]), "months; lanes", out["lanes"], "loads", out["loads"])
print("kpi", [f"{v:.0%}" for v in out["kpi"]]); print("share", out["share"])
