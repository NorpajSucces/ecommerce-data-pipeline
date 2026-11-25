# Unit tests for sequential pipeline runner control flow and audit hooks.

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_pipeline.py"

ALL_STEPS = [
    "check_database_connection.py",
    "load_customers.py",
    "load_orders.py",
    "load_order_items.py",
    "verify_monthly_summary.py",
]


def run_runner(*, argv=None, subprocess_side_effect=None, audit=None):
    stdout = StringIO()
    stderr = StringIO()
    audit_module = audit or SimpleNamespace(
        start_run=Mock(return_value="test-run-id"),
        finish_run=Mock(),
    )
    patched_argv = ["run_pipeline.py", *(argv or [])]

    with (
        patch("sys.argv", patched_argv),
        patch.dict("sys.modules", {"pipeline_audit": audit_module}),
        patch(
            "subprocess.run",
            side_effect=subprocess_side_effect,
        ) as mocked_run,
        redirect_stdout(stdout),
        redirect_stderr(stderr),
    ):
        try:
            runpy.run_path(str(RUNNER_PATH), run_name="__main__")
        except SystemExit as exc:
            exit_code = exc.code
        else:
            raise AssertionError("Expected run_pipeline.py to exit via SystemExit.")

    return exit_code, stdout.getvalue(), stderr.getvalue(), mocked_run, audit_module


class PipelineRunnerTests(unittest.TestCase):
    def test_stops_after_orders_failure(self):
        failure = subprocess.CalledProcessError(
            returncode=7,
            cmd=["simulated_order_loader"],
        )

        exit_code, stdout, stderr, mocked_run, audit = run_runner(
            subprocess_side_effect=[None, None, failure],
        )

        executed_files = [
            Path(call.args[0][1]).name
            for call in mocked_run.call_args_list
        ]

        self.assertEqual(
            executed_files,
            [
                "check_database_connection.py",
                "load_customers.py",
                "load_orders.py",
            ],
        )
        self.assertEqual(exit_code, 7)
        self.assertIn("Pipeline stopped at: Load or verify orders.", stderr)
        self.assertIn("Exit code: 7", stderr)
        self.assertNotIn("Pipeline completed successfully.", stdout)
        audit.start_run.assert_called_once_with("ecommerce_data_pipeline")
        audit.finish_run.assert_called_once_with(
            "test-run-id",
            status="failed",
            exit_code=7,
            failed_step="Load or verify orders",
        )

    def test_completes_all_steps_and_records_success(self):
        exit_code, stdout, stderr, mocked_run, audit = run_runner(
            subprocess_side_effect=[None] * len(ALL_STEPS),
        )

        executed_files = [
            Path(call.args[0][1]).name
            for call in mocked_run.call_args_list
        ]

        self.assertEqual(executed_files, ALL_STEPS)
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("Pipeline run ID: test-run-id", stdout)
        self.assertIn("Pipeline completed successfully.", stdout)
        audit.start_run.assert_called_once_with("ecommerce_data_pipeline")
        audit.finish_run.assert_called_once_with(
            "test-run-id",
            status="succeeded",
            exit_code=0,
            failed_step=None,
        )

    def test_aborts_before_steps_when_audit_start_fails(self):
        audit = SimpleNamespace(
            start_run=Mock(side_effect=RuntimeError("database unavailable")),
            finish_run=Mock(),
        )

        exit_code, stdout, stderr, mocked_run, _ = run_runner(audit=audit)

        self.assertEqual(exit_code, 1)
        mocked_run.assert_not_called()
        audit.finish_run.assert_not_called()
        self.assertEqual(stdout, "")
        self.assertIn(
            "Pipeline did not start: audit creation failed (RuntimeError).",
            stderr,
        )

    def test_returns_nonzero_when_final_audit_update_fails(self):
        audit = SimpleNamespace(
            start_run=Mock(return_value="test-run-id"),
            finish_run=Mock(side_effect=RuntimeError("audit write failed")),
        )

        exit_code, stdout, stderr, mocked_run, _ = run_runner(
            subprocess_side_effect=[None] * len(ALL_STEPS),
            audit=audit,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(len(mocked_run.call_args_list), len(ALL_STEPS))
        self.assertNotIn("Pipeline completed successfully.", stdout)
        self.assertIn(
            "Could not finalize audit record: RuntimeError. "
            "Run test-run-id may remain running.",
            stderr,
        )

    def test_records_keyboard_interrupt_with_exit_code_130(self):
        exit_code, stdout, stderr, mocked_run, audit = run_runner(
            subprocess_side_effect=[None, KeyboardInterrupt()],
        )

        self.assertEqual(exit_code, 130)
        self.assertEqual(len(mocked_run.call_args_list), 2)
        self.assertNotIn("Pipeline completed successfully.", stdout)
        self.assertIn("Pipeline stopped at: Load or verify customers.", stderr)
        self.assertIn("Exit code: 130", stderr)
        audit.finish_run.assert_called_once_with(
            "test-run-id",
            status="failed",
            exit_code=130,
            failed_step="Load or verify customers",
        )

    def test_forwards_custom_orders_input_argument(self):
        custom_path = "data/raw/test_cases/orders_changed.csv"
        exit_code, _, _, mocked_run, _ = run_runner(
            argv=["--orders-input", custom_path],
            subprocess_side_effect=[None] * len(ALL_STEPS),
        )

        self.assertEqual(exit_code, 0)
        orders_command = mocked_run.call_args_list[2].args[0]
        customers_command = mocked_run.call_args_list[1].args[0]

        self.assertEqual(
            orders_command[-2:],
            ["--input", str(Path(custom_path))],
        )
        self.assertNotIn("--input", customers_command)


if __name__ == "__main__":
    unittest.main()
