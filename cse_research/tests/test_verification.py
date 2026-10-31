"""Test suite for the CSE verification and diagnostic visualization layer."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Ensure project root and src/scripts are in sys.path
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set cache directory to prevent permissions issues
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / "data" / "cache" / "matplotlib"))

import pytest

from cse.utils.config import find_project_root
from scripts.build_master_report import main as build_master_report_main
from scripts.verify_all import run_all_stages

ROOT_DIR = find_project_root()
VERIFICATION_DIR = ROOT_DIR / "reports" / "verification"
MASTER_DIR = VERIFICATION_DIR / "master"
FILENAME_REGEX = re.compile(r"^stage\d+_[a-z0-9_]+_\d{8}_\d{6}\.png$")


def test_verify_all_execution():
    """Verify that verify_all.py executes Stages 1-8 without exceptions and saves summary."""
    summary = run_all_stages()
    assert summary is not None, "run_all_stages() should return summary dict"
    assert "stages" in summary, "Summary should contain 'stages' list"
    assert len(summary["stages"]) == 8, f"Expected 8 stages, found {len(summary['stages'])}"

    for stg in summary["stages"]:
        assert stg["status"] == "PASS", f"Stage {stg['stage']} failed with error: {stg.get('error')}"
        assert stg["charts"] >= 2, f"Stage {stg['stage']} generated fewer than 2 charts: {stg['charts']}"


def test_chart_counts_and_naming_conventions():
    """Verify that at least 40 PNG files exist and all strictly match the regex naming convention."""
    png_files = list(VERIFICATION_DIR.glob("stage*/*.png"))
    assert len(png_files) >= 40, f"Expected at least 40 diagnostic PNG files, found {len(png_files)}"

    invalid_names = []
    for p in png_files:
        fn = p.name
        if not FILENAME_REGEX.match(fn):
            invalid_names.append(fn)

    assert not invalid_names, f"The following filenames violate regex ^stage\\d+_[a-z0-9_]+_\\d{{8}}_\\d{{6}}\\.png$: {invalid_names[:5]}"


def test_manifests_integrity():
    """Verify that every stage (1 to 8) has a manifest.json with >= 2 entries."""
    for i in range(1, 9):
        stage_key = f"stage{i}"
        manifest_path = VERIFICATION_DIR / stage_key / "manifest.json"
        assert manifest_path.exists(), f"Manifest missing for {stage_key} at {manifest_path}"

        with open(manifest_path, "r", encoding="utf-8") as f:
            entries = json.load(f)

        assert isinstance(entries, list), f"Manifest in {stage_key} must be a list"
        assert len(entries) >= 2, f"Expected >= 2 entries in {stage_key}/manifest.json, found {len(entries)}"

        for e in entries:
            assert "filename" in e, f"Entry missing 'filename': {e}"
            assert "topic" in e, f"Entry missing 'topic': {e}"
            assert "detail" in e, f"Entry missing 'detail': {e}"
            assert "summary" in e, f"Entry missing 'summary': {e}"
            assert "timestamp" in e, f"Entry missing 'timestamp': {e}"
            assert "stage" in e, f"Entry missing 'stage': {e}"
            assert FILENAME_REGEX.match(e["filename"]), f"Manifest filename mismatch: {e['filename']}"


def test_master_html_report():
    """Verify that master report index.html exists, contains 8 sections, and links work."""
    build_master_report_main()

    index_html = MASTER_DIR / "index.html"
    run_summary_json = MASTER_DIR / "run_summary.json"

    assert index_html.exists(), f"Master report missing at {index_html}"
    assert run_summary_json.exists(), f"Run summary missing at {run_summary_json}"

    content = index_html.read_text(encoding="utf-8")
    section_count = content.count("<section")
    assert section_count == 8, f"Expected exactly 8 <section> blocks in index.html, found {section_count}"

    for i in range(1, 9):
        assert f'id="stage{i}"' in content, f"Section for stage{i} missing from index.html"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
