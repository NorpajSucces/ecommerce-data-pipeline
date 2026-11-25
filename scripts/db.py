# Shared PostgreSQL connection helper for pipeline scripts.

import os

import psycopg

REQUIRED_ENV_VARS = (
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)


def get_connection():
    missing_variables = [
        name for name in REQUIRED_ENV_VARS if not os.environ.get(name)
    ]

    if missing_variables:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing_variables)
        )

    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    )
