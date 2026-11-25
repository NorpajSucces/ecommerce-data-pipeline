# Run pipeline steps and record execution history.

import argparse
from pathlib import Path
import subprocess
import sys

from pipeline_audit import finish_run, start_run

project_root = Path(__file__).resolve().parent.parent

steps = [
    ("Check database connection", "check_database_connection.py", None),
    ("Load or verify customers", "load_customers.py", "customers_input"),
    ("Load or verify orders", "load_orders.py", "orders_input"),
    ("Load or verify order items", "load_order_items.py", "order_items_input"),
    ("Verify monthly summary", "verify_monthly_summary.py", None),
]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the e-commerce data pipeline and record audit history."
    )
    parser.add_argument(
        "--customers-input",
        type=Path,
        default=None,
        help="Optional CSV path override for the customers loader.",
    )
    parser.add_argument(
        "--orders-input",
        type=Path,
        default=None,
        help="Optional CSV path override for the orders loader.",
    )
    parser.add_argument(
        "--order-items-input",
        type=Path,
        default=None,
        help="Optional CSV path override for the order items loader.",
    )
    return parser.parse_args(argv)


def record_finish(run_id, *, status, exit_code, failed_step=None):
    try:
        finish_run(
            run_id,
            status=status,
            exit_code=exit_code,
            failed_step=failed_step,
        )
    except Exception as error:
        print(
            f"Could not finalize audit record: {type(error).__name__}. "
            f"Run {run_id} may remain running.",
            file=sys.stderr,
            flush=True,
        )
        return False

    return True


def main(argv=None):
    args = parse_args(argv)

    try:
        run_id = start_run("ecommerce_data_pipeline")
    except Exception as error:
        print(
            f"Pipeline did not start: audit creation failed "
            f"({type(error).__name__}).",
            file=sys.stderr,
            flush=True,
        )
        return 1

    print(f"Pipeline run ID: {run_id}", flush=True)
    label = "Pipeline setup"

    try:
        for step_number, (label, filename, input_arg) in enumerate(
            steps, start=1
        ):
            print(
                f"\n[{step_number}/{len(steps)}] {label}",
                flush=True,
            )

            script_path = project_root / "scripts" / filename
            command = [sys.executable, str(script_path)]

            if input_arg is not None:
                custom_input = getattr(args, input_arg)
                if custom_input is not None:
                    command.extend(["--input", str(custom_input)])

            subprocess.run(
                command,
                cwd=project_root,
                check=True,
            )

    except (Exception, KeyboardInterrupt) as error:
        if isinstance(error, subprocess.CalledProcessError):
            exit_code = error.returncode or 1
        elif isinstance(error, KeyboardInterrupt):
            exit_code = 130
        else:
            exit_code = 1

        record_finish(
            run_id,
            status="failed",
            exit_code=exit_code,
            failed_step=label,
        )

        print(
            f"\nPipeline stopped at: {label}. Exit code: {exit_code}",
            file=sys.stderr,
            flush=True,
        )
        return exit_code

    if not record_finish(
        run_id,
        status="succeeded",
        exit_code=0,
    ):
        return 1

    print("\nPipeline completed successfully.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
