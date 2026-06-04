"""
CLI entry point.

Local file usage:
    isca-validate <notebook.[sql|py|ipynb]> [options]

Databricks usage:
    isca-validate --databricks /Users/me/my_notebook [options]

Options:
    --databricks PATH   Databricks workspace path (fetched via API, no download)
    --fix               Write the auto-corrected script alongside the original.
    --fix-out PATH      Write the auto-corrected script to PATH.
    --report-out PATH   Write the text report to PATH instead of stdout.
    --no-report         Suppress the report (useful when only --fix is needed).
    --exit-zero         Always exit 0, even when violations exist.

Databricks environment variables (required when using --databricks):
    DATABRICKS_HOST     e.g. https://adb-1234567890.12.azuredatabricks.net
    DATABRICKS_TOKEN    Personal access token or service principal token
"""
import argparse
import os
import sys

from .validator import Validator


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="isca-validate",
        description="Validate a Databricks SQL/PySpark notebook against ISCA Data Engineering Standards.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  isca-validate my_notebook.sql\n"
            "  isca-validate --databricks /Users/me/my_notebook\n"
            "  isca-validate my_notebook.sql --fix\n"
            "  isca-validate --databricks /Users/me/my_notebook --report-out report.txt\n"
        ),
    )

    # Source — mutually exclusive: local file or Databricks path
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "notebook",
        nargs="?",
        help="Path to a local notebook file (.sql, .py, .ipynb)",
    )
    source.add_argument(
        "--databricks",
        metavar="PATH",
        default=None,
        help="Databricks workspace path, e.g. /Users/me/my_notebook (requires DATABRICKS_HOST and DATABRICKS_TOKEN env vars)",
    )

    parser.add_argument("--fix", action="store_true", help="Auto-fix and save corrected script locally")
    parser.add_argument("--fix-out", metavar="PATH", default=None, help="Output path for the fixed script")
    parser.add_argument("--report-out", metavar="PATH", default=None, help="Write report to file instead of stdout")
    parser.add_argument("--no-report", action="store_true", help="Suppress the validation report")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit with code 0")
    args = parser.parse_args(argv)

    # Build Validator — local file or Databricks
    if args.databricks:
        v = _load_from_databricks(args.databricks, parser)
    else:
        if not os.path.isfile(args.notebook):
            parser.error(f"File not found: {args.notebook}")
        v = Validator(args.notebook)

    # Report
    if not args.no_report:
        report = v.report()
        if args.report_out:
            with open(args.report_out, "w", encoding="utf-8") as fh:
                fh.write(report)
            print(f"Report written to: {args.report_out}")
        else:
            print(report)

    # Fix
    if args.fix or args.fix_out:
        fix_out = _resolve_fix_out(args, v)
        out = v.save_fixed(fix_out)
        print(f"Fixed script written to: {out}")

    if args.exit_zero:
        sys.exit(0)

    violations = v.validate()
    errors = [vv for vv in violations if vv.severity == "error"]
    sys.exit(1 if errors else 0)


def _load_from_databricks(workspace_path: str, parser: argparse.ArgumentParser) -> Validator:
    """Fetch a notebook from Databricks and return a Validator instance."""
    try:
        from .databricks_fetcher import fetch_notebook
    except ImportError as exc:
        parser.error(f"Could not import databricks_fetcher: {exc}")

    print(f"Fetching from Databricks: {workspace_path}")
    try:
        lines, is_python, label = fetch_notebook(workspace_path)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    lang = "Python" if is_python else "SQL"
    print(f"Fetched {len(lines)} lines ({lang})")
    return Validator(path=label, lines=lines, is_python=is_python)


_FIXER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixer")


def _resolve_fix_out(args: argparse.Namespace, v: Validator) -> str:
    """
    Resolve the output path for the fixed script.
    Defaults to the 'fixer/' folder in the project root.
    The folder is created automatically if it does not exist.
    """
    if args.fix_out:
        out_dir = os.path.dirname(args.fix_out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        return args.fix_out

    os.makedirs(_FIXER_DIR, exist_ok=True)

    if args.databricks:
        nb_name = args.databricks.rstrip("/").split("/")[-1]
    else:
        nb_name = os.path.splitext(os.path.basename(v.path))[0]

    ext = ".py" if v.is_python else ".sql"
    return os.path.join(_FIXER_DIR, f"{nb_name}_fixed{ext}")


if __name__ == "__main__":
    main()
