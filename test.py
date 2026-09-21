from datetime import date, timedelta

import pandas as pd

from data import Flight
from analytics import (
    flights_to_dataframe,
    validate_dataframe,
    add_analytics
)


##make a flight with default values for testing edge cases

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


##Flight validation edge cases

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


def capacity_cannot_be_negative():

    try:
        make_flight(
            capacity=-100,
            seats_remaining=0
        )

        print("FAILED: capacity cannot be negative")

    except ValueError:
        print("PASSED: capacity cannot be negative")


def seats_cannot_be_negative():

    try:
        make_flight(
            seats_remaining=-1
        )

        print("FAILED: seats cannot be negative")

    except ValueError:
        print("PASSED: seats cannot be negative")


def seats_cannot_exceed_capacity():

    try:
        make_flight(
            seats_remaining=101,
            capacity=100
        )

        print("FAILED: seats cannot exceed capacity")

    except ValueError:
        print("PASSED: seats cannot exceed capacity")


def base_fare_cannot_be_zero():

    try:
        make_flight(
            base_fare=0
        )

        print("FAILED: base fare cannot be zero")

    except ValueError:
        print("PASSED: base fare cannot be zero")


def base_fare_cannot_be_negative():

    try:
        make_flight(
            base_fare=-100
        )

        print("FAILED: base fare cannot be negative")

    except ValueError:
        print("PASSED: base fare cannot be negative")


def demand_cannot_be_zero():

    try:
        make_flight(
            demand_index=0
        )

        print("FAILED: demand index cannot be zero")

    except ValueError:
        print("PASSED: demand index cannot be zero")


def demand_cannot_be_negative():

    try:
        make_flight(
            demand_index=-1
        )

        print("FAILED: demand index cannot be negative")

    except ValueError:
        print("PASSED: demand index cannot be negative")


#seat selling edge cases

def cannot_sell_zero_seats():

    flight = make_flight(
        seats_remaining=10
    )

    try:
        flight.sell_seats(0)

        print("FAILED: cannot sell zero seats")

    except ValueError:
        print("PASSED: cannot sell zero seats")


def cannot_sell_negative_seats():

    flight = make_flight(
        seats_remaining=10
    )

    try:
        flight.sell_seats(-1)

        print("FAILED: cannot sell negative seats")

    except ValueError:
        print("PASSED: cannot sell negative seats")


def cannot_sell_more_than_remaining():

    flight = make_flight(
        seats_remaining=5
    )

    try:
        flight.sell_seats(6)

        print("FAILED: cannot sell more seats than remaining")

    except ValueError:
        print("PASSED: cannot sell more seats than remaining")


def cannot_sell_sold_out_flight():

    flight = make_flight(
        seats_remaining=0
    )

    try:
        flight.sell_seats(1)

        print("FAILED: cannot sell seat from sold out flight")

    except ValueError:
        print("PASSED: cannot sell seat from sold out flight")


def can_sell_last_seat():

    flight = make_flight(
        seats_remaining=1
    )

    flight.sell_seats(1)

    assert flight.seats_remaining == 0

    print("PASSED: last seat can be sold")


##time factor edge cases

def cannot_price_departure_today():

    flight = make_flight(
        days_until=0
    )

    try:
        flight.time_factor()

        print("FAILED: cannot price flight departing today")

    except ValueError:
        print("PASSED: cannot price flight departing today")


def cannot_price_past_flight():

    flight = make_flight(
        days_until=-1
    )

    try:
        flight.time_factor()

        print("FAILED: cannot price past flight")

    except ValueError:
        print("PASSED: cannot price past flight")


def three_day_boundary():

    flight = make_flight(
        days_until=3
    )

    assert flight.time_factor() == 1.50

    print("PASSED: 3 day boundary")


def four_day_boundary():

    flight = make_flight(
        days_until=4
    )

    assert flight.time_factor() == 1.35

    print("PASSED: 4 day boundary")


def seven_day_boundary():

    flight = make_flight(
        days_until=7
    )

    assert flight.time_factor() == 1.35

    print("PASSED: 7 day boundary")


def eight_day_boundary():

    flight = make_flight(
        days_until=8
    )

    assert flight.time_factor() == 1.10

    print("PASSED: 8 day boundary")


def fourteen_day_boundary():

    flight = make_flight(
        days_until=14
    )

    assert flight.time_factor() == 1.10

    print("PASSED: 14 day boundary")


def fifteen_day_boundary():

    flight = make_flight(
        days_until=15
    )

    assert flight.time_factor() == 1.00

    print("PASSED: 15 day boundary")


##Capacity factor edge cases

def empty_plane_capacity():

    flight = make_flight(
        capacity=100,
        seats_remaining=100
    )

    assert flight.capacity_factor() == 0.85

    print("PASSED: empty plane capacity factor")


def full_plane_capacity():

    flight = make_flight(
        capacity=100,
        seats_remaining=0
    )

    assert flight.capacity_factor() == 1.35

    print("PASSED: full plane capacity factor")



## Run all edge cases

def run_edge_cases():

    print("\nFlight validation\n")

    cannot_equal_destination()
    capacity_cannot_be_zero()
    capacity_cannot_be_negative()
    seats_cannot_be_negative()
    seats_cannot_exceed_capacity()
    base_fare_cannot_be_zero()
    base_fare_cannot_be_negative()
    demand_cannot_be_zero()
    demand_cannot_be_negative()

    print("\nSeat selling\n")

    cannot_sell_zero_seats()
    cannot_sell_negative_seats()
    cannot_sell_more_than_remaining()
    cannot_sell_sold_out_flight()
    can_sell_last_seat()

    print("\nTime factor\n")

    cannot_price_departure_today()
    cannot_price_past_flight()
    three_day_boundary()
    four_day_boundary()
    seven_day_boundary()
    eight_day_boundary()
    fourteen_day_boundary()
    fifteen_day_boundary()

    print("\nCapacity factor\n")

    empty_plane_capacity()
    full_plane_capacity()

    print("\nAll edge case tests finished.")


if __name__ == "__main__":
    run_edge_cases()
