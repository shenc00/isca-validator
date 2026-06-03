"""
Databricks Workspace API integration.
Fetches notebook source directly without downloading to local disk.

Required environment variables:
    DATABRICKS_HOST   Full workspace URL, e.g. https://adb-1234567890.12.azuredatabricks.net
    DATABRICKS_TOKEN  Personal access token or service principal token
"""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Tuple


def _require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise RuntimeError(
            f"Environment variable {name} is not set. "
            "See README — Databricks Setup for instructions."
        )
    return val


def _api_get(host: str, token: str, endpoint: str, params: dict) -> dict:
    """Authenticated GET request to the Databricks REST API."""
    url = f"{host.rstrip('/')}{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            msg = json.loads(body).get("message", body)
        except Exception:
            msg = body
        raise RuntimeError(f"Databricks API error {exc.code}: {msg}") from exc


def fetch_notebook(workspace_path: str) -> Tuple[List[str], bool, str]:
    """
    Fetch a notebook from the Databricks workspace.

    Returns:
        (lines, is_python, display_label)
        lines        — source lines ready for the Validator
        is_python    — True for Python notebooks, False for SQL
        display_label — human-readable label for reports (host + path)

    Raises:
        RuntimeError if env vars are missing, the API call fails,
        or the notebook language is unsupported.
    """
    host = _require_env("DATABRICKS_HOST")
    token = _require_env("DATABRICKS_TOKEN")

    display_label = f"{host.rstrip('/')}{workspace_path}"

    # Step 1 — resolve notebook language
    status = _api_get(
        host, token,
        "/api/2.0/workspace/get-status",
        {"path": workspace_path},
    )

    obj_type = status.get("object_type", "")
    if obj_type != "NOTEBOOK":
        raise RuntimeError(
            f"'{workspace_path}' is a {obj_type or 'unknown object'}, not a NOTEBOOK."
        )

    language = status.get("language", "").upper()
    if language == "PYTHON":
        is_python = True
    elif language == "SQL":
        is_python = False
    else:
        raise RuntimeError(
            f"Notebook language '{language}' is not supported. "
            "Only SQL and Python notebooks are validated."
        )

    # Step 2 — export source (base64-encoded)
    export = _api_get(
        host, token,
        "/api/2.0/workspace/export",
        {"path": workspace_path, "format": "SOURCE"},
    )

    content_b64 = export.get("content", "")
    if not content_b64:
        raise RuntimeError(f"Empty content returned for '{workspace_path}'.")

    source = base64.b64decode(content_b64).decode("utf-8")
    lines = source.splitlines(keepends=True)

    return lines, is_python, display_label
