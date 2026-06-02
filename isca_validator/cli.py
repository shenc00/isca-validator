"""
CLI entry point.

Usage:
    python -m isca_validator <notebook.[sql|py|ipynb]> [options]

Options:
    --fix           Write the auto-corrected script alongside the original.
    --fix-out PATH  Write the auto-corrected script to PATH.
    --report-out PATH  Write the text report to PATH instead of stdout.
    --no-report     Suppress the report (useful when only --fix is needed).
    --exit-zero     Always exit 0, even when violations exist.
"""
import argparse
import sys

from .validator import Validator


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="isca_validator",
        description="Validate a Databricks SQL/PySpark notebook against ISCA Data Engineering Standards.",
    )
    parser.add_argument("notebook", help="Path to the notebook file (.sql, .py, .ipynb)")
    parser.add_argument("--fix", action="store_true", help="Auto-fix and save corrected script")
    parser.add_argument("--fix-out", metavar="PATH", default=None, help="Output path for the fixed script")
    parser.add_argument("--report-out", metavar="PATH", default=None, help="Write report to file instead of stdout")
    parser.add_argument("--no-report", action="store_true", help="Suppress the validation report")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit with code 0")
    args = parser.parse_args(argv)

    v = Validator(args.notebook)

    if not args.no_report:
        report = v.report()
        if args.report_out:
            with open(args.report_out, "w", encoding="utf-8") as fh:
                fh.write(report)
            print(f"Report written to: {args.report_out}")
        else:
            print(report)

    if args.fix or args.fix_out:
        out = v.save_fixed(args.fix_out)
        print(f"Fixed script written to: {out}")

    if args.exit_zero:
        sys.exit(0)

    violations = v.validate()
    errors = [vv for vv in violations if vv.severity == "error"]
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
