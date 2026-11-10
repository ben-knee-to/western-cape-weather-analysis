
import streamlit as st
import pandas as pd
import plotly.express as px

from pathlib import Path

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Western Cape Weather Analytics",
    page_icon="🌦️",
    layout="wide"
)

st.title("🌦️ Western Cape Historical Weather Analytics")
st.caption(
    "Exploring historical temperature, rainfall, "
    "sunshine and wind patterns across the Western Cape, "
    "South Africa."
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

DATA_FILE = (
    Path(__file__).parent
    / "data"
    / "western_cape_weather_cleaned.csv"
)


@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path, parse_dates=["date"])

    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

    return df


if not DATA_FILE.exists():
    st.error(
        "Cleaned dataset not found. "
        "Run fetch_weather.py and clean_weather.py first."
    )
    st.stop()

df = load_data(DATA_FILE)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

locations = sorted(df["location"].dropna().unique())

selected_locations = st.sidebar.multiselect(
    "Select locations",
    options=locations,
    default=locations
)

available_years = sorted(
    df["year"].dropna().unique()
)

selected_years = st.sidebar.slider(
    "Select year range",
    min_value=int(min(available_years)),
    max_value=int(max(available_years)),
    value=(
        int(min(available_years)),
        int(max(available_years))
    )
)

if not selected_locations:
    st.warning("Select at least one location.")
    st.stop()

filtered = df[
    df["location"].isin(selected_locations)
    & df["year"].between(
        selected_years[0],
        selected_years[1]
    )
].copy()

if filtered.empty:
    st.warning("No records match your selected filters.")
    st.stop()

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

st.subheader("Weather Overview")

col1, col2, col3, col4 = st.columns(4)

mean_temp = filtered["temperature_2m_mean"].mean()
total_rain = filtered["precipitation_sum"].sum()
max_temp = filtered["temperature_2m_max"].max()
mean_wind = filtered["wind_speed_10m_max"].mean()

col1.metric(
    "Average Temperature",
    f"{mean_temp:.1f} °C"
    if pd.notna(mean_temp) else "N/A"
)

col2.metric(
    "Recorded Precipitation",
    f"{total_rain:,.0f} mm"
    if pd.notna(total_rain) else "N/A"
)

col3.metric(
    "Highest Daily Temperature",
    f"{max_temp:.1f} °C"
    if pd.notna(max_temp) else "N/A"
)

col4.metric(
    "Average Daily Maximum Wind",
    f"{mean_wind:.1f} km/h"
    if pd.notna(mean_wind) else "N/A"
)

st.caption(
    "Rainfall is summed across the selected locations and dates. "
    "It is not a single province-wide rainfall total. "
    "Temperature and wind metrics summarise daily records."
)

st.divider()

# --------------------------------------------------
# TEMPERATURE ANALYSIS
# --------------------------------------------------

st.header("1. Temperature Trends")

annual_temp = (
    filtered.groupby(
        ["year", "location"], as_index=False
    )
    .agg(
        mean_temperature=("temperature_2m_mean", "mean"),
        mean_max_temperature=("temperature_2m_max", "mean"),
        mean_min_temperature=("temperature_2m_min", "mean")
    )
)

fig_temp = px.line(
    annual_temp,
    x="year",
    y="mean_temperature",
    color="location",
    markers=True,
    title="Annual Average Temperature by Location",
    labels={
        "year": "Year",
        "mean_temperature": "Average Temperature (°C)",
        "location": "Location"
    }
)

st.plotly_chart(fig_temp, use_container_width=True)

# Daily maximum vs minimum temperature
temperature_comparison = (
    filtered.groupby("location", as_index=False)
    .agg(
        average_max=("temperature_2m_max", "mean"),
        average_min=("temperature_2m_min", "mean")
    )
)

temp_long = temperature_comparison.melt(
    id_vars="location",
    value_vars=["average_max", "average_min"],
    var_name="temperature_type",
    value_name="temperature"
)

temp_long["temperature_type"] = temp_long[
    "temperature_type"
].map({
    "average_max": "Average Daily Maximum",
    "average_min": "Average Daily Minimum"
})

fig_range = px.bar(
    temp_long,
    x="location",
    y="temperature",
    color="temperature_type",
    barmode="group",
    title="Average Daily Maximum and Minimum Temperatures",
    labels={
        "location": "Location",
        "temperature": "Temperature (°C)",
        "temperature_type": "Measure"
    }
)

st.plotly_chart(fig_range, use_container_width=True)

st.divider()

# --------------------------------------------------
# RAINFALL ANALYSIS
# --------------------------------------------------

st.header("2. Rainfall Analysis")

monthly_rain = (
    filtered.groupby(
        ["month", "month_name", "location"],
        observed=True,
        as_index=False
    )
    .agg(
        average_monthly_rainfall=("precipitation_sum", "mean")
    )
)

fig_rain = px.line(
    monthly_rain,
    x="month",
    y="average_monthly_rainfall",
    color="location",
    markers=True,
    title="Average Daily Precipitation by Month",
    labels={
        "month": "Month Number",
        "average_monthly_rainfall": "Average Daily Precipitation (mm)",
        "location": "Location"
    }
)

fig_rain.update_xaxes(
    tickmode="array",
    tickvals=list(range(1, 13)),
    ticktext=[
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
)

st.plotly_chart(fig_rain, use_container_width=True)

# Annual precipitation per location
annual_rain = (
    filtered.groupby(
        ["year", "location"], as_index=False
    )
    .agg(
        annual_precipitation=("precipitation_sum", "sum")
    )
)

fig_annual_rain = px.bar(
    annual_rain,
    x="year",
    y="annual_precipitation",
    color="location",
    barmode="group",
    title="Annual Recorded Precipitation by Location",
    labels={
        "year": "Year",
        "annual_precipitation": "Precipitation (mm)",
        "location": "Location"
    }
)

st.plotly_chart(
    fig_annual_rain,
    use_container_width=True
)

st.divider()

# --------------------------------------------------
# SEASONAL ANALYSIS
# --------------------------------------------------

st.header("3. Seasonal Weather Patterns")

season_order = [
    "Summer", "Autumn", "Winter", "Spring"
]

seasonal = (
    filtered.groupby(
        ["season", "location"],
        observed=True,
        as_index=False
    )
    .agg(
        average_temperature=("temperature_2m_mean", "mean"),
        average_daily_precipitation=("precipitation_sum", "mean")
    )
)

seasonal["season"] = pd.Categorical(
    seasonal["season"],
    categories=season_order,
    ordered=True
)

seasonal = seasonal.sort_values("season")

fig_season = px.bar(
    seasonal,
    x="season",
    y="average_temperature",
    color="location",
    barmode="group",
    title="Average Temperature by Season",
    labels={
        "season": "Season",
        "average_temperature": "Temperature (°C)",
        "location": "Location"
    }
)

st.plotly_chart(
    fig_season,
    use_container_width=True
)

# --------------------------------------------------
# WIND AND SUNSHINE
# --------------------------------------------------

st.header("4. Wind and Sunshine")

col1, col2 = st.columns(2)

wind_data = (
    filtered.groupby("location", as_index=False)
    .agg(
        average_max_wind=("wind_speed_10m_max", "mean")
    )
)

fig_wind = px.bar(
    wind_data,
    x="location",
    y="average_max_wind",
    title="Average Daily Maximum Wind Speed",
    labels={
        "location": "Location",
        "average_max_wind": "Wind Speed (km/h)"
    }
)

col1.plotly_chart(
    fig_wind,
    use_container_width=True
)

sunshine_data = (
    filtered.groupby("location", as_index=False)
    .agg(
        average_sunshine=("sunshine_duration", "mean")
    )
)

sunshine_data["average_sunshine_hours"] = (
    sunshine_data["average_sunshine"] / 3600
)

fig_sunshine = px.bar(
    sunshine_data,
    x="location",
    y="average_sunshine_hours",
    title="Average Daily Sunshine Duration",
    labels={
        "location": "Location",
        "average_sunshine_hours": "Sunshine (hours/day)"
    }
)

col2.plotly_chart(
    fig_sunshine,
    use_container_width=True
)

st.divider()

# --------------------------------------------------
# DATA EXPLORER
# --------------------------------------------------

st.header("5. Explore the Dataset")

st.write(
    "Inspect and download the weather records "
    "matching your selected filters."
)

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="western_cape_weather_filtered.csv",
    mime="text/csv"
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "Data source: Open-Meteo Historical Weather API. "
    "Historical values are reanalysis-based estimates, "
    "not necessarily direct weather-station measurements."
)
