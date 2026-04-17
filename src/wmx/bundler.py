"""Bundle raw app source files using esbuild."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from wmx.errors import UsageError


def bundle_raw_app(value: dict[str, Any]) -> tuple[str, str]:
    """Bundle raw app source files into JS and CSS.

    Args:
        value: The app value containing files, data, and runnables

    Returns:
        Tuple of (bundled_js, bundled_css)

    Raises:
        UsageError: If esbuild is not available or bundling fails
    """
    files = value.get("files", {})
    if not files:
        raise UsageError("No source files found in app value.files")

    # Check for esbuild
    esbuild_cmd = _find_esbuild()
    if not esbuild_cmd:
        raise UsageError(
            "esbuild not found. Install it with: npm install -g esbuild",
            hint="Or use 'npx esbuild' by ensuring npm is available.",
        )

    # Create temp directory with source files
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()

        # Write source files
        for file_path, content in files.items():
            # Remove leading slash for relative path
            rel_path = file_path.lstrip("/")
            file_dest = src_dir / rel_path
            file_dest.parent.mkdir(parents=True, exist_ok=True)
            file_dest.write_text(content, encoding="utf-8")

        # Write package.json if not present (needed for resolution)
        pkg_json = src_dir / "package.json"
        if not pkg_json.exists():
            pkg_json.write_text(json.dumps({
                "dependencies": {
                    "react": "19.0.0",
                    "react-dom": "19.0.0"
                }
            }))

        # Bundle JS
        js_out = Path(tmpdir) / "bundle.js"
        entry_point = _find_entry_point(src_dir)

        js_args = [
            str(entry_point),
            "--bundle",
            "--format=esm",
            "--target=es2020",
            "--jsx=automatic",
            "--minify",
            f"--outfile={js_out}",
            # External react - Windmill provides it
            "--external:react",
            "--external:react-dom",
            "--external:react/jsx-runtime",
            # Handle CSS imports
            "--loader:.css=css",
        ]

        js_result = subprocess.run(
            esbuild_cmd + js_args,
            capture_output=True,
            text=True,
            cwd=src_dir,
        )

        if js_result.returncode != 0:
            raise UsageError(
                f"esbuild failed to bundle JS: {js_result.stderr}",
                hint="Check your source files for syntax errors.",
            )

        bundled_js = js_out.read_text(encoding="utf-8") if js_out.exists() else ""

        # Bundle CSS separately
        css_out = Path(tmpdir) / "bundle.css"
        css_entry = _find_css_entry(src_dir)

        if css_entry:
            css_args = [
                str(css_entry),
                "--bundle",
                "--minify",
                f"--outfile={css_out}",
            ]

            css_result = subprocess.run(
                esbuild_cmd + css_args,
                capture_output=True,
                text=True,
                cwd=src_dir,
            )

            if css_result.returncode != 0:
                # CSS bundling failed, try to extract from JS bundle or use empty
                bundled_css = ""
            else:
                bundled_css = css_out.read_text(encoding="utf-8") if css_out.exists() else ""
        else:
            bundled_css = ""

        # If no separate CSS, check if esbuild extracted it
        esbuild_css = js_out.with_suffix(".css")
        if esbuild_css.exists() and not bundled_css:
            bundled_css = esbuild_css.read_text(encoding="utf-8")

        return bundled_js, bundled_css


def _find_esbuild() -> list[str] | None:
    """Find esbuild command (as list for subprocess)."""
    # Check for global esbuild
    esbuild = shutil.which("esbuild")
    if esbuild:
        return [esbuild]

    # Check for npx
    npx = shutil.which("npx")
    if npx:
        # Verify esbuild is available via npx
        result = subprocess.run(
            [npx, "--yes", "esbuild", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return [npx, "--yes", "esbuild"]

    return None


def _find_entry_point(src_dir: Path) -> Path:
    """Find the entry point file (index.tsx, index.ts, index.jsx, index.js)."""
    for name in ["index.tsx", "index.ts", "index.jsx", "index.js", "main.tsx", "main.ts"]:
        entry = src_dir / name
        if entry.exists():
            return entry

    # Fallback to App.tsx if no index
    app = src_dir / "App.tsx"
    if app.exists():
        return app

    raise UsageError(
        "No entry point found. Expected index.tsx, index.ts, or App.tsx",
        hint="Ensure your app has an entry point file.",
    )


def _find_css_entry(src_dir: Path) -> Path | None:
    """Find the main CSS file."""
    for name in ["index.css", "styles.css", "main.css", "App.css"]:
        css = src_dir / name
        if css.exists():
            return css
    return None
