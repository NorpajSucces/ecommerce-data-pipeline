# Unit tests for pipeline audit helper validation and database updates.

from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pipeline_audit  # noqa: E402


def make_mock_connection(rowcount=1):
    cursor = MagicMock()
    cursor.rowcount = rowcount

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection, cursor


class PipelineAuditTests(unittest.TestCase):
    def test_start_run_inserts_running_record_and_returns_uuid(self):
        connection, cursor = make_mock_connection()

        with patch.object(
            pipeline_audit, "get_connection", return_value=connection
        ):
            run_id = pipeline_audit.start_run("ecommerce_data_pipeline")

        self.assertIsInstance(run_id, UUID)
        cursor.execute.assert_called_once()
        sql_query, params = cursor.execute.call_args.args
        self.assertIn("INSERT INTO audit.pipeline_runs", sql_query)
        self.assertEqual(params, (run_id, "ecommerce_data_pipeline"))

    def test_finish_run_rejects_invalid_status(self):
        with self.assertRaises(ValueError):
            pipeline_audit.finish_run(
                "run-1",
                status="running",
                exit_code=0,
            )

    def test_finish_run_rejects_inconsistent_succeeded_arguments(self):
        with self.assertRaises(ValueError):
            pipeline_audit.finish_run(
                "run-1",
                status="succeeded",
                exit_code=1,
            )

        with self.assertRaises(ValueError):
            pipeline_audit.finish_run(
                "run-1",
                status="succeeded",
                exit_code=0,
                failed_step="Load or verify orders",
            )

    def test_finish_run_rejects_inconsistent_failed_arguments(self):
        with self.assertRaises(ValueError):
            pipeline_audit.finish_run(
                "run-1",
                status="failed",
                exit_code=0,
                failed_step="Load or verify orders",
            )

        with self.assertRaises(ValueError):
            pipeline_audit.finish_run(
                "run-1",
                status="failed",
                exit_code=1,
                failed_step=None,
            )

        with self.assertRaises(ValueError):
            pipeline_audit.finish_run(
                "run-1",
                status="failed",
                exit_code=1,
                failed_step="   ",
            )

    def test_finish_run_raises_when_no_running_row_updated(self):
        connection, _ = make_mock_connection(rowcount=0)

        with patch.object(
            pipeline_audit, "get_connection", return_value=connection
        ):
            with self.assertRaises(RuntimeError):
                pipeline_audit.finish_run(
                    "run-1",
                    status="succeeded",
                    exit_code=0,
                )

    def test_finish_run_updates_running_record_successfully(self):
        connection, cursor = make_mock_connection(rowcount=1)

        with patch.object(
            pipeline_audit, "get_connection", return_value=connection
        ):
            pipeline_audit.finish_run(
                "run-1",
                status="failed",
                exit_code=7,
                failed_step="Load or verify orders",
            )

        cursor.execute.assert_called_once()
        sql_query, params = cursor.execute.call_args.args
        self.assertIn("UPDATE audit.pipeline_runs", sql_query)
        self.assertEqual(
            params,
            ("failed", "Load or verify orders", 7, "run-1"),
        )


if __name__ == "__main__":
    unittest.main()
