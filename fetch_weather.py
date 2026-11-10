
import os
import requests
import pandas as pd

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


session = requests.Session()

retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://", adapter)


# --------------------------------------------------
# PROJECT SETTINGS
# --------------------------------------------------

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

START_DATE = "2010-01-01"
END_DATE = "2025-12-31"

OUTPUT_FOLDER = "data"
OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "western_cape_weather_2010_2025.csv"
)

# Approximate coordinates for each location
LOCATIONS = {
    "Cape Town": (-33.9249, 18.4241),
    "Stellenbosch": (-33.9321, 18.8602),
    "George": (-33.9646, 22.4617),
    "Worcester": (-33.6465, 19.4485),
    "Knysna": (-34.0363, 23.0471),
}

DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "sunshine_duration",
    "wind_speed_10m_max",
    "relative_humidity_2m_mean",
]


# --------------------------------------------------
# DOWNLOAD DATA FOR ONE LOCATION
# --------------------------------------------------

def fetch_location_weather(location, latitude, longitude):

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "Africa/Johannesburg",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    print(f"Downloading weather data for {location}...")

    response = session.get(
        BASE_URL,
        params=params,
        timeout=(20, 60)
    )
    response.raise_for_status()


    result = response.json()

    if "daily" not in result:
        raise ValueError(
            f"No daily weather data returned for {location}"
        )

    df = pd.DataFrame(result["daily"])

    # Add location information
    df["location"] = location
    df["latitude"] = latitude
    df["longitude"] = longitude

    # Standardise the date column
    df["time"] = pd.to_datetime(df["time"])
    df = df.rename(columns={"time": "date"})

    print(f"Downloaded {len(df):,} daily records.")

    return df


# --------------------------------------------------
# DOWNLOAD ALL LOCATIONS
# --------------------------------------------------

def main():

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    weather_data = []

    for location, coordinates in LOCATIONS.items():

        latitude, longitude = coordinates

        try:
            df = fetch_location_weather(
                location,
                latitude,
                longitude
            )

            weather_data.append(df)

        except (requests.RequestException, ValueError) as error:
            print(f"ERROR for {location}: {error}")
            raise

    # Combine all locations into one dataset
    combined_df = pd.concat(
        weather_data,
        ignore_index=True
    )

    # Sort records for easier analysis
    combined_df = combined_df.sort_values(
        ["location", "date"]
    ).reset_index(drop=True)

    # Data quality checks
    print("\nDATA QUALITY CHECKS")
    print("-" * 40)

    print("Total rows:", len(combined_df))
    print("Total columns:", len(combined_df.columns))
    print("Missing values per column:")
    print(combined_df.isnull().sum())

    duplicate_count = combined_df.duplicated(
        subset=["location", "date"]
    ).sum()

    print("Duplicate location-date records:", duplicate_count)

    # Save the combined dataset
    combined_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nDOWNLOAD COMPLETED")
    print(f"Saved dataset to: {OUTPUT_FILE}")

    print("\nPreview:")
    print(combined_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
