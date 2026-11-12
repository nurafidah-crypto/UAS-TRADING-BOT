
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

SCRIPTS = [
    "update_forward_data.py",
    "update_forward_indicators.py",
]

def run_script(command, name):
    print(f"\n{'=' * 60}")
    print(f"Menjalankan: {name}")
    print("=" * 60, flush=True)

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True
    )

def main():
    for script in SCRIPTS:
        script_path = PROJECT_ROOT / "src" / script
        run_script(
            [str(PYTHON), str(script_path)],
            script
        )

    # Jalankan engine sebagai modul dari folder project
    run_script(
        [str(PYTHON), "-m", "src.forward_engine"],
        "forward_engine.py"
    )

    print("\nSatu siklus forward test selesai.", flush=True)

if __name__ == "__main__":
    main()
