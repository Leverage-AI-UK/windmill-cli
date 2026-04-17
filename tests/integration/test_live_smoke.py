from __future__ import annotations

import os

import pytest

from wmx.client import WindmillAPI
from wmx.config import resolve_config


@pytest.mark.skipif(
    not (
        os.getenv("WMX_BASE_URL")
        and os.getenv("WMX_WORKSPACE")
        and os.getenv("WMX_TOKEN")
    ),
    reason="Set WMX_BASE_URL, WMX_WORKSPACE, and WMX_TOKEN to run live tests.",
)
def test_live_whoami_smoke() -> None:
    config = resolve_config(base_url=None, workspace=None, token=None).require_complete()
    api = WindmillAPI(config)
    assert api.auth.workspace_whoami()
