"""Exercise the source bundle that the Studio hands to a reviewer."""

import io
import tokenize
import os
import subprocess
import sys

from app.artifacts import generate_bundle


def test_url_shortener_bundle_contains_readable_runnable_source(tmp_path):
    run_dir = tmp_path / "generated-run"
    plan = [{"id": "T1", "name": "Normalize requirement", "status": "completed"}]
    normalized = {
        "normalized_problem": "Build a URL shortener",
        "assumptions": [],
        "ambiguities": [],
    }

    generate_bundle(
        run_dir,
        normalized,
        plan,
        "greenfield",
        "Create a URL shortener with persistence and analytics.",
    )

    source_file = run_dir / "src" / "url_shortener.py"
    generated_source = source_file.read_text(encoding="utf-8")
    assert "from __future__ import annotations" in generated_source
    assert "def shorten(self, url: str) -> dict[str, Any]:" in generated_source
    assert "secrets.choice" in generated_source
    tokens = tokenize.generate_tokens(io.StringIO(generated_source).readline)
    assert not any(token.type == tokenize.OP and token.string == ";" for token in tokens)
    assert (run_dir / "src" / "__init__.py").exists()

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(run_dir)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_url_shortener.py"],
        cwd=run_dir,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
