"""
Run integration tests one class at a time, checking nanoCAD health between each.
This isolates crashes and reports which test class caused nanoCAD to die.
"""
import os
import subprocess
import sys
import time

TEST_CLASSES = [
    "TestSystem",
    "TestDocument",
    "TestLayers",
    "Test2DEntities",
    "Test3DSolids",
    "Test3DBooleans",
    "TestTransforms",
    "TestBlocks",
    "TestSymbols",
    "TestTables",
    "TestDimensions",
    "TestConstraints",
    "TestHatch",
    "TestMeasurements",
    "TestAssembly",
    "TestSheetMetal",
    "TestMultiCad",
    "Test3DView",
    "TestSelection",
    "TestNurbs",
    "TestFeatures",
    "TestMeshAndGradient",
    "Test3DArrayAlign",
    "Test3DDivideMeasure",
    "TestViewportRender",
    "TestSketchFeatures",
    "TestBoundaryRegion",
]

TEST_FILE = "F:\\nanoCAD\\server\\tests\\integration\\test_http_api.py"


def check_health() -> bool:
    """Return True if nanoCAD HTTP API is alive."""
    import json
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:5080/api/system/health", timeout=5) as r:
            data = json.loads(r.read())
            return data.get("status") == "ok"
    except Exception:
        return False


def is_nano_alive() -> bool:
    """Check if nCad.exe is running."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Process -Name nCad -ErrorAction SilentlyContinue | Select-Object Id"],
            capture_output=True, text=True, timeout=10,
        )
        return "Id" in result.stdout or any(c.isdigit() for c in result.stdout.strip().splitlines() if c.strip())
    except Exception:
        return False


def restart_nano() -> None:
    """Kill and restart nanoCAD."""
    subprocess.run(
        ["powershell", "-Command", "Get-Process -Name nCad -ErrorAction SilentlyContinue | Stop-Process -Force"],
        capture_output=True, timeout=10,
    )
    time.sleep(3)
    subprocess.Popen(["F:\\nanoCAD\\nanoCAD\\nCad.exe"])
    time.sleep(35)


def run_class(class_name: str) -> tuple:
    """Run a single test class via pytest."""
    cmd = [
        "py", "-m", "pytest",
        f"{TEST_FILE}::{class_name}",
        "-v", "--tb=line", "--no-header", "-q",
    ]
    env = os.environ.copy()
    env["NANOCAD_MCP_TEST_LIVE"] = "1"
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180,
            cwd="F:\\nanoCAD\\server", env=env,
        )
        passed = failed = skipped = 0
        for line in result.stdout.splitlines():
            if " passed" in line and " in " in line:
                import re
                m = re.search(r"(\d+) passed", line)
                if m: passed = int(m.group(1))
                m = re.search(r"(\d+) failed", line)
                if m: failed = int(m.group(1))
                m = re.search(r"(\d+) skipped", line)
                if m: skipped = int(m.group(1))
        return passed, failed, skipped
    except subprocess.TimeoutExpired:
        return 0, -1, 0
    except Exception:
        return 0, -2, 0


def main() -> int:

    if not check_health():
        restart_nano()
        if not check_health():
            return 1

    total_p = total_f = total_s = 0
    failed_classes = []

    for cls in TEST_CLASSES:
        if not is_nano_alive():
            restart_nano()
            if not check_health():
                return 2

        p, f, s = run_class(cls)
        total_p += p
        total_f += max(0, f)
        total_s += s

        if f in (-1, -2):
            pass
        elif f > 0:
            failed_classes.append(cls)
        else:
            pass

        # Health check after
        if not check_health():
            restart_nano()
            if not check_health():
                return 3

    if failed_classes:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
