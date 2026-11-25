# Shared snapshot loading for staging tables.

import csv
from pathlib import Path

from psycopg import sql

from db import get_connection


def load_snapshot(*, table_name, file_path, expected_columns, key_columns):
    file_path = Path(file_path)

    if (
        not expected_columns
        or not key_columns
        or not set(key_columns).issubset(expected_columns)
    ):
        raise ValueError("Invalid column configuration for the loader.")

    target_table = sql.Identifier("staging", table_name)
    incoming_table = sql.Identifier("incoming_snapshot")
    column_names = sql.SQL(", ").join(
        sql.Identifier(column)
        for column in expected_columns
    )

    count_query = sql.SQL(
        "SELECT COUNT(*) FROM {};"
    ).format(target_table)

    source_row_count = 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL lock_timeout = '10s';")
            cursor.execute(
                sql.SQL(
                    "LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE;"
                ).format(target_table)
            )

            cursor.execute(
                sql.SQL(
                    "CREATE TEMP TABLE {} "
                    "(LIKE {} INCLUDING ALL) ON COMMIT DROP;"
                ).format(incoming_table, target_table)
            )

            with file_path.open(
                mode="r",
                encoding="utf-8-sig",
                newline="",
            ) as csv_file:
                reader = csv.DictReader(csv_file)

                if reader.fieldnames != expected_columns:
                    raise ValueError(
                        f"{table_name} CSV columns do not match "
                        "the expected header."
                    )

                copy_query = sql.SQL(
                    "COPY {} ({}) FROM STDIN"
                ).format(incoming_table, column_names)

                with cursor.copy(copy_query) as copy:
                    for row in reader:
                        source_row_count += 1

                        if None in row or any(
                            value is None for value in row.values()
                        ):
                            raise ValueError(
                                f"Malformed CSV record: {source_row_count}"
                            )

                        for key_column in key_columns:
                            if not row[key_column].strip():
                                raise ValueError(
                                    f"Missing {key_column} "
                                    f"at record {source_row_count}"
                                )

                        values = tuple(
                            None if row[column] == "" else row[column]
                            for column in expected_columns
                        )
                        copy.write_row(values)

            if source_row_count == 0:
                raise ValueError(f"{table_name} CSV has no data rows.")

            cursor.execute(count_query)
            existing_row_count = cursor.fetchone()[0]

            if existing_row_count == 0:
                cursor.execute(
                    sql.SQL(
                        "INSERT INTO {} ({}) "
                        "SELECT {} FROM {};"
                    ).format(
                        target_table,
                        column_names,
                        column_names,
                        incoming_table,
                    )
                )
                load_status = "loaded"
            else:
                cursor.execute(
                    sql.SQL(
                        """
                        SELECT EXISTS (
                            (
                                SELECT {columns} FROM {incoming}
                                EXCEPT ALL
                                SELECT {columns} FROM {target}
                            )
                            UNION ALL
                            (
                                SELECT {columns} FROM {target}
                                EXCEPT ALL
                                SELECT {columns} FROM {incoming}
                            )
                        );
                        """
                    ).format(
                        columns=column_names,
                        incoming=incoming_table,
                        target=target_table,
                    )
                )

                if cursor.fetchone()[0]:
                    raise RuntimeError(
                        f"staging.{table_name} source differs "
                        "from existing data. "
                        "Load stopped; existing rows were preserved."
                    )

                load_status = "skipped"

            cursor.execute(count_query)
            database_row_count = cursor.fetchone()[0]

            if database_row_count != source_row_count:
                raise RuntimeError(
                    f"Row count mismatch between CSV "
                    f"and staging.{table_name}."
                )

    return {
        "status": load_status,
        "source_rows": source_row_count,
        "database_rows": database_row_count,
    }