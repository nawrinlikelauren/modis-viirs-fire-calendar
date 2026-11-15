import numpy as np
import pandas as pd

w = pd.read_csv("data/processed/harmonized_monthly.csv", parse_dates=["month"]).set_index("month")
TRAIN_END = "2023-12-31"
CUT = 1000  # VIIRS monthly count separating high from low activity

train = w[w.index <= TRAIN_END]
hi, lo = train[train.viirs >= CUT], train[train.viirs < CUT]
r_hi = hi.modis.sum() / hi.viirs.sum()
r_lo = lo.modis.sum() / lo.viirs.sum()
print(f"high-activity ratio: {r_hi:.3f}  (n={len(hi)} months)")
print(f"low-activity ratio:  {r_lo:.3f}  (n={len(lo)} months)")

w["pred_2regime"] = w.viirs * np.where(w.viirs >= CUT, r_hi, r_lo)
w.to_csv("data/processed/harmonized_monthly.csv")

for name, df in [("train", w[w.index <= TRAIN_END]), ("held-out", w[w.index > TRAIN_END])]:
    quiet = df[df.viirs < CUT]
    print(f"\n{name}")
    for col in ["pred_ratio", "pred_2regime"]:
        mae = (df[col] - df.modis).abs().mean()
        tot = df[col].sum() / df.modis.sum() - 1
        qmae = (quiet[col] - quiet.modis).abs().mean()
        print(f"  {col}: MAE = {mae:.1f}, total error = {tot:+.1%}, quiet-month MAE = {qmae:.1f}")
