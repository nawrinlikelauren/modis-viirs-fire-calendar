import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()
url = URL.create(
    "mysql+pymysql",
    username=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD") or None,
    host=os.getenv("MYSQL_HOST", "localhost"),
    database=os.getenv("MYSQL_DATABASE", "fire_calendar"),
)
engine = create_engine(url)

clean = pd.read_csv("data/processed/hotspots_clean.csv", parse_dates=["date"])
monthly = pd.read_csv("data/processed/monthly_counts.csv", parse_dates=["month"])

clean.to_sql("hotspots_clean", engine, if_exists="replace", index=False, chunksize=5000)
monthly.to_sql("monthly_counts", engine, if_exists="replace", index=False)
print(f"loaded {len(clean):,} rows into hotspots_clean and {len(monthly):,} rows into monthly_counts")
