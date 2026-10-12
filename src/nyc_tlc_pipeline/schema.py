"""Contains the column names and expected data types based on 2024-01 raw yellow taxi trips."""

RAW_SCHEMA = "raw"
RAW_YELLOW_TAXI_TRIPS_TABLE = "yellow_taxi_trips"

RAW_YELLOW_TAXI_TRIPS_COLUMNS: dict[str, str] = {
    "VendorID": "INTEGER",
    "tpep_pickup_datetime": "TIMESTAMP",
    "tpep_dropoff_datetime": "TIMESTAMP",
    "passenger_count": "BIGINT",
    "trip_distance": "DOUBLE",
    "RatecodeID": "BIGINT",
    "store_and_fwd_flag": "VARCHAR",
    "PULocationID": "INTEGER",
    "DOLocationID": "INTEGER",
    "payment_type": "BIGINT",
    "fare_amount": "DOUBLE",
    "extra": "DOUBLE",
    "mta_tax": "DOUBLE",
    "tip_amount": "DOUBLE",
    "tolls_amount": "DOUBLE",
    "improvement_surcharge": "DOUBLE",
    "total_amount": "DOUBLE",
    "congestion_surcharge": "DOUBLE",
    "Airport_fee": "DOUBLE",
}
