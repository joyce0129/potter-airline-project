"""Search flights or update seat inventory: python main.py.

Requires pandas and numpy. When SQLite is empty, load flights.csv next to this
script. Later runs reuse stored records. Searching does not change seats.
"""

import csv
from datetime import date
from pathlib import Path

from analytics import (
    add_analytics,
    flights_to_dataframe,
    summarize_by_route,
)
from data import COLUMNS, Flight
from db import (
    create_flights_table,
    get_all_flights,
    get_flight_by_id,
    insert_flights,
    update_flight,
)


def load_csv_flights(path: Path) -> list[Flight]:
    """Read CSV values into validated Flight objects before storing them."""
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing = set(COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        flights = []
        for row in reader:
            try:
                flights.append(Flight(
                    flight_id=row["flight_id"],
                    origin=row["origin"],
                    destination=row["destination"],
                    depart_date=date.fromisoformat(row["depart_date"]),
                    base_fare=float(row["base_fare"]),
                    seats_remaining=int(row["seats_remaining"]),
                    capacity=int(row["capacity"]),
                    demand_index=float(row["demand_index"]),
                    season=row["season"],
                ))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid flight at CSV line {reader.line_num}: {exc}") from exc
    if len({flight.flight_id for flight in flights}) != len(flights):
        raise ValueError("CSV flight IDs must be unique")
    return flights


def update_seats_remaining():
    """Validate an inventory adjustment, save it, and verify persistence."""
    flight_id = input("Flight ID: ").strip().upper()
    flight = get_flight_by_id(flight_id)
    if flight is None:
        print(f"No flight found with ID {flight_id}.")
        return

    print(flight)
    while True:
        try:
            new_seat_count = int(input(
                f"New seats remaining (0–{flight.capacity}): "
            ).strip())
        except ValueError:
            print("Enter a whole number.")
            continue
        if not 0 <= new_seat_count <= flight.capacity:
            print(f"Seat count must be between 0 and {flight.capacity}.")
            continue
        break

    previous_count = flight.seats_remaining
    flight.seats_remaining = new_seat_count
    update_flight(flight)
    saved_flight = get_flight_by_id(flight_id)
    assert saved_flight is not None, "Updated flight must exist in SQLite"
    assert saved_flight.seats_remaining == new_seat_count, (
        "Saved seat count does not match the requested update"
    )
    print(f"Updated {flight_id}: {previous_count} -> "
          f"{saved_flight.seats_remaining} seats remaining.")
    print("Validation passed: the saved seat count was retrieved from SQLite.")


def main():
    """Initialize stored flight data and offer search and inventory actions."""
    create_flights_table()
    flights = get_all_flights()
    if not flights:
        csv_path = Path(__file__).resolve().with_name("flights.csv")
        try:
            csv_flights = load_csv_flights(csv_path)
        except (OSError, ValueError) as exc:
            print(f"Could not load flight data: {exc}")
            return
        if not csv_flights:
            print("flights.csv contains no flight records.")
            return
        insert_flights(csv_flights)
        flights = get_all_flights()
        print(f"Loaded {len(flights)} flights from flights.csv into SQLite.")
    else:
        print(f"Using {len(flights)} stored flights from SQLite.")

    while True:
        print("\nPotter Airlines")
        print("1. Search flights")
        print("2. Update seats remaining")
        print("3. Exit")
        choice = input("Choose an option (1–3): ").strip()
        if choice == "1":
            search_flights()
        elif choice == "2":
            update_seats_remaining()
        elif choice == "3":
            print("Goodbye.")
            return
        else:
            print("Choose 1, 2, or 3.")


def search_flights():
    """Search current stored records so inventory changes appear immediately."""
    today = date.today()
    flights = get_all_flights()
    destinations = sorted({flight.destination for flight in flights})

    print("Potter Airlines — Flight Search")
    print("Destinations: " + ", ".join(destinations))
    print("Show flights departing on or after your date, earliest first.")
    print("Press Ctrl+C to exit.\n")

    while True:
        entered_date = input("Depart on or after (YYYY-MM-DD): ").strip()
        try:
            departure_date = date.fromisoformat(entered_date)
            if entered_date != departure_date.isoformat():
                raise ValueError
        except ValueError:
            print("Enter a valid date in YYYY-MM-DD format.")
            continue
        if departure_date <= today:
            print("Enter a future date; same-day and past fares are unavailable.")
            continue
        break

    while True:
        destination = input("Destination airport code (for example, YVR): ").strip().upper()
        if destination in destinations:
            break
        print("Choose a destination from: " + ", ".join(destinations))

    df = flights_to_dataframe(flights)
    matches = df[
        (df["depart_date"].dt.date >= departure_date)
        & (df["destination"] == destination)
    ].copy()
    if matches.empty:
        print(f"\nNo flights found to {destination} on or after {departure_date}.")
        return

    ranked = add_analytics(matches, as_of=today).sort_values(
        ["depart_date", "flight_id"]
    )
    ranked["availability"] = ranked["seats_remaining"].gt(0).map(
        {True: "Available", False: "Sold out"}
    )
    details = ranked[
        ["flight_id", "origin", "destination", "depart_date", "base_fare",
         "price", "seats_remaining", "capacity", "availability"]
    ].rename(columns={"price": "adjusted_fare"})
    print(f"\nFound {len(details)} flight(s) to {destination} on or after "
          f"{departure_date}, sorted by departure date:")
    print(details.to_string(
        index=False,
        formatters={"base_fare": "${:.2f}".format,
                    "adjusted_fare": "${:.2f}".format},
    ))

    # Use the same filtered flights as the details above, not the full database.
    summary_formatters = {
        "average_price": "${:.2f}".format,
        "minimum_price": "${:.2f}".format,
        "maximum_price": "${:.2f}".format,
    }
    print("\nRoute summary — displayed flights only:")
    route_summary = summarize_by_route(ranked)[
        ["origin", "destination", "number_of_flights",
         "average_price", "minimum_price", "maximum_price"]
    ]
    print(route_summary.to_string(
        index=False, formatters=summary_formatters,
    ))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram closed.")
