"""
Potter Airlines - NumPy and Pandas analysis.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from data import Flight, COLUMNS


def flights_to_dataframe(flights: list[Flight]) -> pd.DataFrame:
    """Convert Flight objects into a Pandas DataFrame."""

    # Use the same column order as data.py and the SQLite table
    rows = [flight.as_row() for flight in flights]
    df = pd.DataFrame(rows, columns=COLUMNS)

    # Convert departure dates into Pandas datetime values
    df["depart_date"] = pd.to_datetime(df["depart_date"])

    return df


def validate_dataframe(df: pd.DataFrame) -> None:
    """Check flight data before running calculations."""

    # Check that all required columns are present
    missing_columns = set(COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # Capacity must be greater than zero
    if (df["capacity"] <= 0).any():
        raise ValueError("Capacity must be positive")

    # Seats remaining must be between zero and capacity
    if (df["seats_remaining"] < 0).any():
        raise ValueError("Seats remaining cannot be negative")

    if (df["seats_remaining"] > df["capacity"]).any():
        raise ValueError("Seats remaining cannot exceed capacity")

    # Fare and demand values must be positive
    if (df["base_fare"] <= 0).any():
        raise ValueError("Base fare must be positive")

    if (df["demand_index"] <= 0).any():
        raise ValueError("Demand index must be positive")


def add_analytics(
    df: pd.DataFrame,
    as_of: date | None = None,
) -> pd.DataFrame:
    """Add vectorized flight and pricing calculations."""

    # Validate before calculating
    validate_dataframe(df)

    # Keep the original DataFrame unchanged
    result = df.copy()

    # Use today's date unless another date is provided
    analysis_date = pd.Timestamp(as_of or date.today())

    # Calculate seats sold for all flights
    result["seats_sold"] = (
        result["capacity"] - result["seats_remaining"]
    )

    # Calculate load factor for all flights
    result["load_factor"] = (
        result["seats_sold"] / result["capacity"]
    )

    # Calculate days until departure
    result["days_until_departure"] = (
        result["depart_date"] - analysis_date
    ).dt.days

    # Tickets cannot be purchased on or after departure
    if (result["days_until_departure"] <= 0).any():
        raise ValueError(
            "Cannot calculate price on or after plane departure"
        )

    # Time factor based on days until departure
    result["time_factor"] = np.select(
        [
            result["days_until_departure"] <= 3,
            result["days_until_departure"] <= 7,
            result["days_until_departure"] <= 14,
        ],
        [
            1.50,
            1.35,
            1.10,
        ],
        default=1.00,
    )

    # Capacity factor increases as the flight fills up
    result["capacity_factor"] = (
        0.85 + 0.50 * result["load_factor"]
    )

    # Weekend departures have a higher factor
    result["weekend_factor"] = np.where(
        result["depart_date"].dt.weekday >= 5,
        1.08,
        1.00,
    )

    # Seasonal factor based on departure month
    months = result["depart_date"].dt.month

    result["season_factor"] = np.select(
        [
            months.isin([12, 1, 2]),
            months.isin([3, 4, 5]),
            months.isin([6, 7, 8]),
            months.isin([9, 10, 11]),
        ],
        [
            1.05,
            1.00,
            1.20,
            0.90,
        ],
        default=np.nan,
    )

    # Make sure every departure date received a seasonal factor
    if result["season_factor"].isna().any():
        raise ValueError("Invalid departure month")

    # Calculate dynamic prices for all flights without a Python loop
    result["price"] = (
        result["base_fare"]
        * result["demand_index"]
        * result["time_factor"]
        * result["capacity_factor"]
        * result["weekend_factor"]
        * result["season_factor"]
    )

    # Round prices to cents
    result["price"] = result["price"].round(2)

    return result


def filter_by_route(
    df: pd.DataFrame,
    origin: str,
    destination: str,
) -> pd.DataFrame:
    """Return flights matching a route."""

    # Filter using origin and destination
    return df[
        (df["origin"] == origin)
        & (df["destination"] == destination)
    ].copy()


def filter_available_flights(df: pd.DataFrame) -> pd.DataFrame:
    """Return flights that still have seats available."""

    # Remove sold-out flights
    return df[
        df["seats_remaining"] > 0
    ].copy()


def rank_by_price(
    df: pd.DataFrame,
    ascending: bool = True,
) -> pd.DataFrame:
    """Rank flights by dynamic price."""

    # Price must already be calculated
    if "price" not in df.columns:
        raise ValueError(
            "Run add_analytics before ranking by price"
        )

    # Lowest price first by default
    return df.sort_values(
        by="price",
        ascending=ascending,
    ).reset_index(drop=True)


def rank_by_load_factor(df: pd.DataFrame) -> pd.DataFrame:
    """Rank flights from fullest to emptiest."""

    # Load factor must already be calculated
    if "load_factor" not in df.columns:
        raise ValueError(
            "Run add_analytics before ranking by load factor"
        )

    # Fullest flights first
    return df.sort_values(
        by="load_factor",
        ascending=False,
    ).reset_index(drop=True)


def summarize_by_route(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize prices and flight activity by route."""

    # Analytics must be calculated before creating the summary
    required = {"price", "load_factor"}

    if not required.issubset(df.columns):
        raise ValueError(
            "Run add_analytics before summarizing routes"
        )

    # Group flights by route and calculate summary statistics
    summary = (
        df.groupby(
            ["origin", "destination"],
            as_index=False,
        )
        .agg(
            number_of_flights=("flight_id", "count"),
            average_price=("price", "mean"),
            minimum_price=("price", "min"),
            maximum_price=("price", "max"),
            average_load_factor=("load_factor", "mean"),
            average_demand_index=("demand_index", "mean"),
        )
    )

    # Round summary values
    summary["average_price"] = (
        summary["average_price"].round(2)
    )
    summary["minimum_price"] = (
        summary["minimum_price"].round(2)
    )
    summary["maximum_price"] = (
        summary["maximum_price"].round(2)
    )
    summary["average_load_factor"] = (
        summary["average_load_factor"].round(3)
    )
    summary["average_demand_index"] = (
        summary["average_demand_index"].round(3)
    )

    # Highest average priced routes first
    return summary.sort_values(
        by="average_price",
        ascending=False,
    ).reset_index(drop=True)


def summarize_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize prices and flight activity by season."""

    # Analytics must be calculated before creating the summary
    required = {"price", "load_factor"}

    if not required.issubset(df.columns):
        raise ValueError(
            "Run add_analytics before summarizing seasons"
        )

    # Group flights by the season already stored in the dataset
    summary = (
        df.groupby(
            "season",
            as_index=False,
        )
        .agg(
            number_of_flights=("flight_id", "count"),
            average_price=("price", "mean"),
            average_load_factor=("load_factor", "mean"),
        )
    )

    # Round summary values
    summary["average_price"] = (
        summary["average_price"].round(2)
    )
    summary["average_load_factor"] = (
        summary["average_load_factor"].round(3)
    )

    return summary


if __name__ == "__main__":
    from data import generate_flights

    # Generate the project flight data
    flights = generate_flights()

    # Convert flights into a DataFrame
    df = flights_to_dataframe(flights)

    # Run vectorized NumPy and Pandas calculations
    df = add_analytics(df)

    # Display sample flight prices and pricing factors
    print("\nFlight analysis:")
    print(
        df[
            [
                "flight_id",
                "origin",
                "destination",
                "days_until_departure",
                "load_factor",
                "time_factor",
                "capacity_factor",
                "weekend_factor",
                "season_factor",
                "price",
            ]
        ].head(10)
    )

    # Show available flights ranked from cheapest to most expensive
    print("\nAvailable flights ranked by price:")
    available = filter_available_flights(df)

    print(
        rank_by_price(available)[
            [
                "flight_id",
                "origin",
                "destination",
                "seats_remaining",
                "price",
            ]
        ].head(10)
    )

    # Display route-level analysis
    print("\nRoute summary:")
    print(summarize_by_route(df))

    # Display seasonal analysis
    print("\nSeason summary:")
    print(summarize_by_season(df))