# Check the PostgreSQL connection from the local Python environment.

from db import get_connection

with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database(), current_user;"
        )
        database_name, database_user = cursor.fetchone()

print("Database connection successful.")
print(f"Database: {database_name}")
print(f"User: {database_user}")