# Check the PostgreSQL connection from the local Python environment.

import os

import psycopg

required_variables = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
]

missing_variables = [
    name
    for name in required_variables
    if not os.environ.get(name)
]

if missing_variables:
    raise ValueError(
        "Missing required environment variables: "
        + ", ".join(missing_variables)
    )

with psycopg.connect(
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ["POSTGRES_PORT"]),
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    connect_timeout=10,
) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database(), current_user;"
        )
        database_name, database_user = cursor.fetchone()

print("Database connection successful.")
print(f"Database: {database_name}")
print(f"User: {database_user}")