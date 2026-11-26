from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command, *, cwd: Path, env=None) -> str:
    result = subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed: {}\n{}\n{}".format(
                " ".join(str(item) for item in command),
                result.stdout,
                result.stderr,
            )
        )
    return result.stdout


def main() -> int:
    wheels = sorted((ROOT / "dist").glob("cashbook-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("Expected exactly one cashbook wheel in dist/, found {}".format(len(wheels)))
    wheel = wheels[0].resolve()

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        if not {"cashbook/cli.py", "cjktable/core.py"}.issubset(names):
            raise RuntimeError("Wheel is missing cashbook or vendored cjktable")
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")
        requirements = [line for line in metadata.splitlines() if line.startswith("Requires-Dist:")]
        if requirements:
            raise RuntimeError("Wheel must not declare runtime dependencies: {}".format(requirements))

    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        work = base / "work"
        work.mkdir()
        venv = base / "venv"
        scripts = venv / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        executable = scripts / ("cashbook.exe" if os.name == "nt" else "cashbook")

        run([sys.executable, "-m", "venv", str(venv)], cwd=work)
        run([python, "-m", "pip", "install", "--no-index", "--no-deps", wheel], cwd=work)

        module_info = run(
            [python, "-c", "import cashbook, cjktable; print(cashbook.__file__); print(cjktable.__file__); print(cashbook.__version__)"],
            cwd=work,
        ).splitlines()
        if len(module_info) != 3 or any("site-packages" not in line for line in module_info[:2]):
            raise RuntimeError("Installed modules did not resolve from the clean virtual environment")
        installed_version = module_info[2].strip()

        version = run([executable, "--version"], cwd=work).strip()
        if version != "cashbook {}".format(installed_version):
            raise RuntimeError("Console script version mismatch: {}".format(version))
        help_text = run([executable, "--help"], cwd=work)
        if "add" not in help_text or "summary" not in help_text:
            raise RuntimeError("Console script help output is incomplete")

        ledger = work / "ledger.json"
        command = [executable, "--file", str(ledger)]
        run(command + ["add", "25.5", "餐饮", "午饭"], cwd=work)
        run(command + ["add", "3000", "工资", "--in"], cwd=work)
        run(command + ["budget", "set", "餐饮", "20"], cwd=work)

        listing = json.loads(run(command + ["list", "--json"], cwd=work))
        if listing["count"] != 2:
            raise RuntimeError("Installed CLI did not persist both records")
        report = json.loads(run(command + ["summary", "--json"], cwd=work))
        if report["record_count"] != 2 or report["income"] != "3000.00" or report["expense"] != "25.50":
            raise RuntimeError("Installed CLI produced an incorrect summary")
        if not report["budget"]:
            raise RuntimeError("Installed CLI lost the configured budget")

        csv_path = work / "export.csv"
        exported = json.loads(run(command + ["export", str(csv_path), "--json"], cwd=work))
        if exported["count"] != 2 or not csv_path.exists():
            raise RuntimeError("Installed CLI failed to export records")
        if "餐饮" not in csv_path.read_text(encoding="utf-8-sig"):
            raise RuntimeError("Exported CSV lost Chinese text")

        removed = json.loads(run(command + ["rm", "1", "--json"], cwd=work))
        if removed["removed"] != [1]:
            raise RuntimeError("Installed CLI failed to remove a record")
        if json.loads(run(command + ["list", "--json"], cwd=work))["count"] != 1:
            raise RuntimeError("Installed CLI state changed unexpectedly after removal")

    print("Installed wheel smoke test: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
