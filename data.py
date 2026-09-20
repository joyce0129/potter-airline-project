"""
Potter Airlines - flight data and the Flight class.
Owner: Joyce  (data + Flight class)

Other modules depend on the names here:
    pricing.py    reads base_fare, demand_index, seats_remaining, capacity, depart_date
    db.py         uses COLUMNS, as_row(), from_row()
    analytics.py  uses COLUMNS as DataFrame column names

Import it as:
    from data import Flight, generate_flights, COLUMNS

Run it directly to generate the data, check it, and write flights.csv:
    python3 data.py
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta

# Routes. base_fare = anchor price; demand_index = how hot the route is (1.00 = average).
ROUTES = {
    ("YYZ", "YUL"): {"base_fare": 119.0, "demand_index": 0.85},  # short hop, many alternatives
    ("YYZ", "JFK"): {"base_fare": 229.0, "demand_index": 1.30},  # business heavy
    ("YYZ", "ORD"): {"base_fare": 199.0, "demand_index": 1.15},  # business heavy
    ("YYZ", "YVR"): {"base_fare": 349.0, "demand_index": 1.00},  # transcontinental
    ("YYZ", "LAX"): {"base_fare": 389.0, "demand_index": 1.10},
    ("YYZ", "MIA"): {"base_fare": 299.0, "demand_index": 1.05},  # snowbird traffic
    ("YYZ", "CUN"): {"base_fare": 329.0, "demand_index": 0.95},  # leisure, price sensitive
    ("YYZ", "LHR"): {"base_fare": 649.0, "demand_index": 1.20},  # long haul
}

CAPACITIES = [78, 137, 189]          # aircraft sizes Potter Airlines flies

# Season of the departure date. 
SEASONS = {12: "winter", 1: "winter", 2: "winter",
           3: "spring", 4: "spring", 5: "spring",
           6: "summer", 7: "summer", 8: "summer",
           9: "fall", 10: "fall", 11: "fall"}


def season_of(depart_date: date) -> str:
    """'winter', 'spring', 'summer' or 'fall' for the month the flight departs."""
    return SEASONS[depart_date.month]


# Column order shared by the SQLite table, as_row() and the DataFrame.
COLUMNS = ("flight_id", "origin", "destination", "depart_date",
           "base_fare", "seats_remaining", "capacity", "demand_index",
           "season")


@dataclass
class Flight:

    flight_id: str
    origin: str
    destination: str
    depart_date: date
    base_fare: float
    seats_remaining: int
    capacity: int
    demand_index: float = 1.00
    season: str = ""                  # filled in from depart_date if left blank

    def __post_init__(self):
        """Reject impossible flights(Validation)."""
        if isinstance(self.depart_date, str):          # SQLite stores dates as text
            self.depart_date = date.fromisoformat(self.depart_date)
        if self.origin == self.destination:
            raise ValueError(f"{self.flight_id}: origin and destination are both {self.origin}")
        if self.capacity <= 0:
            raise ValueError(f"{self.flight_id}: capacity must be positive")
        if not 0 <= self.seats_remaining <= self.capacity:
            raise ValueError(
                f"{self.flight_id}: seats_remaining ({self.seats_remaining}) "
                f"must be between 0 and capacity ({self.capacity})"
            )
        if self.base_fare <= 0 or self.demand_index <= 0:
            raise ValueError(f"{self.flight_id}: base_fare and demand_index must be positive")
        if not self.season:                        # keep it in step with depart_date
            self.season = season_of(self.depart_date)

    @property
    def route(self) -> str:
        return f"{self.origin}-{self.destination}"

    @property
    def load_factor(self) -> float:
        """Fraction of the aircraft already sold"""
        return (self.capacity - self.seats_remaining) / self.capacity

    @property
    def is_weekend_departure(self) -> bool:
        return self.depart_date.weekday() >= 5

    def days_until_departure(self, as_of: date | None = None) -> int:
        """Days from `as_of` (default today) to departure. Negative if already flown."""
        return (self.depart_date - (as_of or date.today())).days

    def sell_seats(self, n: int = 1) -> int:
        """Sell n seats."""
        if n <= 0:
            raise ValueError(f"must sell at least 1 seat, got {n}")
        if n > self.seats_remaining:
            raise ValueError(
                f"{self.flight_id}: cannot sell {n}, only {self.seats_remaining} remain"
            )
        self.seats_remaining -= n
        return self.seats_remaining

    def as_row(self) -> tuple:
        """COLUMNS-ordered tuple for a parameterised INSERT."""
        return (self.flight_id, self.origin, self.destination,
                self.depart_date.isoformat(), self.base_fare,
                self.seats_remaining, self.capacity, self.demand_index,
                self.season)

    @classmethod
    def from_row(cls, row) -> "Flight":
        """Rebuild a Flight from a SELECT result. Re-validates via __post_init__."""
        return cls(*tuple(row))

    #this is a builtin method no? prob delete or change name?
    def __str__(self) -> str:
        return (f"{self.flight_id} {self.route} {self.depart_date} "
                f"({self.seats_remaining}/{self.capacity} seats left, base ${self.base_fare:.0f})")

    def time_factor(self):
        # calculates and returns the time factor that influences price
        days= self.days_until_departure()
        #days away from departure
        if days<=0:
            #error if already departed or now departing
            raise ValueError(f"Cannot buy ticket on or after plane departure")
        elif days<=3:
            #time factor if departure less than or equal to 3 days away
            return 1.5
        elif days<=7:
            #time factor if departure less than or equal to a week away
            return 1.35
        elif days<=14:
            #time factor if departure less than or equal to 2 weeks away
            return 1.1
        else:
            #time factor if departure more than 2 weeks away
            return 1

    def capacity_factor(self):
        #calculates and returns the capacity factor that influences price
        return 0.85+0.5*self.load_factor
        #if load factor is 0 capacity factor is 0.85, otherwise capacity factor becomes 0.85+.5 times the load factor

    def weekend_factor(self):
        #calculates and returns the weekend factor that influences price
        if self.is_weekend_departure:
            #weekend factor if on weekend
            return 1.08
        else:
            #weekend factor if weekday
            return 1

    def season_factor(self):
        #calculates and returns the season factor that influences price
        the_month = self.depart_date.month
        #gets the month
        if (the_month<=2) or (the_month==12):
            #winter season
            return 1.05
        elif the_month<=5:
            #spring season
            return 1
        elif the_month<=8:
            #summer season
            return 1.2
        elif the_month<=11:
            #fall season
            return 0.9
        else:
            #error as not a month
            raise ValueError(f"Not a month")




    def price(self):
        #calculates price by multiplying the base fare by demand factor(which is the demand index), time factor, capacity factor, weekend factor, and season factor
        return self.base_fare*self.demand_index+self.time_factor()+self.capacity_factor()+self.weekend_factor()*self.season_factor()





def generate_flights(n: int = 100, as_of: date | None = None, seed: int = 42) -> list[Flight]:
    """Create n flights departing in the next 365 days(Assumption).

    A full year so every season shows up in the data.

    the data contains the "closer to departure = fuller" pattern the
    pricing model is meant to react to. 
    """
    as_of = as_of or date.today()
    rng = random.Random(seed)          # seeded: everyone gets identical data
    routes = list(ROUTES.items())
    flights = []

    for i in range(n):
        (origin, destination), info = routes[i % len(routes)]
        capacity = rng.choice(CAPACITIES)
        days_out = rng.randint(1, 365)
        depart_date = as_of + timedelta(days=days_out)

        # How much of the plane is already sold, by advance-purchase tier.
        if days_out <= 30:
            sold_ratio = 0.80
        elif days_out <= 60:
            sold_ratio = 0.60
        else:
            sold_ratio = 0.40

        sold_ratio += rng.uniform(-0.08, 0.08)          # so same-tier flights differ
        sold_ratio = min(max(sold_ratio, 0.0), 1.0)     # keep seats within 0..capacity

        flights.append(Flight(
            flight_id=f"PA{1000 + i}",
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            base_fare=info["base_fare"],
            seats_remaining=capacity - round(sold_ratio * capacity),
            capacity=capacity,
            demand_index=round(info["demand_index"] * rng.uniform(0.95, 1.05), 3),
            season=season_of(depart_date),
        ))

    # Force the edge cases the testing module needs.
    flights[0].seats_remaining = 0                       # sold out
    flights[1].seats_remaining = 1                       # last seat
    flights[2].depart_date = as_of + timedelta(days=1)   # departs tomorrow
    flights[2].season = season_of(flights[2].depart_date)   # new date can be a new season
    return flights


def export_csv(flights: list[Flight], path: str = "flights.csv") -> str:
    """Write the flights to a CSV file and return the path."""
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)                        # header row
        writer.writerows(f.as_row() for f in flights)   # one row per flight
    return path


if __name__ == "__main__":
    fleet = generate_flights()
    print(f"Generated {len(fleet)} flights\n")
    for f in fleet[:10]:
        print(" ", f)

    print("\nEdge cases:")
    print(f"  sold out  : {fleet[0]}")
    print(f"  last seat : {fleet[1]}")
    print(f"  tomorrow  : days_until={fleet[2].days_until_departure()}")

    print("\nFlights by season:")
    for s in ("winter", "spring", "summer", "fall"):
        print(f"  {s:7}: {sum(f.season == s for f in fleet)}")

    row = fleet[2].as_row()
    assert Flight.from_row(row) == fleet[2]
    print(f"\nSQLite round-trip OK: {row}")

    path = export_csv(fleet)
    print(f"Wrote {len(fleet)} flights to {path}")

