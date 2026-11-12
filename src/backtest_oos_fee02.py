import os
import sys
import glob
import subprocess
import shutil
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDICATOR_DIR = os.path.join(BASE, "data", "indicators")
TEMP_DIR = os.path.join(BASE, "data", "oos_temp")
OUTPUT_DIR = os.path.join(BASE, "data", "oos_results_fee02")

CUT_DATE = pd.Timestamp("2025-12-15 01:35:59.999999", tz="UTC")
FEE_RATE = 0.002

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

original_dir = os.path.join(BASE, "data", "indicators_original")
os.makedirs(original_dir, exist_ok=True)

# Simpan salinan asli agar tidak kehilangan data.
files = sorted(glob.glob(os.path.join(INDICATOR_DIR, "*_indicators.csv")))

if not files:
    raise FileNotFoundError("File indikator tidak ditemukan.")

for file in files:
    name = os.path.basename(file)
    backup = os.path.join(original_dir, name)

    if not os.path.exists(backup):
        pd.read_csv(file).to_csv(backup, index=False)

# Jalankan dua periode secara terpisah.
periods = {
    "train": ("train", lambda t: t <= CUT_DATE),
    "test": ("test", lambda t: t > CUT_DATE),
}

summary = []

for period, (_, condition) in periods.items():
    period_dir = os.path.join(TEMP_DIR, period)
    os.makedirs(period_dir, exist_ok=True)

    for file in files:
        df = pd.read_csv(file)

        df["Time"] = pd.to_datetime(
            df["Time"], unit="s", utc=True
        )

        df = df.loc[condition(df["Time"])].copy()

        if df.empty:
            continue

        df["Time"] = df["Time"].apply(
            lambda x: int(x.timestamp())
        )

        df.to_csv(
            os.path.join(period_dir, os.path.basename(file)),
            index=False
        )

    # Jalankan backtest dengan data periode yang dipilih.
    env = os.environ.copy()
    env["OOS_INDICATOR_DIR"] = period_dir

    script = os.path.join(BASE, "src", "backtest_multi.py")

    # Gunakan salinan skrip sementara.
    with open(script, "r", encoding="utf-8") as f:
        code = f.read()

    code = code.replace(
        'INDICATOR_FOLDER = "data/indicators"',
        f'INDICATOR_FOLDER = r"{period_dir}"'
    )

    code = code.replace(
        "FEE_RATE = 0.003",
        f"FEE_RATE = {FEE_RATE}"
    )

    temp_script = os.path.join(
        BASE, "src", f"_oos_{period}.py"
    )

    with open(temp_script, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        subprocess.run(
            [sys.executable, temp_script],
            cwd=BASE,
            check=True
        )

        # Simpan hasil setiap periode ke folder masing-masing.
        period_output_dir = os.path.join(OUTPUT_DIR, period)
        os.makedirs(period_output_dir, exist_ok=True)

        for filename in [
            "trades_multi.csv",
            "equity_multi.csv",
            "metrics_multi.csv"
        ]:
            source = os.path.join(
                BASE, "data", "backtest", filename
            )

            destination = os.path.join(
                period_output_dir, filename
            )

            shutil.copy2(source, destination)

        # Baca metrik periode yang baru selesai.
        metrics_file = os.path.join(
            BASE, "data", "backtest", "metrics_multi.csv"
        )

        metrics = pd.read_csv(metrics_file)
        metrics = dict(zip(metrics["Metric"], metrics["Value"]))

        summary.append({
            "Period": period,
            "Fee_Per_Side": FEE_RATE,
            "Initial_Capital": metrics["Initial_Capital"],
            "Final_Equity": metrics["Final_Equity"],
            "Return_Percent": metrics["Total_Return_Percent"],
            "Max_Drawdown_Percent": metrics["Max_Drawdown_Percent"],
            "Trades": metrics["Completed_Trades"],
            "Profit_Factor": metrics["Profit_Factor"]
        })

    finally:
        if os.path.exists(temp_script):
            os.remove(temp_script)

result = pd.DataFrame(summary)

result.to_csv(
    os.path.join(OUTPUT_DIR, "oos_summary.csv"),
    index=False
)

print("\n========== HASIL TRAIN VS TEST ==========")
print(result.to_string(index=False))
print("\nHasil tersimpan di:", OUTPUT_DIR)
print("=========================================")
