"""
Databricks Workspace API integration.
Fetches notebook source directly without downloading to local disk.

Accepts either:
  - A workspace path:  /Users/me/folder/my_notebook
  - A full notebook URL: https://adb-xxx.azuredatabricks.net/editor/notebooks/1243119985943256

Required environment variables:
    DATABRICKS_HOST   Full workspace URL, e.g. https://adb-1234567890.12.azuredatabricks.net
                      (auto-extracted when a full URL is passed as the notebook argument)
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


def _parse_notebook_url(url: str) -> Tuple[str, str]:
    """
    Parse a full Databricks notebook URL into (host, object_id).

    Handles formats:
      https://adb-xxx.net/editor/notebooks/1243119985943256?o=...
      https://adb-xxx.net/#notebook/1243119985943256
    """
    parsed = urllib.parse.urlparse(url)
    host = f"{parsed.scheme}://{parsed.netloc}"

    # Format 1: /editor/notebooks/<id>
    path_parts = parsed.path.rstrip("/").split("/")
    for part in reversed(path_parts):
        if part.isdigit():
            return host, part

    # Format 2: fragment like #notebook/1243119985943256
    fragment = parsed.fragment
    if "/" in fragment:
        frag_id = fragment.split("/")[-1]
        if frag_id.isdigit():
            return host, frag_id

    raise RuntimeError(
        f"Could not extract a notebook ID from URL: {url}\n"
        "Expected format: https://<workspace>.azuredatabricks.net/editor/notebooks/<id>"
    )


def fetch_notebook(input_str: str) -> Tuple[List[str], bool, str]:
    """
    Fetch a notebook from the Databricks workspace.

    input_str must be a workspace path, e.g.:
      /Users/me/folder/my_notebook
      /Shared/folder/my_notebook

    Returns:
        (lines, is_python, display_label)

    Raises:
        RuntimeError on any failure.
    """
    token = _require_env("DATABRICKS_TOKEN")

    if input_str.startswith("http://") or input_str.startswith("https://"):
        host, object_id = _parse_notebook_url(input_str)
        raise RuntimeError(
            f"Notebook URLs are not supported by the Databricks API — "
            f"a workspace path is required.\n\n"
            f"  Detected host     : {host}\n"
            f"  Detected notebook : {object_id}\n\n"
            "To get the workspace path:\n"
            "  1. In Databricks, go to Workspace in the left sidebar\n"
            "  2. Right-click your notebook\n"
            "  3. Select 'Copy path'\n"
            "  4. Re-run with: --databricks \"/Users/your.email/folder/notebook_name\""
        )

    host = _require_env("DATABRICKS_HOST")
    workspace_path = input_str

    display_label = f"{host.rstrip('/')}{workspace_path}"

    # Step 1 — get notebook language
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
