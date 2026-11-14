import glob
import os
import pandas as pd

RAW = "data/raw"
OUT = "data/processed"
os.makedirs(OUT, exist_ok=True)

frames = []
for path in sorted(glob.glob(f"{RAW}/**/*.csv", recursive=True)):
    df = pd.read_csv(path)
    n_raw = len(df)
    df["sensor"] = df["instrument"].str.upper()

    # Drop low-confidence detections (scales differ by sensor)
    is_modis = df["sensor"] == "MODIS"
    modis_ok = pd.to_numeric(df["confidence"], errors="coerce") >= 30
    viirs_ok = df["confidence"].astype(str).str.lower().str[0].isin(["n", "h"])
    ok = (is_modis & modis_ok) | (~is_modis & viirs_ok)

    # Keep presumed vegetation fires only
    df = df[ok & (df["type"] == 0)].copy()
    df["date"] = pd.to_datetime(df["acq_date"])
    df = df.rename(columns={"satellite": "platform"})
    df = df[["date", "sensor", "platform", "latitude", "longitude", "frp", "daynight"]]
    print(f"{os.path.basename(path)}: {n_raw} raw -> {len(df)} kept")
    frames.append(df)

clean = pd.concat(frames, ignore_index=True)
clean.to_csv(f"{OUT}/hotspots_clean.csv", index=False)

clean["month"] = clean["date"].dt.to_period("M").dt.to_timestamp()
monthly = (
    clean.groupby(["month", "sensor"])
    .agg(hotspots=("frp", "size"), total_frp=("frp", "sum"))
    .reset_index()
)
monthly.to_csv(f"{OUT}/monthly_counts.csv", index=False)

wide = monthly.pivot(index="month", columns="sensor", values="hotspots")
if {"MODIS", "VIIRS"} <= set(wide.columns):
    wide["viirs_per_modis"] = wide["VIIRS"] / wide["MODIS"]
print("\nMonthly hotspot counts:")
print(wide.round(2).to_string())
