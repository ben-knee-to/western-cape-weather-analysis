
import os
import pandas as pd

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

INPUT_FILE = (
    "data/western_cape_weather_2010_2025.csv"
)

OUTPUT_FILE = (
    "data/western_cape_weather_cleaned.csv"
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def main():

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}. "
            "Run fetch_weather.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    print("=" * 60)
    print("WESTERN CAPE WEATHER DATA CLEANING")
    print("=" * 60)

    print("\n1. RAW DATA OVERVIEW")
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    print("\nColumn data types:")
    print(df.dtypes)

    # --------------------------------------------------
    # STANDARDISE DATA TYPES
    # --------------------------------------------------

    print("\n2. STANDARDISING DATA TYPES")

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    numeric_columns = [
        "latitude",
        "longitude",
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "sunshine_duration",
        "wind_speed_10m_max",
        "relative_humidity_2m_mean",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------
    # CHECK MISSING VALUES
    # --------------------------------------------------

    print("\n3. MISSING VALUES BEFORE CLEANING")

    print(
        df.isnull().sum().to_string()
    )

    # --------------------------------------------------
    # REMOVE DUPLICATE RECORDS
    # --------------------------------------------------

    print("\n4. DUPLICATE CHECK")

    duplicates = df.duplicated(
        subset=["location", "date"]
    ).sum()

    print("Duplicate location-date records:", duplicates)

    df = df.drop_duplicates(
        subset=["location", "date"],
        keep="first"
    )

    # Records without a usable date or location
    # cannot be used reliably in the dashboard.
    df = df.dropna(
        subset=["date", "location"]
    )

    # --------------------------------------------------
    # VALIDATE WEATHER VALUES
    # --------------------------------------------------

    print("\n5. VALIDATING WEATHER VALUES")

    # These are broad plausibility checks, not
    # absolute physical limits for every location.

    range_checks = {
        "temperature_2m_mean": (-10, 55),
        "temperature_2m_max": (-10, 60),
        "temperature_2m_min": (-15, 50),
        "precipitation_sum": (0, 1000),
        "sunshine_duration": (0, 86400),
        "wind_speed_10m_max": (0, 300),
        "relative_humidity_2m_mean": (0, 100),
    }

    for column, (lower, upper) in range_checks.items():

        if column not in df.columns:
            continue

        invalid = (
            (df[column] < lower)
            | (df[column] > upper)
        )

        invalid_count = int(invalid.sum())

        if invalid_count > 0:
            print(
                f"{column}: {invalid_count} "
                "values outside the accepted range"
            )

            # Flag implausible values as missing
            df.loc[invalid, column] = float("nan")

    # Check temperature consistency
    inconsistent_temperatures = (
        (df["temperature_2m_min"]
         > df["temperature_2m_max"])
        | (
            (df["temperature_2m_mean"]
             < df["temperature_2m_min"])
            & df["temperature_2m_mean"].notna()
        )
        | (
            (df["temperature_2m_mean"]
             > df["temperature_2m_max"])
            & df["temperature_2m_mean"].notna()
        )
    )

    print(
        "Rows with inconsistent temperatures:",
        int(inconsistent_temperatures.sum())
    )

    temperature_columns = [
        "temperature_2m_mean",
        "temperature_2m_min",
        "temperature_2m_max",
    ]

    # Flag inconsistent temperature readings.
    # Keep the date and other weather variables.
    df.loc[
        inconsistent_temperatures,
        temperature_columns
    ] = float("nan")

    # --------------------------------------------------
    # CREATE ANALYSIS COLUMNS
    # --------------------------------------------------

    print("\n6. CREATING ANALYSIS COLUMNS")

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["day"] = df["date"].dt.day

    # Southern Hemisphere seasons
    season_mapping = {
        12: "Summer",
        1: "Summer",
        2: "Summer",
        3: "Autumn",
        4: "Autumn",
        5: "Autumn",
        6: "Winter",
        7: "Winter",
        8: "Winter",
        9: "Spring",
        10: "Spring",
        11: "Spring",
    }

    df["season"] = df["month"].map(
        season_mapping
    )

    # Useful for sorting months in charts
    df["month_name"] = pd.Categorical(
        df["month_name"],
        categories=[
            "January", "February", "March",
            "April", "May", "June",
            "July", "August", "September",
            "October", "November", "December"
        ],
        ordered=True
    )

    # --------------------------------------------------
    # FINAL DATA QUALITY REPORT
    # --------------------------------------------------

    df = df.sort_values(
        ["location", "date"]
    ).reset_index(drop=True)

    print("\n7. FINAL DATA QUALITY REPORT")

    print("Final rows:", len(df))
    print("Final columns:", len(df.columns))

    print("\nMissing values after cleaning:")
    print(df.isnull().sum().to_string())

    print(
        "\nDuplicate location-date records:",
        df.duplicated(
            subset=["location", "date"]
        ).sum()
    )

    print("\nRecords per location:")
    print(df.groupby("location", observed=True).size())

    # --------------------------------------------------
    # SAVE CLEANED DATA
    # --------------------------------------------------

    os.makedirs("data", exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nCLEANING COMPLETED")
    print("Saved to:", OUTPUT_FILE)

    print("\nCleaned data preview:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
