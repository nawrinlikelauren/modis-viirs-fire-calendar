import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

m = pd.read_csv("data/processed/monthly_counts.csv", parse_dates=["month"])
wide = (m.pivot(index="month", columns="sensor", values="hotspots")
          .dropna().sort_index().rename(columns={"MODIS": "modis", "VIIRS": "viirs"}))

TRAIN_END = "2023-12-31"
train = wide[wide.index <= TRAIN_END]

# Baseline: one constant VIIRS -> MODIS ratio
ratio = train.modis.sum() / train.viirs.sum()
wide["pred_ratio"] = wide.viirs * ratio

# Curve: log(MODIS+1) = a + b * log(VIIRS+1)
b, a = np.polyfit(np.log1p(train.viirs), np.log1p(train.modis), 1)
wide["pred_curve"] = np.expm1(a + b * np.log1p(wide.viirs)).clip(lower=0)

print(f"constant ratio (MODIS per VIIRS): {ratio:.3f}")
print(f"curve: log(MODIS+1) = {a:.3f} + {b:.3f} * log(VIIRS+1)")

test = wide[wide.index > TRAIN_END]
for name, df in [("train", wide[wide.index <= TRAIN_END]), ("held-out", test)]:
    print(f"\n{name} ({len(df)} months)")
    for col in ["pred_ratio", "pred_curve"]:
        mae = (df[col] - df.modis).abs().mean()
        tot = df[col].sum() / df.modis.sum() - 1
        print(f"  {col}: MAE = {mae:.1f} hotspots/month, total error = {tot:+.1%}")

wide.round(1).to_csv("data/processed/harmonized_monthly.csv")

ax = wide[["modis", "pred_ratio", "pred_curve"]].plot(figsize=(11, 4), logy=True)
ax.axvline(pd.Timestamp(TRAIN_END), color="gray", linestyle="--")
ax.set_ylabel("monthly hotspots (log scale)")
ax.set_title("Observed MODIS vs. predictions from VIIRS (dashed line = end of fitting period)")
plt.tight_layout()
plt.savefig("docs/validation.png", dpi=150)
print("\nsaved data/processed/harmonized_monthly.csv and docs/validation.png")
