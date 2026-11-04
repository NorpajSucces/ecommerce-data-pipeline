# Run the existing pipeline steps in dependency order.

from pathlib import Path
import subprocess
import sys

project_root = Path(__file__).resolve().parent.parent

steps = [
    ("Check database connection", "check_database_connection.py"),
    ("Load or verify customers", "load_customers.py"),
    ("Load or verify orders", "load_orders.py"),
    ("Load or verify order items", "load_order_items.py"),
    ("Verify monthly summary", "verify_monthly_summary.py"),
]


def main():
    for step_number, (label, filename) in enumerate(steps, start=1):
        print(
            f"\n[{step_number}/{len(steps)}] {label}",
            flush=True,
        )

        script_path = project_root / "scripts" / filename

        try:
            subprocess.run(
                [sys.executable, str(script_path)],
                cwd=project_root,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(
                f"\nPipeline stopped at: {label}. "
                f"Exit code: {error.returncode}",
                file=sys.stderr,
                flush=True,
            )
            return error.returncode

    print("\nPipeline completed successfully.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())