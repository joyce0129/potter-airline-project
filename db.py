import sqlite3

from data import Flight, COLUMNS

# Name of the SQLite database file
DB_PATH = "potter_airlines.db"

def get_db_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

# Create table
def create_flights_table():
    """Create the flights table in the database if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_id TEXT PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            depart_date TEXT NOT NULL,
            base_fare REAL NOT NULL,
            seats_remaining INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            demand_index REAL NOT NULL,
            season TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Insert flight data into the database
def insert_flight(flight):
    """Insert a Flight object into the flights table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO flights ({', '.join(COLUMNS)})
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, flight.as_row())
    conn.commit()
    conn.close()

def insert_flights(flights):
    """Insert multiple Flight objects into the flights table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany(f"""
        INSERT INTO flights ({', '.join(COLUMNS)})
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [flight.as_row() for flight in flights])
    conn.commit()
    conn.close()

# Retrieve flight data from the database
def get_all_flights():
    """Retrieve all flights from the flights table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT {', '.join(COLUMNS)} 
        FROM flights""")
    rows = cursor.fetchall()
    conn.close()
    return [Flight.from_row(row) for row in rows]

def get_flight_by_id(flight_id):
    """Retrieve a flight by its ID from the flights table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT {', '.join(COLUMNS)} 
        FROM flights 
        WHERE flight_id = ?""", (flight_id,))
    row = cursor.fetchone()
    conn.close()
    return Flight.from_row(row) if row else None

def get_flights_by_route(origin, destination):
    """Retrieve flights by origin and destination from the flights table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT {', '.join(COLUMNS)} 
        FROM flights
        WHERE origin = ? AND destination = ?
    """, (origin, destination))
    rows = cursor.fetchall()
    conn.close()
    return [Flight.from_row(row) for row in rows]

# Update
def update_flight(flight):
    """Update a Flight object in the flights table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE flights
        SET origin = ?, destination = ?, depart_date = ?, base_fare = ?,
            seats_remaining = ?, capacity = ?, demand_index = ?, season = ?
        WHERE flight_id = ?
    """, flight.as_row()[1:] + (flight.flight_id,))
    conn.commit()
    conn.close()

# Delete flight data from the database
def delete_flight(flight_id):
    """Delete a flight from the flights table by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM flights 
        WHERE flight_id = ?
    """, (flight_id,))
    conn.commit()
    conn.close()

# Helper function to count stored flights
def count_flights():
    """Count the number of flights in the flights table.
    This is useful for checking that all flights have been inserted after 
    generating them."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM flights")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Initialize the database by creating the flights table if it doesn't exist
def initialize_database(flights):
    """Create the flights table and insert initial flight data if the table is empty."""
    create_flights_table()
    if count_flights() == 0:
        insert_flights(flights)

