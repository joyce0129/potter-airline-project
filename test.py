from datetime import date, timedelta

import pandas as pd

from data import Flight
from analytics import (
    flights_to_dataframe,
    validate_dataframe,
    add_analytics
)


## make a sample flight for testing
def make_flight(
    flight_id="TEST100",
    origin="YYZ",
    destination="YVR",
    days_until=30,
    base_fare=300,
    seats_remaining=50,
    capacity=100,
    demand_index=1.0
):
    
    return Flight(
        flight_id=flight_id,
        origin=origin,
        destination=destination,
        depart_date=date.today() + timedelta(days=days_until),
        base_fare=base_fare,
        seats_remaining=seats_remaining,
        capacity=capacity,
        demand_index=demand_index
    )

## test the edge cases:
def cannot_equal_destination():

    try:
        make_flight(
            origin="YYZ",
            destination="YYZ"
        )

        print("FAILED: origin cannot equal destination")

    except ValueError:
        print("PASSED: origin cannot equal destination")

def capacity_cannot_be_zero():

    try:
        make_flight(
            capacity=0,
            seats_remaining=0
        )

        print("FAILED: capacity cannot be zero")

    except ValueError:
        print("PASSED: capacity cannot be zero")
def seats_cannot_be_negative():

    try:
        make_flight(
            seats_remaining=-1
        )

        print("FAILED: seats cannot be negative")

    except ValueError:
        print("PASSED: seats cannot be negative")
def seats_cannot_be_negative():

    try:
        make_flight(
            seats_remaining=-1
        )

        print("FAILED: seats cannot be negative")

    except ValueError:
        print("PASSED: seats cannot be negative")
def base_fare_cannot_be_zero():

    try:
        make_flight(
            base_fare=0
        )

        print("FAILED: base fare cannot be zero")

    except ValueError:
        print("PASSED: base fare cannot be zero")

