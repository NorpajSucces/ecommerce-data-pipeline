# Verify that the pipeline stops after a failed step.

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


class PipelineRunnerTests(unittest.TestCase):
    def test_stops_after_orders_failure(self):
        project_root = Path(__file__).resolve().parent.parent
        runner_path = project_root / "scripts" / "run_pipeline.py"

        failure = subprocess.CalledProcessError(
            returncode=7,
            cmd=["simulated_order_loader"],
        )
        stdout = StringIO()
        stderr = StringIO()

        with (
            patch(
                "subprocess.run",
                side_effect=[None, None, failure],
            ) as mocked_run,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            with self.assertRaises(SystemExit) as exit_context:
                runpy.run_path(
                    str(runner_path),
                    run_name="__main__",
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
        self.assertEqual(exit_context.exception.code, 7)
        self.assertIn(
            "Pipeline stopped at: Load or verify orders.",
            stderr.getvalue(),
        )
        self.assertIn("Exit code: 7", stderr.getvalue())
        self.assertNotIn(
            "Pipeline completed successfully.",
            stdout.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()