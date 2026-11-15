import calendar

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

CUT = 1000
TRAIN_END = "2023-12-31"

st.set_page_config(page_title="Burning Activity Calendar: Bangladesh", layout="wide")


@st.cache_data
def load():
    m = pd.read_csv("data/processed/monthly_counts.csv", parse_dates=["month"])
    w = m.pivot(index="month", columns="sensor", values="hotspots").sort_index()
    w.columns = [c.lower() for c in w.columns]

    # Two conversion ratios (VIIRS -> MODIS scale), fitted on 2020-2023 overlap
    both = w.dropna(subset=["modis", "viirs"])
    train = both[both.index <= TRAIN_END]
    hi, lo = train[train.viirs >= CUT], train[train.viirs < CUT]
    r_hi = hi.modis.sum() / hi.viirs.sum()
    r_lo = lo.modis.sum() / lo.viirs.sum()

    w["viirs_converted"] = w.viirs * np.where(w.viirs >= CUT, r_hi, r_lo)
    w["harmonized"] = w.modis.fillna(w.viirs_converted)
    w["source"] = np.where(w.modis.notna(), "MODIS observed", "VIIRS converted")
    w["year"] = w.index.year
    w["month_num"] = w.index.month
    return w.reset_index(), r_hi, r_lo


df, r_hi, r_lo = load()
years = sorted(df.year.unique())

st.title("Burning Activity Calendar: Bangladesh")
st.caption("Monthly active-fire hotspots from NASA FIRMS, MODIS and VIIRS S-NPP on one scale.")

series_label = st.sidebar.radio(
    "Series", ["Harmonized (MODIS scale)", "VIIRS converted to MODIS scale"]
)
col = "harmonized" if series_label.startswith("Harmonized") else "viirs_converted"
yr_range = st.sidebar.slider("Years", min(years), max(years), (min(years), max(years)))
sub = df[df.year.between(*yr_range)]

# --- Calendar heatmap ---
pivot = sub.pivot(index="year", columns="month_num", values=col)
pivot.columns = [calendar.month_abbr[i] for i in pivot.columns]
fig = px.imshow(
    pivot.round(0),
    color_continuous_scale="Viridis",
    aspect="auto",
    text_auto=True,
    labels=dict(x="Month", y="Year", color="Hotspots"),
)
fig.update_yaxes(type="category")
st.plotly_chart(fig, use_container_width=True)

# --- Month vs history ---
st.subheader("Compare a month with its history")
c1, c2 = st.columns(2)
sel_year = c1.selectbox("Year", years, index=len(years) - 1)
sel_month = c2.selectbox(
    "Month", list(range(1, 13)), format_func=lambda i: calendar.month_name[i]
)
cur = df[(df.year == sel_year) & (df.month_num == sel_month)][col]
hist = df[(df.year != sel_year) & (df.month_num == sel_month)][col].dropna()

if cur.empty or pd.isna(cur.iloc[0]) or hist.empty:
    st.info("Not enough data for that month with this series.")
else:
    value, median = cur.iloc[0], hist.median()
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{calendar.month_name[sel_month]} {sel_year}", f"{value:,.0f}")
    m2.metric("Median of other years", f"{median:,.0f}")
    if median > 0:
        m3.metric("Compared with median", f"{(value / median - 1):+.0%}")

# --- Download ---
out = sub[["month", "modis", "viirs", "viirs_converted", "harmonized", "source"]]
st.download_button(
    "Download CSV", out.to_csv(index=False), "burning_calendar_bangladesh.csv", "text/csv"
)

with st.expander("Method and limitations"):
    st.write(
        f"VIIRS counts are converted to MODIS scale with two ratios fitted on 2020-2023: "
        f"{r_hi:.3f} for months with 1,000+ VIIRS detections and {r_lo:.3f} for other months. "
        "Validated on 2024, which was held out. Wherever MODIS was observed, the harmonized "
        "series uses the observed MODIS count. The conversion only fills months where MODIS is "
        "missing. Limits: one country, one held-out year, a cutoff chosen by eye, and no "
        "S-NPP file for 2025."
    )
