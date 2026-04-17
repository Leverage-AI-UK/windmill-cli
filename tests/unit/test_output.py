from __future__ import annotations

import json
from pathlib import Path

from wmx.output import OutputManager, OutputOptions


def test_large_payload_spills_to_file(tmp_path, capsys) -> None:
    manager = OutputManager(
        OutputOptions(
            json_mode=True,
            output_mode="auto",
            output_file=None,
            spill_dir=tmp_path,
            spill_threshold_bytes=10,
            quiet=False,
            verbose=False,
        )
    )
    manager.emit({"big": "x" * 200}, label="preview-result", file_stem="preview")
    stdout = capsys.readouterr().out
    manifest = json.loads(stdout)
    saved = Path(manifest["saved_to"])
    assert saved.exists()
    assert json.loads(saved.read_text(encoding="utf-8"))["big"] == "x" * 200

