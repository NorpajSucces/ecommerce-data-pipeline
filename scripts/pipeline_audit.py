# Record pipeline execution history in PostgreSQL.

from uuid import uuid4

from db import get_connection


def start_run(pipeline_name):
    run_id = uuid4()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit.pipeline_runs (
                    run_id,
                    pipeline_name,
                    status
                )
                VALUES (%s, %s, 'running');
                """,
                (run_id, pipeline_name),
            )

    return run_id


def finish_run(run_id, *, status, exit_code, failed_step=None):
    if status not in ("succeeded", "failed"):
        raise ValueError("Invalid final pipeline status.")

    if status == "succeeded":
        if exit_code != 0 or failed_step is not None:
            raise ValueError("Inconsistent successful run result.")
    elif exit_code == 0 or not failed_step or not failed_step.strip():
        raise ValueError("A failed run requires a step and nonzero exit code.")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE audit.pipeline_runs
                SET
                    finished_at = clock_timestamp(),
                    status = %s,
                    failed_step = %s,
                    exit_code = %s
                WHERE run_id = %s
                  AND status = 'running';
                """,
                (status, failed_step, exit_code, run_id),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Expected one running audit record to update."
                )