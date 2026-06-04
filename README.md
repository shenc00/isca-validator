# ISCA Validator

Validates Databricks SQL, PySpark, and Jupyter notebook files against the ISCA Data Engineering Standards. It flags violations and can automatically fix many of them.

---

## Step 1 — Install the tool

In windows powershell, navigate to the project root.

```powershell
cd "C:\Users\10320283\OneDrive - BD\Documents\Github\isca-validator"
```

From the project root, run once to install it in editable mode:

```powershell
pip install -e .
```

This registers the `isca-validate` command on your path. Alternatively, you can always run it via:

```powershell
python -m isca_validator <file>
```

---

## Step 2 — Validate a file

Point the validator at any `.sql`, `.py`, or `.ipynb` file:

```powershell
tests\samples\bad_notebook.sql
```

The report prints to the terminal and looks like this:

```
======================================================================
  ISCA Data Engineering Standards — Validation Report
  File: my_notebook.sql
======================================================================
  Summary: 3 error(s), 1 warning(s) across 4 violation(s)

======================================================================
  ERRORS
======================================================================

  [ERROR  ] Line   5 | SQL-01
  Message   : SELECT * is not allowed.
  Suggestion: Explicitly list each required column name.
  Code      : select * from s_isca.otif_orders a

  [ERROR  ] Line  19 | SQL-05
  Message   : IFNULL is not allowed; use COALESCE instead.
  Suggestion: Replace IFNULL(expr, val) with COALESCE(expr, val).
  Code      : SELECT IFNULL(one.Region, 'UNKNOWN') AS Region
  Fixed     : SELECT COALESCE(one.Region, 'UNKNOWN') AS Region
...
```

---

## Step 3 — Auto-fix violations

For violations that have a known fix (keyword casing, IFNULL → COALESCE, snake_case column names, etc.), the validator can rewrite the file automatically.

**Fix in-place (saves as `<filename>_fixed.<ext>`):**
```powershell
isca-validate path\to\my_notebook.sql --fix
```

**Fix to a specific output path:**
```powershell
isca-validate path\to\my_notebook.sql --fix-out path\to\corrected.sql
```

The original file is never overwritten — the fixed version is always written to a new path.

---

## Step 4 — Save the report to a file

```powershell
isca-validate path\to\my_notebook.sql --report-out path\to\report.txt
```

---

## Step 5 — Use in CI / pre-commit hooks

The tool exits with code `1` if any **errors** are found, and `0` if only warnings or nothing. This makes it suitable for blocking pipelines on violations:

```powershell
# In a CI script — fails the pipeline if errors exist
isca-validate path\to\my_notebook.sql
```

To always exit `0` (report only, never block):
```powershell
isca-validate path\to\my_notebook.sql --exit-zero
```

To suppress the report and only apply the fix:
```powershell
isca-validate path\to\my_notebook.sql --fix --no-report
```

---

## What Gets Checked

| Rule ID | Severity | Description |
|---|---|---|
| **SQL-01** | Error | No `SELECT *` — list columns explicitly |
| **SQL-02** | Error | SQL keywords must be `UPPER CASE` |
| **SQL-03** | Error | No positional numbers in `ORDER BY` |
| **SQL-04** | Warning | Table references must include schema prefix (e.g. `s_isca.table`) |
| **SQL-05** | Error | Use `COALESCE` instead of `IFNULL` |
| **SQL-06** | Error | Use `TRIM` — don't combine `LTRIM` + `RTRIM` |
| **SQL-07** | Error | No `DROP TABLE` + `CREATE TABLE` — use `INSERT OVERWRITE TABLE` |
| **SQL-08** | Error | No single-letter table aliases (`a`, `b`) — use `one`, `two`, etc. |
| **SQL-09** | Warning | Qualify column names with table alias in `SELECT` |
| **SQL-10** | Warning | Use temp views (`tv_`) instead of intermediate tables |
| **SQL-11** | Warning | Avoid UDFs — use built-in Spark/Databricks functions |
| **SQL-12** | Warning | Prefer `INSERT OVERWRITE TABLE` over `INSERT INTO` |
| **NAME-COL-01/02/03/04** | Error | Column aliases must be PascalCase, max 255 chars, no special chars |
| **NAME-VIEW-01/02** | Error | Views must start with `v_` and be fully lowercase |
| **NAME-TMPVIEW-01/02** | Error | Temp views must start with `tv_` and be fully lowercase |
| **NAME-TBL-01/02** | Error | Table names must be lowercase with only `a-z`, `0-9`, `_` |
| **PY-01** | Error | No wildcard imports (`from x import *`) |
| **PY-02** | Error | Use `pyspark.pandas` instead of standalone `pandas` |
| **PY-03** | Error/Warning | Use 4-space indentation — no tabs |

---

## Quick Reference

```powershell
# Validate only
isca-validate my_notebook.sql

# Validate + auto-fix
isca-validate my_notebook.sql --fix

# Validate + save report to file
isca-validate my_notebook.sql --report-out report.txt

# Validate + fix + save report + never fail CI
isca-validate my_notebook.sql --fix --report-out report.txt --exit-zero
```

---

## Try It Now with the Sample File

The repo includes a pre-built bad example you can run against immediately:

```powershell
isca-validate tests\samples\bad_notebook.sql
```

This file intentionally violates every rule so you can see what a full report looks like. Run with `--fix` to see the auto-corrected output.

---

## Validating Databricks Notebooks Directly

The `--databricks` flag fetches a notebook from your Databricks workspace via the REST API and validates it in-memory — no file is downloaded to your local drive.

### Databricks Setup

**Step 1 — Generate a personal access token in Databricks**

1. Log in to your Databricks workspace
2. Click your profile icon (top right) → **Settings** → **Developer**
3. Under **Access tokens**, click **Generate new token**
4. Give it a name (e.g. `isca-validator`) and set an expiry
5. Copy the token — it is only shown once

**Step 2 — Set environment variables in PowerShell**

```powershell
$env:DATABRICKS_HOST  = "https://adb-1234567890.12.azuredatabricks.net"
$env:DATABRICKS_TOKEN = "dapi1234abcd..."
```

Your `DATABRICKS_HOST` is the base URL of your workspace — visible in your browser's address bar when logged in.

To make these permanent, add them via **System Properties → Environment Variables → User variables**.

**Step 3 — Get the notebook workspace path**

1. In Databricks, go to **Workspace** in the left sidebar
2. Navigate to and **right-click** your notebook
3. Select **Copy URL/path → Full path**

This gives you the workspace path:

```
/Workspace/FreightwiseApp/ISC-Freightwise/src/proj_DataProducts/nb_salespurchase_orders_apex
```

> **Note:** Do not use the browser URL or the "URL" option — the Databricks API requires the full workspace path, not a notebook ID.

---

### Usage — Databricks Mode

**Validate a notebook directly from Databricks:**

```powershell
isca-validate --databricks "/Workspace/FreightwiseApp/ISC-Freightwise/src/proj_DataProducts/nb_salespurchase_orders_apex"
```

**Validate and save the report to a file:**

```powershell
isca-validate --databricks "/Workspace/FreightwiseApp/ISC-Freightwise/src/proj_DataProducts/nb_salespurchase_orders_apex" --report-out report.txt
```

**Validate and save an auto-fixed version locally:**

```powershell
isca-validate --databricks "/Workspace/FreightwiseApp/ISC-Freightwise/src/proj_DataProducts/nb_salespurchase_orders_apex" --fix
```

The fixed file is saved in your current directory as `<notebook_name>_fixed.sql` or `<notebook_name>_fixed.py`. The original notebook in Databricks is never modified.

**Save the fixed script to a specific path:**

```powershell
isca-validate --databricks "/Workspace/.../nb_salespurchase_orders_apex" --fix-out "C:\Scripts\nb_fixed.sql"
```

**Suppress the report (validate only for CI exit code):**

```powershell
isca-validate --databricks "/Workspace/.../nb_salespurchase_orders_apex" --no-report
```

---

### How It Works

```
isca-validate --databricks "/Workspace/path/to/notebook"
       │
       ├─ GET /api/2.0/workspace/get-status   → detect SQL or Python
       ├─ GET /api/2.0/workspace/export       → fetch source (base64)
       │         (no file written to disk)
       └─ Validator runs in-memory → report printed / saved
```

Only SQL and Python notebooks are supported. Scala and R notebooks will return an unsupported language error.

---

### Quick Reference — Both Modes

```powershell
# Local file
isca-validate my_notebook.sql
isca-validate my_notebook.sql --fix
isca-validate my_notebook.sql --report-out report.txt
isca-validate my_notebook.sql --fix --report-out report.txt --exit-zero

# Databricks (right-click notebook → Copy URL/path → Full path)
isca-validate --databricks "/Workspace/MyApp/project/my_notebook"
isca-validate --databricks "/Workspace/MyApp/project/my_notebook" --fix
isca-validate --databricks "/Workspace/MyApp/project/my_notebook" --report-out report.txt
isca-validate --databricks "/Workspace/MyApp/project/my_notebook" --fix-out fixed.sql --exit-zero
```
