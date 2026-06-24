from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_PROJECT = REPO_ROOT / "python"
OUTPUT_DIR = REPO_ROOT / "releases" / "python"


def main() -> int:
    if shutil.which(sys.executable) is None:
        print("Python executable could not be resolved for release packaging.", file=sys.stderr)
        return 1

    try:
        import build  # noqa: F401
    except Exception:
        print(
            "Python release tooling is missing. Install it with `python -m pip install build` "
            "and run `npm run release:python` again.",
            file=sys.stderr,
        )
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "build",
        str(PYTHON_PROJECT),
        "--outdir",
        str(OUTPUT_DIR),
    ]

    print(f"Building Python artifacts into {OUTPUT_DIR}")
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
