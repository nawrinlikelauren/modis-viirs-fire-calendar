import glob
import os
import pandas as pd

paths = sorted(glob.glob("data/raw/**/*.csv", recursive=True))
print("working folder:", os.getcwd())
print("csv files found:", paths)

for path in paths:
    df = pd.read_csv(path)
    print("\n==", path)
    print("rows:", len(df))
    print("columns:", list(df.columns))
    if "acq_date" in df:
        print("dates:", df["acq_date"].min(), "to", df["acq_date"].max())
    for col in ("satellite", "instrument", "confidence", "daynight", "type"):
        if col in df:
            print(col, df[col].value_counts().head(6).to_dict())
    print(df.head(3).to_string())
