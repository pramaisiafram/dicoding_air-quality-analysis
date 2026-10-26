from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

sns.set_theme(style="whitegrid")

SEASON_ORDER = ["Spring", "Summer", "Autumn", "Winter"]
AQI_LABELS = ["Baik", "Sedang", "Tidak Sehat (Sensitif)", "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]
AQI_COLORS = ["#2ca02c", "#bcbd22", "#ff7f0e", "#d62728", "#9467bd", "#7f0000"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


@st.cache_data
def load_data():
    df = pd.read_csv(Path(__file__).parent / "main_data.csv", parse_dates=["datetime"])
    df["month"] = df["datetime"].dt.month
    return df


df = load_data()

# Sidebar filter
with st.sidebar:
    st.title("Filter")
    date_range = st.date_input(
        "Rentang waktu",
        value=[df["datetime"].min(), df["datetime"].max()],
        min_value=df["datetime"].min(),
        max_value=df["datetime"].max(),
    )
    stations = st.multiselect("Stasiun", sorted(df["station"].unique()), default=sorted(df["station"].unique()))

if len(date_range) != 2:
    st.info("Pilih tanggal awal dan akhir.")
    st.stop()
start_date, end_date = date_range

data = df[
    (df["datetime"] >= pd.to_datetime(start_date))
    & (df["datetime"] <= pd.to_datetime(end_date))
    & (df["station"].isin(stations))
]

st.title("Dashboard Kualitas Udara Beijing (PM2.5)")
st.caption("Data: 12 stasiun pemantauan, Maret 2013 – Februari 2017")

if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Rata-rata PM2.5", f"{data['PM2.5'].mean():.1f} µg/m³")
col2.metric("PM2.5 harian tertinggi", f"{data['PM2.5'].max():.1f} µg/m³")
unhealthy = data["aqi_category"].isin(AQI_LABELS[2:]).mean() * 100
col3.metric("Hari tidak sehat", f"{unhealthy:.1f}%")

# Pertanyaan 1
st.subheader("Rata-rata PM2.5 per Stasiun")
station_pm25 = data.groupby("station")["PM2.5"].mean().sort_values()
colors = ["#d62728" if s == station_pm25.idxmax() else "#2ca02c" if s == station_pm25.idxmin() else "#bdbdbd"
          for s in station_pm25.index]
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(station_pm25.index, station_pm25.values, color=colors)
ax.axvline(75, color="black", linestyle="--", linewidth=1, label="Standar harian China (75)")
for i, v in enumerate(station_pm25.values):
    ax.text(v + 0.5, i, f"{v:.1f}", va="center", fontsize=9)
ax.set_xlabel("Rata-rata PM2.5 (µg/m³)")
ax.legend(loc="lower right")
st.pyplot(fig)

# Pertanyaan 2
st.subheader("Pola Musiman PM2.5")
col1, col2 = st.columns([2, 1])

monthly = data.groupby("month")["PM2.5"].mean().reindex(range(1, 13))
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(MONTH_NAMES, monthly.values, marker="o", color="steelblue", linewidth=2)
ax.set_title("Rata-rata per Bulan")
ax.set_ylabel("PM2.5 (µg/m³)")
ax.set_ylim(bottom=0)
col1.pyplot(fig)

season = data.groupby("season")["PM2.5"].mean().reindex(SEASON_ORDER)
fig, ax = plt.subplots(figsize=(4, 5))
season_colors = ["#d62728" if s == season.idxmax() else "#9ecae1" for s in season.index]
ax.bar(season.index, season.fillna(0).values, color=season_colors)
ax.set_title("Rata-rata per Musim")
ax.set_ylim(bottom=0)
col2.pyplot(fig)

# Analisis lanjutan
st.subheader("Proporsi Hari per Kategori Kualitas Udara")
season_cat = (pd.crosstab(data["season"], data["aqi_category"], normalize="index")
                .reindex(index=SEASON_ORDER, columns=AQI_LABELS, fill_value=0) * 100)
fig, ax = plt.subplots(figsize=(10, 4))
season_cat.plot(kind="barh", stacked=True, color=AQI_COLORS, width=0.7, ax=ax)
ax.set_xlabel("Persentase hari (%)")
ax.set_ylabel(None)
ax.set_xlim(0, 100)
ax.legend(title="Kategori", bbox_to_anchor=(1.01, 1), loc="upper left")
st.pyplot(fig)

st.caption("Kategori berdasarkan rata-rata PM2.5 harian (standar AQI China HJ 633-2012).")
